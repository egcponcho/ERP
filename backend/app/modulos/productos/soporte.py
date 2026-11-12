"""Piezas que comparten los servicios de productos: buscar el producto, revisar
la versión, validar el tipo y escribir los valores de atributos de un nivel.

No depende de ningún otro archivo de servicio del módulo, así que cualquiera
(productos, variantes, complementos, asistente) lo puede usar sin ciclos.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errores import conflicto, invalido, no_existe
from app.modulos.productos import esquema as esq
from app.modulos.productos import valores as val
from app.modulos.productos.modelos import Categoria, Producto, TipoProducto, ValorAtributo


def obtener(db: Session, producto_id: int) -> Producto:
    p = db.get(Producto, producto_id)
    if p is None:
        raise no_existe("El producto")
    return p


def verificar_version(obj, version: int | None) -> None:
    """Bloqueo optimista explícito: la pantalla manda la versión que leyó."""
    if version is not None and version != obj.version:
        raise conflicto("Otra persona modificó el registro mientras tanto: vuelva a cargarlo.",
                        {"version_actual": obj.version})


def tipo_activo(db: Session, tipo_id: int) -> TipoProducto:
    t = db.get(TipoProducto, tipo_id)
    if t is None:
        raise no_existe("El tipo de producto")
    if not t.activo:
        raise invalido("El tipo de producto está inactivo.")
    return t


# ---- Valores de atributos -----------------------------------------------------------------
def fijar_valores(db: Session, filas: list[ValorAtributo], campos: list[esq.Campo], entrada: dict,
                   nuevo: bool, crear) -> dict:
    """Escribe en `filas` los valores de `entrada` para los `campos` del nivel.
    En un alta se ponen los valores por defecto que no lleguen. Devuelve
    {código: Normalizado} de lo escrito. `crear()` hace una fila nueva del dueño."""
    por_codigo = {c.codigo: c for c in campos}
    errores = [{"campo": f"atributos.{k}", "mensaje": "No es un atributo de este nivel del tipo."}
               for k in entrada if k not in por_codigo]
    actuales = {f.atributo.id: f for f in filas}
    escritos = {}
    pendientes = dict(entrada)
    if nuevo:
        for c in campos:
            if c.codigo not in pendientes and c.valor_defecto is not None:
                pendientes[c.codigo] = c.valor_defecto
    for codigo, crudo in pendientes.items():
        c = por_codigo.get(codigo)
        if c is None:
            continue
        fila = actuales.get(c.atributo.id)
        if val.vacio(crudo):
            if fila is not None:
                filas.remove(fila)
            continue
        try:
            n = val.convertir(db, c.atributo, crudo)
        except ValueError as ex:
            errores.append({"campo": f"atributos.{codigo}", "mensaje": f"{c.atributo.nombre}: {ex}."})
            continue
        if fila is None:
            fila = crear(c.atributo)
            filas.append(fila)
        val.aplicar(fila, n)
        escritos[codigo] = n
    if errores:
        raise invalido("Revise los atributos.", errores)
    return escritos


def valores_dict(filas: list[ValorAtributo]) -> dict:
    """{código del atributo: valor legible} de un producto o variante."""
    return {f.atributo.codigo: val.leer(f) for f in filas}


def subcategorias(db: Session, categoria_id: int) -> set[int]:
    """La categoría y todas las que cuelgan de ella (para filtrar «incluye subcategorías»)."""
    hijos: dict[int | None, list[int]] = {}
    for i, padre in db.execute(select(Categoria.id, Categoria.padre_id)):
        hijos.setdefault(padre, []).append(i)
    res, pendientes = set(), [categoria_id]
    while pendientes:
        i = pendientes.pop()
        if i not in res:
            res.add(i)
            pendientes.extend(hijos.get(i, []))
    return res


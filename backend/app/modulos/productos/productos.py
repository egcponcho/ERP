"""Productos: alta, edición, categorías, cambio de tipo, estado y baja.

Todo lo que depende del rubro sale del esquema del tipo (esquema.py): qué
atributos se capturan, en qué nivel, cuáles son obligatorios y cuáles
distinguen variantes. Este servicio no conoce ningún rubro.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import integridad, referencias
from app.core.errores import conflicto, invalido, no_existe
from app.core.modelo import ahora
from app.modulos.productos import configuracion as conf
from app.modulos.productos import esquema as esq
from app.modulos.productos import esquemas as e
from app.modulos.productos.lectura import detalle, faltantes
from app.modulos.productos.modelos import (
    Categoria,
    EstadoProducto,
    EstadoTransicion,
    Producto,
    ProductoCategoria,
    TipoProducto,
    ValorAtributo,
)
from app.modulos.productos.soporte import fijar_valores, obtener, tipo_activo, verificar_version


# ---- Categorías ---------------------------------------------------------------------------
def _fijar_categorias(db: Session, p: Producto, ids: list[int]) -> None:
    cats = []
    for i in dict.fromkeys(ids):
        c = db.get(Categoria, i)
        if c is None:
            raise invalido("Revise las categorías.", [{"campo": "categorias", "mensaje": f"La categoría {i} no existe."}])
        if not c.activa:
            raise invalido(f"La categoría {c.nombre} está inactiva.")
        cats.append(c)
    por_tax: dict[int, list[Categoria]] = {}
    for c in cats:
        por_tax.setdefault(c.taxonomia_id, []).append(c)
    for lista in por_tax.values():
        if len(lista) > 1 and not lista[0].taxonomia.multiple:
            raise invalido(f"En {lista[0].taxonomia.nombre} el producto va en una sola categoría.")
    actuales = {pc.categoria_id: pc for pc in p.categorias}
    p.categorias = [actuales.get(c.id) or ProductoCategoria(categoria=c) for c in cats]


# ---- Estado -------------------------------------------------------------------------------
def _exigir_completo(db: Session, p: Producto, estado: EstadoProducto) -> None:
    if estado.exige_completo:
        falta = faltantes(db, p)
        if falta:
            raise invalido(f"Para pasar a {estado.nombre} el producto debe estar completo.", {"faltantes": falta})


def cambiar_estado(db: Session, producto_id: int, datos: e.CambioEstado) -> dict:
    p = obtener(db, producto_id)
    verificar_version(p, datos.version)
    destino = db.get(EstadoProducto, datos.estado_id)
    if destino is None or not destino.activo:
        raise no_existe("El estado")
    if destino.id == p.estado_id:
        return detalle(db, p)
    permitidos = set(db.scalars(select(EstadoTransicion.destino_id).where(EstadoTransicion.origen_id == p.estado_id)))
    if permitidos and destino.id not in permitidos:
        raise conflicto(f"No se puede pasar de {p.estado.nombre} a {destino.nombre}.")
    _exigir_completo(db, p, destino)
    p.estado = destino
    integridad.guardar(db)
    return detalle(db, p)


# ---- Alta y edición -----------------------------------------------------------------------
def crear(db: Session, datos: e.ProductoAlta) -> dict:
    tipo = tipo_activo(db, datos.tipo_id)
    e_ = esq.resolver(tipo)
    unidad_id = datos.unidad_id or e_.unidad_defecto_id
    if unidad_id is None:
        raise invalido("Indique la unidad base (el tipo no tiene una por defecto).")
    if datos.estado_id:
        estado = db.get(EstadoProducto, datos.estado_id)
        if estado is None or not estado.activo:
            raise no_existe("El estado")
    else:
        estado = db.scalar(select(EstadoProducto).where(EstadoProducto.inicial.is_(True), EstadoProducto.activo.is_(True)))
        if estado is None:
            raise invalido("Configure un estado inicial o indique el estado.")
    codigo = datos.codigo.strip() if datos.codigo else conf.siguiente_codigo(db, tipo)
    if not codigo:
        raise invalido("Indique el código (el tipo no tiene plantilla de código).")
    p = Producto(codigo=codigo, nombre=datos.nombre.strip(), descripcion=datos.descripcion, tipo=tipo,
                 unidad_id=unidad_id, estado_id=estado.id)
    integridad.verificar_referencias(db, p)
    p.estado = estado
    fijar_valores(db, p.valores, e_.de_nivel("producto"), datos.atributos, True,
                   lambda a: ValorAtributo(atributo=a))
    _fijar_categorias(db, p, datos.categorias)
    _exigir_completo(db, p, estado)
    integridad.guardar(db, p, "Ya existe un producto con ese código.")
    return detalle(db, p)


def editar(db: Session, producto_id: int, datos: e.ProductoEdicion) -> dict:
    p = obtener(db, producto_id)
    verificar_version(p, datos.version)
    cambios = datos.model_dump(exclude_unset=True, exclude={"version", "atributos", "categorias", "descartar_atributos"})
    if "tipo_id" in cambios and cambios["tipo_id"] != p.tipo_id:
        _cambiar_tipo(db, p, tipo_activo(db, cambios.pop("tipo_id")), datos.descartar_atributos)
    cambios.pop("tipo_id", None)
    for k, v in cambios.items():
        if v is None and k in ("codigo", "nombre", "unidad_id"):
            raise invalido(f"El campo {k} no puede quedar vacío.")
        setattr(p, k, v.strip() if isinstance(v, str) and k != "descripcion" else v)
    integridad.verificar_referencias(db, p)
    e_ = esq.resolver(p.tipo)
    if datos.atributos is not None:
        fijar_valores(db, p.valores, e_.de_nivel("producto"), datos.atributos, False,
                       lambda a: ValorAtributo(atributo=a))
    if datos.categorias is not None:
        _fijar_categorias(db, p, datos.categorias)
    _exigir_completo(db, p, p.estado)
    p.actualizado_en = ahora()  # nueva versión del producto aunque solo cambien filas hijas
    db.add(p)
    integridad.guardar(db, None, "Ya existe un producto con ese código.")
    return detalle(db, p)


def _cambiar_tipo(db: Session, p: Producto, nuevo: TipoProducto, descartar: bool) -> None:
    antes, despues = esq.resolver(p.tipo), esq.resolver(nuevo)
    if p.variantes and {c.atributo.id for c in antes.ejes} != {c.atributo.id for c in despues.ejes}:
        raise conflicto("El producto tiene variantes y el nuevo tipo las distingue con otros ejes.")
    nivel_p = {c.atributo.id for c in despues.de_nivel("producto")}
    nivel_v = {c.atributo.id for c in despues.de_nivel("variante")}
    sobran = [f for f in p.valores if f.atributo.id not in nivel_p]
    sobran_v = [(v, f) for v in p.variantes for f in v.valores if f.atributo.id not in nivel_v]
    if (sobran or sobran_v) and not descartar:
        raise conflicto("El nuevo tipo no tiene algunos atributos con valor. Confirme con descartar_atributos.",
                        {"atributos": sorted({f.atributo.codigo for f in sobran} | {f.atributo.codigo for _, f in sobran_v})})
    for f in sobran:
        p.valores.remove(f)
    for v, f in sobran_v:
        v.valores.remove(f)
    p.tipo = nuevo


def eliminar(db: Session, producto_id: int) -> None:
    p = obtener(db, producto_id)
    uso = referencias.en_uso(db, "producto", p.id)
    if uso:
        raise conflicto(f"El producto está en uso ({uso}): cámbielo a un estado inactivo en lugar de borrarlo.")
    integridad.borrar(db, p, "El producto")

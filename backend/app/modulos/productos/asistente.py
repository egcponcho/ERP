"""Asistente de alta: crea el producto con sus variantes, presentaciones,
identificadores y estado final en una sola transacción.

Con `validar` todo se ejecuta igual y después se descarta (la ruta hace
rollback): así la pantalla muestra, antes de guardar, el código y los SKU que
resultarán y cualquier problema, señalado en el paso donde se corrige.

Los errores de cada sección se juntan (no se detiene en el primero) y vienen
en `detalle` como {campo, mensaje} con el camino completo:
producto.nombre, producto.atributos.color, variantes.3, presentaciones.0.codigo,
identificadores.1, estado.
"""
from sqlalchemy.orm import Session

from app.core import integridad
from app.core.errores import ErrorNegocio, invalido
from app.modulos.productos import complementos, productos
from app.modulos.productos import esquema as esq
from app.modulos.productos import esquemas as e
from app.modulos.productos.modelos import Presentacion


def _con_prefijo(ex: ErrorNegocio, prefijo: str) -> list[dict]:
    """Los problemas de un error con el camino de su sección delante."""
    detalle = ex.detalle if isinstance(ex.detalle, list) else None
    if detalle and all(isinstance(d, dict) and "campo" in d for d in detalle):
        return [{**d, "campo": f"{prefijo}.{d['campo']}"} for d in detalle]
    extra = {"faltantes": ex.detalle["faltantes"]} if isinstance(ex.detalle, dict) and "faltantes" in ex.detalle else {}
    return [{"campo": prefijo, "mensaje": ex.mensaje, **extra}]


def ejecutar(db: Session, datos: e.AsistenteEntrada) -> dict:
    try:
        creado = productos.crear(db, datos.producto.model_copy(update={"estado_id": None}))
    except ErrorNegocio as ex:
        if ex.status not in (404, 409, 422):
            raise
        raise invalido("Revise los datos del producto.", _con_prefijo(ex, "producto")) from ex
    p = productos.obtener(db, creado["id"])
    errores: list[dict] = []

    if datos.variantes:
        e_ = esq.resolver(p.tipo)
        for i, v in enumerate(datos.variantes):
            try:
                with db.begin_nested():
                    nueva = productos._nueva_variante(db, p, e_, v)
                    db.add(nueva)
                    db.flush()
            except ErrorNegocio as ex:
                errores += _con_prefijo(ex, f"variantes.{i}")

    por_codigo: dict[str, Presentacion] = {}
    for i, x in enumerate(datos.presentaciones):
        if x.variante_id is not None:
            errores.append({"campo": f"presentaciones.{i}", "mensaje": "En el alta, las presentaciones son del producto."})
            continue
        try:
            with db.begin_nested():
                complementos.crear_presentacion(db, p.id, x)
            por_codigo[x.codigo.lower()] = next(y for y in p.presentaciones if y.codigo.lower() == x.codigo.lower())
        except ErrorNegocio as ex:
            errores += _con_prefijo(ex, f"presentaciones.{i}")

    for i, x in enumerate(datos.identificadores):
        presentacion = None
        if x.presentacion_codigo:
            presentacion = por_codigo.get(x.presentacion_codigo.lower())
            if presentacion is None:
                errores.append({"campo": f"identificadores.{i}", "mensaje": f"No hay una presentación {x.presentacion_codigo}."})
                continue
        try:
            with db.begin_nested():
                complementos.crear_identificador(db, p.id, e.IdentificadorEntrada(
                    tipo_id=x.tipo_id, valor=x.valor, presentacion_id=presentacion.id if presentacion else None))
        except ErrorNegocio as ex:
            errores += _con_prefijo(ex, f"identificadores.{i}")

    if errores:
        raise invalido("Hay datos por corregir.", errores)

    db.refresh(p)
    if datos.estado_id and datos.estado_id != p.estado_id:
        try:
            productos.cambiar_estado(db, p.id, e.CambioEstado(estado_id=datos.estado_id))
        except ErrorNegocio as ex:
            raise invalido(ex.mensaje, _con_prefijo(ex, "estado")) from ex
    integridad.guardar(db)
    db.refresh(p)
    return productos.detalle(db, p)

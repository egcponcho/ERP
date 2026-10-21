"""Lo que cuelga del producto: presentaciones, identificadores, relaciones con
otros productos y revisiones publicadas."""
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import integridad
from app.core.errores import conflicto, invalido, no_existe
from app.core.modelo import ahora
from app.modulos.productos import esquemas as e
from app.modulos.productos import valores as val
from app.modulos.productos.modelos import (
    Identificador,
    Presentacion,
    Producto,
    RelacionProducto,
    RevisionProducto,
    TipoIdentificador,
    TipoRelacion,
    Variante,
)
from app.modulos.productos.productos import detalle, obtener


def _de_producto(db: Session, modelo, producto_id: int, id_: int, que: str):
    obj = db.get(modelo, id_)
    if obj is None or obj.producto_id != producto_id:
        raise no_existe(que)
    return obj


def _variante_del_producto(db: Session, p: Producto, variante_id: int | None) -> None:
    if variante_id is not None:
        v = db.get(Variante, variante_id)
        if v is None or v.producto_id != p.id:
            raise invalido("La variante no es de este producto.")


def presentacion_dict(x: Presentacion) -> dict:
    return {"id": x.id, "codigo": x.codigo, "nombre": x.nombre, "variante_id": x.variante_id,
            "unidad": x.unidad.codigo, "unidad_id": x.unidad_id, "cantidad": val.numero(x.cantidad), "activa": x.activa}


def identificador_dict(x: Identificador) -> dict:
    return {"id": x.id, "tipo": x.tipo.codigo, "tipo_id": x.tipo_id, "valor": x.valor,
            "variante_id": x.variante_id, "presentacion_id": x.presentacion_id}


def relacion_dict(x: RelacionProducto) -> dict:
    return {"id": x.id, "tipo": x.tipo.codigo, "tipo_id": x.tipo_id, "destino": {
        "id": x.destino.id, "codigo": x.destino.codigo, "nombre": x.destino.nombre},
        "destino_variante_id": x.destino_variante_id, "cantidad": val.numero(x.cantidad),
        "unidad": x.unidad.codigo if x.unidad else None, "orden": x.orden}


def de_producto(p: Producto) -> dict:
    return {
        "presentaciones": [presentacion_dict(x) for x in p.presentaciones],
        "identificadores": [identificador_dict(x) for x in p.identificadores],
        "relaciones": [relacion_dict(x) for x in p.relaciones],
    }


# ---- Presentaciones -----------------------------------------------------------------------
def crear_presentacion(db: Session, producto_id: int, datos: e.PresentacionEntrada) -> dict:
    p = obtener(db, producto_id)
    _variante_del_producto(db, p, datos.variante_id)
    x = Presentacion(producto=p, **datos.model_dump())
    integridad.verificar_referencias(db, x)
    integridad.guardar(db, x, "Ya existe una presentación con ese código en el producto.")
    return presentacion_dict(x)


def editar_presentacion(db: Session, producto_id: int, id_: int, datos) -> dict:
    x = _de_producto(db, Presentacion, producto_id, id_, "La presentación")
    for k, v in datos.model_dump(exclude_unset=True).items():
        if v is None and k in ("codigo", "nombre", "unidad_id", "cantidad", "activa"):
            raise invalido(f"El campo {k} no puede quedar vacío.")
        setattr(x, k, v)
    _variante_del_producto(db, x.producto, x.variante_id)
    integridad.verificar_referencias(db, x)
    integridad.guardar(db, None, "Ya existe una presentación con ese código en el producto.")
    return presentacion_dict(x)


def borrar_presentacion(db: Session, producto_id: int, id_: int) -> None:
    integridad.borrar(db, _de_producto(db, Presentacion, producto_id, id_, "La presentación"), "La presentación")


# ---- Identificadores ----------------------------------------------------------------------
def crear_identificador(db: Session, producto_id: int, datos: e.IdentificadorEntrada) -> dict:
    p = obtener(db, producto_id)
    tipo = db.get(TipoIdentificador, datos.tipo_id)
    if tipo is None or not tipo.activo:
        raise no_existe("El tipo de identificador")
    valor = datos.valor.strip()
    if tipo.patron and not re.fullmatch(tipo.patron, valor):
        raise invalido(f"El valor no tiene el formato de {tipo.nombre}.")
    _variante_del_producto(db, p, datos.variante_id)
    if datos.presentacion_id is not None:
        x = db.get(Presentacion, datos.presentacion_id)
        if x is None or x.producto_id != p.id:
            raise invalido("La presentación no es de este producto.")
    x = Identificador(producto=p, tipo=tipo, valor=valor, variante_id=datos.variante_id,
                      presentacion_id=datos.presentacion_id)
    integridad.guardar(db, x, f"El {tipo.nombre} {valor} ya está asignado.")
    return identificador_dict(x)


def borrar_identificador(db: Session, producto_id: int, id_: int) -> None:
    integridad.borrar(db, _de_producto(db, Identificador, producto_id, id_, "El identificador"), "El identificador")


def buscar_por_identificador(db: Session, valor: str, tipo_id: int | None = None) -> list[dict]:
    q = select(Identificador).where(Identificador.valor == valor.strip())
    if tipo_id:
        q = q.where(Identificador.tipo_id == tipo_id)
    return [{**identificador_dict(x), "producto": {"id": x.producto.id, "codigo": x.producto.codigo,
                                                   "nombre": x.producto.nombre}} for x in db.scalars(q)]


# ---- Relaciones ---------------------------------------------------------------------------
def _alcanza(db: Session, tipo_id: int, desde: int, hasta: int) -> bool:
    """¿Hay un camino desde → hasta por relaciones del mismo tipo? (evita ciclos en listas de materiales)."""
    vistos, pendientes = set(), [desde]
    while pendientes:
        i = pendientes.pop()
        if i == hasta:
            return True
        if i in vistos:
            continue
        vistos.add(i)
        pendientes.extend(db.scalars(select(RelacionProducto.destino_id)
                                     .where(RelacionProducto.tipo_id == tipo_id, RelacionProducto.origen_id == i)))
    return False


def _validar_relacion(db: Session, x: RelacionProducto) -> None:
    tipo = db.get(TipoRelacion, x.tipo_id)
    if tipo is None or not tipo.activo:
        raise no_existe("El tipo de relación")
    if x.destino_id == x.origen_id:
        raise invalido("Un producto no se relaciona consigo mismo.")
    if x.destino_variante_id is not None:
        v = db.get(Variante, x.destino_variante_id)
        if v is None or v.producto_id != x.destino_id:
            raise invalido("La variante no es del producto relacionado.")
    if tipo.con_cantidad and x.cantidad is None:
        raise invalido(f"{tipo.nombre} lleva cantidad.")
    if not tipo.con_cantidad and (x.cantidad is not None or x.unidad_id is not None):
        raise invalido(f"{tipo.nombre} no lleva cantidad ni unidad.")
    # La restricción única de la base no ve repetidos cuando destino_variante_id es NULL
    repetida = select(RelacionProducto.id).where(
        RelacionProducto.tipo_id == x.tipo_id, RelacionProducto.origen_id == x.origen_id,
        RelacionProducto.destino_id == x.destino_id, RelacionProducto.destino_variante_id.is_(x.destino_variante_id)
        if x.destino_variante_id is None else RelacionProducto.destino_variante_id == x.destino_variante_id)
    if x.id is not None:
        repetida = repetida.where(RelacionProducto.id != x.id)
    if db.scalar(repetida.limit(1)):
        raise conflicto("Esa relación ya existe.")
    if _alcanza(db, x.tipo_id, x.destino_id, x.origen_id):
        raise conflicto("La relación formaría un ciclo (el producto relacionado ya contiene a este).")


def crear_relacion(db: Session, producto_id: int, datos: e.RelacionEntrada) -> dict:
    p = obtener(db, producto_id)
    x = RelacionProducto(origen_id=p.id, **datos.model_dump())
    integridad.verificar_referencias(db, x)
    _validar_relacion(db, x)
    x.origen = p
    integridad.guardar(db, x, "Esa relación ya existe.")
    return relacion_dict(x)


def editar_relacion(db: Session, producto_id: int, id_: int, datos) -> dict:
    x = db.get(RelacionProducto, id_)
    if x is None or x.origen_id != producto_id:
        raise no_existe("La relación")
    for k, v in datos.model_dump(exclude_unset=True).items():
        setattr(x, k, v)
    integridad.verificar_referencias(db, x)
    _validar_relacion(db, x)
    integridad.guardar(db, None, "Esa relación ya existe.")
    db.refresh(x)
    return relacion_dict(x)


def borrar_relacion(db: Session, producto_id: int, id_: int) -> None:
    x = db.get(RelacionProducto, id_)
    if x is None or x.origen_id != producto_id:
        raise no_existe("La relación")
    integridad.borrar(db, x, "La relación")


def usado_en(db: Session, producto_id: int) -> list[dict]:
    """Las relaciones en que el producto es el destino (dónde se usa como componente, sustituto…)."""
    obtener(db, producto_id)
    filas = db.scalars(select(RelacionProducto).where(RelacionProducto.destino_id == producto_id))
    return [{"id": x.id, "tipo": x.tipo.codigo, "nombre": x.tipo.nombre_inverso or x.tipo.nombre,
             "origen": {"id": x.origen.id, "codigo": x.origen.codigo, "nombre": x.origen.nombre},
             "cantidad": val.numero(x.cantidad)} for x in filas]


# ---- Revisiones ---------------------------------------------------------------------------
def publicar_revision(db: Session, producto_id: int, datos: e.RevisionAlta) -> dict:
    """Congela la ficha actual como una revisión nueva y cierra la vigencia de la anterior."""
    p = obtener(db, producto_id)
    momento = ahora()
    anterior = next((r for r in reversed(p.revisiones) if r.vigente_hasta is None), None)
    if anterior is not None:
        anterior.vigente_hasta = momento
    copia = detalle(db, p)
    for k in ("revision", "version", "faltantes"):
        copia.pop(k, None)
    r = RevisionProducto(numero=p.revision + 1, motivo=datos.motivo, vigente_desde=momento, datos=copia)
    p.revisiones.append(r)
    p.revision = r.numero
    integridad.guardar(db)
    return revision_dict(r, con_datos=True)


def revision_dict(r: RevisionProducto, con_datos: bool = False) -> dict:
    return {"numero": r.numero, "motivo": r.motivo, "vigente_desde": r.vigente_desde.isoformat(),
            "vigente_hasta": r.vigente_hasta.isoformat() if r.vigente_hasta else None,
            **({"datos": r.datos} if con_datos else {})}


def revisiones(db: Session, producto_id: int) -> list[dict]:
    return [revision_dict(r) for r in obtener(db, producto_id).revisiones]


def revision(db: Session, producto_id: int, numero: int) -> dict:
    r = next((r for r in obtener(db, producto_id).revisiones if r.numero == numero), None)
    if r is None:
        raise no_existe("La revisión")
    return revision_dict(r, con_datos=True)

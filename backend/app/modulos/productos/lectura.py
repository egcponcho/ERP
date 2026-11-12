"""Cómo se presenta un producto hacia afuera (la ficha que devuelve la API) y
qué le falta para estar completo.

Solo lee: no escribe ni valida entradas. Los demás servicios lo usan para
responder, así que no importa a ninguno de ellos.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modulos.productos import esquema as esq
from app.modulos.productos import valores as val
from app.modulos.productos.modelos import (
    Identificador,
    Presentacion,
    Producto,
    RelacionProducto,
    Taxonomia,
    Variante,
)
from app.modulos.productos.soporte import obtener, valores_dict


# ---- Completitud --------------------------------------------------------------------------
def faltantes(db: Session, p: Producto, e_: esq.Esquema | None = None) -> list[dict]:
    """Lo obligatorio que falta: atributos del producto, de cada variante y taxonomías."""
    e_ = e_ or esq.resolver(p.tipo)
    res = []
    tiene = {f.atributo.id for f in p.valores}
    res += [{"nivel": "producto", "atributo": c.codigo, "nombre": c.atributo.nombre}
            for c in e_.de_nivel("producto") if c.obligatorio and c.atributo.id not in tiene]
    obligatorios_var = [c for c in e_.de_nivel("variante") if c.obligatorio or c.es_eje]
    for v in p.variantes:
        tiene_v = {f.atributo.id for f in v.valores}
        res += [{"nivel": "variante", "variante": v.codigo, "atributo": c.codigo, "nombre": c.atributo.nombre}
                for c in obligatorios_var if c.atributo.id not in tiene_v]
    con_categoria = {pc.categoria.taxonomia_id for pc in p.categorias}
    for t in db.scalars(select(Taxonomia).where(Taxonomia.obligatoria.is_(True), Taxonomia.activa.is_(True))):
        if t.id not in con_categoria:
            res.append({"nivel": "categoria", "taxonomia": t.codigo, "nombre": t.nombre})
    return res


# ---- Piezas de la ficha -------------------------------------------------------------------
def variante_dict(v: Variante) -> dict:
    return {"id": v.id, "codigo": v.codigo, "nombre": v.nombre, "activa": v.activa, "version": v.version,
            "atributos": valores_dict(v.valores)}


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


def complementos(p: Producto) -> dict:
    return {
        "presentaciones": [presentacion_dict(x) for x in p.presentaciones],
        "identificadores": [identificador_dict(x) for x in p.identificadores],
        "relaciones": [relacion_dict(x) for x in p.relaciones],
    }


# ---- La ficha completa --------------------------------------------------------------------
def detalle(db: Session, p: Producto) -> dict:
    """La ficha que devuelven todas las rutas que leen o escriben un producto."""
    e_ = esq.resolver(p.tipo)
    en_esquema = {c.atributo.id for c in e_.de_nivel("producto")}
    return {
        "id": p.id, "codigo": p.codigo, "nombre": p.nombre, "descripcion": p.descripcion,
        "tipo": {"id": p.tipo.id, "codigo": p.tipo.codigo, "nombre": p.tipo.nombre},
        "unidad": {"id": p.unidad.id, "codigo": p.unidad.codigo, "nombre": p.unidad.nombre},
        "estado": {"id": p.estado.id, "codigo": p.estado.codigo, "nombre": p.estado.nombre, "operable": p.estado.operable},
        "atributos": valores_dict([f for f in p.valores if f.atributo.id in en_esquema]),
        # Valores de atributos que el tipo ya no tiene (se ocultaron o se quitaron): se conservan, no se pierden
        "atributos_fuera_de_esquema": valores_dict([f for f in p.valores if f.atributo.id not in en_esquema]),
        "categorias": [{"id": pc.categoria.id, "codigo": pc.categoria.codigo, "nombre": pc.categoria.nombre,
                        "taxonomia": pc.categoria.taxonomia.codigo} for pc in p.categorias],
        "variantes": [variante_dict(v) for v in p.variantes],
        **complementos(p),
        "faltantes": faltantes(db, p, e_),
        "revision": p.revision,
        "version": p.version,
        "creado_en": p.creado_en.isoformat() if p.creado_en else None,
        "actualizado_en": p.actualizado_en.isoformat() if p.actualizado_en else None,
    }


def ver(db: Session, producto_id: int) -> dict:
    return detalle(db, obtener(db, producto_id))

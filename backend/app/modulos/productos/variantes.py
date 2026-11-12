"""Variantes (SKU): el producto con un valor para cada atributo eje.

La combinación de ejes se resume en una `firma` (sha256 de los valores
normalizados), única por producto: 5 kg y 5000 g cuentan como la misma.
El código sale de la plantilla de SKU del tipo o, sin plantilla, del código
del producto más los valores de los ejes.
"""
import hashlib
import itertools
import re

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.core import integridad
from app.core.errores import ErrorNegocio, conflicto, invalido, no_existe
from app.core.modelo import ahora
from app.modulos.productos import esquema as esq
from app.modulos.productos import esquemas as e
from app.modulos.productos import valores as val
from app.modulos.productos.lectura import variante_dict
from app.modulos.productos.modelos import Atributo, Producto, ValorAtributo, Variante
from app.modulos.productos.soporte import fijar_valores, obtener, verificar_version


def _ficha(n: val.Normalizado, a: Atributo) -> str:
    """El valor de un eje como parte de un código (opción → su código)."""
    if n.opcion is not None:
        return n.opcion.codigo
    if n.numero is not None:
        return str(val.numero(n.numero)) + (n.unidad.codigo if n.unidad else "")
    if n.booleano is not None:
        return "S" if n.booleano else "N"
    if n.fecha is not None:
        return n.fecha.strftime("%Y%m%d")
    if n.referencia_id is not None:
        return str(n.referencia_id)
    return re.sub(r"[^A-Za-z0-9]+", "", (n.texto or "").upper())


def _firma(ejes: list[esq.Campo], escritos: dict[str, val.Normalizado]) -> str:
    base = "|".join(f"{c.atributo.id}={escritos[c.codigo].clave()}" for c in sorted(ejes, key=lambda c: c.atributo.id))
    return hashlib.sha256(base.encode()).hexdigest()


def _codigo_variante(p: Producto, e_: esq.Esquema, escritos: dict) -> str:
    fichas = {c.codigo: _ficha(escritos[c.codigo], c.atributo) for c in e_.ejes}
    plantilla = e_.plantilla_sku
    if not plantilla:
        return "-".join([p.codigo, *fichas.values()])
    try:
        return plantilla.format(producto=p.codigo, **fichas)
    except KeyError as ex:
        raise invalido(f"La plantilla de SKU del tipo usa {ex}, que no es un eje del tipo.") from ex


def _nombre_variante(p: Producto, e_: esq.Esquema, v: Variante) -> str:
    por_id = {f.atributo.id: f for f in v.valores}
    partes = [val.texto(por_id[c.atributo.id]) for c in e_.ejes if c.atributo.id in por_id]
    return f"{p.nombre} {' / '.join(partes)}".strip()[:250]


def _valores_de_variante(v: Variante) -> dict[str, val.Normalizado]:
    return {f.atributo.codigo: val.normalizado_de(f) for f in v.valores}


def nueva_variante(db: Session, p: Producto, e_: esq.Esquema, datos: e.VarianteAlta) -> Variante:
    ejes = e_.ejes
    if not ejes:
        raise conflicto("El tipo de este producto no tiene atributos eje: no maneja variantes.")
    faltan = [c.codigo for c in ejes if val.vacio(datos.atributos.get(c.codigo))]
    if faltan:
        raise invalido("Indique los valores de todos los ejes.", {"faltan": faltan})
    v = Variante(activa=datos.activa, firma="")  # se une al producto solo si es válida
    escritos = fijar_valores(db, v.valores, e_.de_nivel("variante"), datos.atributos, True,
                              lambda a: ValorAtributo(atributo=a))
    v.firma = _firma(ejes, escritos)
    if any(x.firma == v.firma for x in p.variantes if x is not v):
        raise conflicto("Ya existe una variante con esos valores.",
                        {"valores": {c.codigo: datos.atributos[c.codigo] for c in ejes}})
    v.codigo = datos.codigo.strip() if datos.codigo else _codigo_variante(p, e_, escritos)
    if db.scalar(select(exists().where(func.lower(Variante.codigo) == v.codigo.lower()))):
        raise conflicto(f"El código {v.codigo} ya es de otra variante.")
    v.nombre = datos.nombre or _nombre_variante(p, e_, v)
    v.producto = p
    return v


def crear_variante(db: Session, producto_id: int, datos: e.VarianteAlta) -> dict:
    p = obtener(db, producto_id)
    v = nueva_variante(db, p, esq.resolver(p.tipo), datos)
    integridad.guardar(db, v, "Ya existe una variante con ese código o con esos valores.")
    return variante_dict(v)


def generar_variantes(db: Session, producto_id: int, datos: e.GenerarVariantes) -> dict:
    """Crea todas las combinaciones de los valores de los ejes; omite las que ya existen."""
    p = obtener(db, producto_id)
    e_ = esq.resolver(p.tipo)
    ejes = [c.codigo for c in e_.ejes]
    if set(datos.ejes) != set(ejes):
        raise invalido("Indique los valores de cada eje del tipo.", {"ejes": ejes})
    creadas, omitidas = [], []
    for combinacion in itertools.product(*(datos.ejes[c] for c in ejes)):
        valores_eje = dict(zip(ejes, combinacion, strict=True))
        try:
            with db.begin_nested():
                v = nueva_variante(db, p, e_, e.VarianteAlta(atributos={**datos.atributos, **valores_eje}))
                db.add(v)
                db.flush()
            creadas.append(v)
        except ErrorNegocio as ex:  # combinación repetida o código ocupado: se informa y se sigue
            if ex.status != 409:
                raise
            omitidas.append({"valores": valores_eje, "motivo": ex.mensaje})
    return {"creadas": [variante_dict(v) for v in creadas], "omitidas": omitidas}


def _variante(db: Session, producto_id: int, variante_id: int) -> Variante:
    v = db.get(Variante, variante_id)
    if v is None or v.producto_id != producto_id:
        raise no_existe("La variante")
    return v


def editar_variante(db: Session, producto_id: int, variante_id: int, datos: e.VarianteEdicion) -> dict:
    v = _variante(db, producto_id, variante_id)
    verificar_version(v, datos.version)
    e_ = esq.resolver(v.producto.tipo)
    if datos.atributos is not None:
        ejes = {c.codigo for c in e_.ejes}
        if any(k in ejes and val.vacio(x) for k, x in datos.atributos.items()):
            raise invalido("Los ejes de una variante no pueden quedar vacíos.")
        fijar_valores(db, v.valores, e_.de_nivel("variante"), datos.atributos, False,
                       lambda a: ValorAtributo(atributo=a))
        if ejes & set(datos.atributos):
            v.firma = _firma(e_.ejes, _valores_de_variante(v))
    for k in ("codigo", "nombre", "activa"):
        if k in datos.model_fields_set:
            valor = getattr(datos, k)
            if valor is None and k != "nombre":
                raise invalido(f"El campo {k} no puede quedar vacío.")
            setattr(v, k, valor)
    v.actualizado_en = ahora()
    db.add(v)
    integridad.guardar(db, None, "Ya existe una variante con ese código o con esos valores.")
    return variante_dict(v)


def eliminar_variante(db: Session, producto_id: int, variante_id: int) -> None:
    integridad.borrar(db, _variante(db, producto_id, variante_id), "La variante")

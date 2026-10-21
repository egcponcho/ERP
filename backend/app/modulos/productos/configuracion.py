"""Configuración del módulo: unidades, atributos, tipos de producto,
taxonomías, estados, tipos de identificador y de relación.

Todos los catálogos comparten el mismo alta/edición/baja (`Catalogo`); cada
uno agrega su validación. Un registro en uso no se borra (409): se desactiva.
"""
import re
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import exists, func, select, update
from sqlalchemy.orm import Session

from app.core import integridad
from app.core.errores import conflicto, invalido, no_existe
from app.modulos.productos import esquema as esq
from app.modulos.productos import esquemas as e
from app.modulos.productos import valores
from app.modulos.productos.modelos import (
    Atributo,
    AtributoOpcion,
    Categoria,
    EstadoProducto,
    EstadoTransicion,
    GrupoAtributo,
    Magnitud,
    Producto,
    Taxonomia,
    TipoIdentificador,
    TipoProducto,
    TipoProductoAtributo,
    TipoRelacion,
    UnidadMedida,
    ValorAtributo,
    Variante,
)


def fila_dict(obj) -> dict:
    """Las columnas del registro (sin la organización), con los números como JSON."""
    res = {}
    for col in obj.__table__.columns:
        if col.key == "organizacion_id":
            continue
        v = getattr(obj, col.key)
        res[col.key] = valores.numero(v) if isinstance(v, Decimal) else v
    return res


@dataclass
class Catalogo:
    ruta: str
    nombre: str
    modelo: type
    alta: type[BaseModel]
    validar: Callable[[Session, object, dict], None] | None = None
    a_dict: Callable[[object], dict] = fila_dict
    orden: tuple = ()

    @property
    def edicion(self) -> type[BaseModel]:
        return e.parcial(self.alta)

    def listar(self, db: Session, solo_activos: bool = False) -> list[dict]:
        q = select(self.modelo).order_by(*(self.orden or (self.modelo.codigo,)))
        activo = getattr(self.modelo, "activo", None) or getattr(self.modelo, "activa", None)
        if solo_activos and activo is not None:
            q = q.where(activo.is_(True))
        return [self.a_dict(x) for x in db.scalars(q)]

    def obtener(self, db: Session, id_: int):
        obj = db.get(self.modelo, id_)
        if obj is None:
            raise no_existe(self.nombre)
        return obj

    def crear(self, db: Session, datos: BaseModel) -> dict:
        campos = datos.model_dump(exclude={"opciones"})
        obj = self.modelo(**campos)
        integridad.verificar_referencias(db, obj)
        if self.validar:
            self.validar(db, obj, {"_nuevo": True, **campos})
        integridad.guardar(db, obj, f"Ya existe {self.nombre.lower()} con ese código.")
        return self.a_dict(obj)

    def editar(self, db: Session, id_: int, datos: BaseModel) -> dict:
        obj = self.obtener(db, id_)
        cambios = datos.model_dump(exclude_unset=True)
        antes = {k: getattr(obj, k) for k in cambios}
        for k, v in cambios.items():
            setattr(obj, k, v)
        integridad.verificar_referencias(db, obj)
        if self.validar:
            self.validar(db, obj, {"_antes": antes, **cambios})
        integridad.guardar(db, None, f"Ya existe {self.nombre.lower()} con ese código.")
        return self.a_dict(obj)

    def borrar(self, db: Session, id_: int) -> None:
        integridad.borrar(db, self.obtener(db, id_), self.nombre)


# ---- Validaciones por catálogo ----------------------------------------------------------
def _unidad(db: Session, u: UnidadMedida, cambios: dict) -> None:
    antes = cambios.get("_antes", {})
    if "magnitud_id" in antes and antes["magnitud_id"] != u.magnitud_id and _unidad_en_uso(db, u.id):
        raise conflicto("La unidad ya tiene valores registrados: no puede cambiar de magnitud.")
    if "factor" in antes and Decimal(antes["factor"]) != Decimal(u.factor):
        # Los valores capturados en esta unidad se vuelven a expresar en la unidad de referencia
        db.execute(update(ValorAtributo).where(ValorAtributo.unidad_id == u.id)
                   .values(valor_numero_base=ValorAtributo.valor_numero * Decimal(u.factor))
                   .execution_options(synchronize_session=False))


def _unidad_en_uso(db: Session, unidad_id: int) -> bool:
    return bool(db.scalar(select(exists().where(ValorAtributo.unidad_id == unidad_id))))


def _atributo(db: Session, a: Atributo, cambios: dict) -> None:
    valores.validar_definicion(db, a)
    antes = cambios.get("_antes", {})
    criticos = {k for k in ("tipo_dato", "magnitud_id", "entidad_referencia") if k in antes and antes[k] != getattr(a, k)}
    if criticos and db.scalar(select(exists().where(ValorAtributo.atributo_id == a.id))):
        raise conflicto("El atributo ya tiene valores registrados: no puede cambiar su tipo de dato, magnitud ni entidad.",
                        {"campos": sorted(criticos)})
    if a.tipo_dato not in ("opcion", "opciones") and a.opciones:
        raise invalido("Solo los atributos de tipo opcion u opciones tienen opciones.")


def _tipo(db: Session, t: TipoProducto, cambios: dict) -> None:
    t.padre = db.get(TipoProducto, t.padre_id) if t.padre_id is not None else None
    esq.ruta(t)  # error si forma un ciclo
    # Solo texto fijo y un {seq} con relleno opcional: nada que format() pueda evaluar
    if t.plantilla_codigo and not re.fullmatch(r"[^{}]*\{seq(:0?\d{1,2}d?)?\}[^{}]*", t.plantilla_codigo):
        raise invalido("La plantilla de código lleva texto fijo y un {seq} (con relleno opcional, p. ej. CAL-{seq:05}).")
    if t.plantilla_sku:
        fichas = re.findall(r"\{([^{}]*)\}", t.plantilla_sku)
        if not fichas or any(not re.fullmatch(r"[a-z][a-z0-9_]*", f) for f in fichas):
            raise invalido("La plantilla de SKU usa {producto} y los códigos de los atributos eje, p. ej. {producto}-{talla}.")


def _categoria(db: Session, c: Categoria, _cambios: dict) -> None:
    padre = c.padre = db.get(Categoria, c.padre_id) if c.padre_id is not None else None
    if padre is None:
        return
    if padre.taxonomia_id != c.taxonomia_id:
        raise invalido("La categoría padre debe ser de la misma taxonomía.")
    vistos, x = {c.id}, padre
    while x is not None:
        if x.id in vistos:
            raise invalido("La categoría no puede quedar dentro de sí misma.")
        vistos.add(x.id)
        x = x.padre


def _estado(db: Session, s: EstadoProducto, cambios: dict) -> None:
    if cambios.get("inicial") and s.inicial:
        db.execute(update(EstadoProducto).where(EstadoProducto.id != (s.id or 0)).values(inicial=False)
                   .execution_options(synchronize_session="fetch"))


def _tipo_identificador(_db: Session, t: TipoIdentificador, _cambios: dict) -> None:
    if t.patron:
        try:
            re.compile(t.patron)
        except re.error as ex:
            raise invalido(f"El patrón no es una expresión regular válida ({ex}).") from ex


def _atributo_dict(a: Atributo) -> dict:
    return valores.atributo_dict(a)


def _tipo_dict(t: TipoProducto) -> dict:
    """El tipo con sus asignaciones propias (también las que ocultan un atributo heredado)."""
    return {**fila_dict(t), "atributos": len(t.asignaciones),
            "asignaciones": [{k: getattr(a, k) for k in ("atributo_id", "nivel", "es_eje", "obligatorio", "oculto",
                                                         "valor_defecto", "orden")} for a in t.asignaciones]}


def _estado_dict(s: EstadoProducto) -> dict:
    return fila_dict(s)


CATALOGOS = {c.ruta: c for c in (
    Catalogo("magnitudes", "La magnitud", Magnitud, e.MagnitudEntrada),
    Catalogo("unidades", "La unidad", UnidadMedida, e.UnidadEntrada, _unidad,
             orden=(UnidadMedida.magnitud_id, UnidadMedida.codigo)),
    Catalogo("grupos-atributo", "El grupo de atributos", GrupoAtributo, e.GrupoAtributoEntrada,
             orden=(GrupoAtributo.orden, GrupoAtributo.codigo)),
    Catalogo("atributos", "El atributo", Atributo, e.AtributoEntrada, _atributo, _atributo_dict,
             orden=(Atributo.orden, Atributo.codigo)),
    Catalogo("tipos-producto", "El tipo de producto", TipoProducto, e.TipoProductoEntrada, _tipo, _tipo_dict),
    Catalogo("taxonomias", "La taxonomía", Taxonomia, e.TaxonomiaEntrada),
    Catalogo("categorias", "La categoría", Categoria, e.CategoriaEntrada, _categoria,
             orden=(Categoria.taxonomia_id, Categoria.orden, Categoria.codigo)),
    Catalogo("estados", "El estado", EstadoProducto, e.EstadoEntrada, _estado, _estado_dict,
             orden=(EstadoProducto.orden, EstadoProducto.codigo)),
    Catalogo("tipos-identificador", "El tipo de identificador", TipoIdentificador, e.TipoIdentificadorEntrada,
             _tipo_identificador),
    Catalogo("tipos-relacion", "El tipo de relación", TipoRelacion, e.TipoRelacionEntrada),
)}


# ---- Atributos: alta con opciones y opciones sueltas ---------------------------------------
def crear_atributo(db: Session, datos: e.AtributoAlta) -> dict:
    a = Atributo(**datos.model_dump(exclude={"opciones"}))
    a.opciones = [AtributoOpcion(**o.model_dump()) for o in datos.opciones]
    if len({o.codigo.lower() for o in a.opciones}) != len(a.opciones):
        raise invalido("Hay opciones con el código repetido.")
    integridad.verificar_referencias(db, a)
    _atributo(db, a, {})
    integridad.guardar(db, a, "Ya existe un atributo con ese código.")
    return valores.atributo_dict(a)


def crear_opcion(db: Session, atributo_id: int, datos: e.OpcionEntrada) -> dict:
    a = CATALOGOS["atributos"].obtener(db, atributo_id)
    if a.tipo_dato not in ("opcion", "opciones"):
        raise invalido("Solo los atributos de tipo opcion u opciones tienen opciones.")
    o = AtributoOpcion(atributo=a, **datos.model_dump())
    integridad.guardar(db, o, "Ya existe una opción con ese código en el atributo.")
    return fila_dict(o)


def _opcion(db: Session, atributo_id: int, opcion_id: int) -> AtributoOpcion:
    o = db.get(AtributoOpcion, opcion_id)
    if o is None or o.atributo_id != atributo_id:
        raise no_existe("La opción")
    return o


def editar_opcion(db: Session, atributo_id: int, opcion_id: int, datos: BaseModel) -> dict:
    o = _opcion(db, atributo_id, opcion_id)
    for k, v in datos.model_dump(exclude_unset=True).items():
        setattr(o, k, v)
    integridad.guardar(db, None, "Ya existe una opción con ese código en el atributo.")
    return fila_dict(o)


def borrar_opcion(db: Session, atributo_id: int, opcion_id: int) -> None:
    integridad.borrar(db, _opcion(db, atributo_id, opcion_id), "La opción")


# ---- Tipos de producto: atributos asignados -----------------------------------------------
def _productos_del_arbol(db: Session, tipo_id: int):
    return select(Producto.id).where(Producto.tipo_id.in_(esq.descendientes(db, tipo_id)))


def _hay_valores(db: Session, tipo_id: int, atributo_id: int) -> bool:
    prods = _productos_del_arbol(db, tipo_id)
    variantes = select(Variante.id).where(Variante.producto_id.in_(prods))
    return bool(db.scalar(select(exists().where(
        ValorAtributo.atributo_id == atributo_id,
        ValorAtributo.producto_id.in_(prods) | ValorAtributo.variante_id.in_(variantes)))))


def _hay_variantes(db: Session, tipo_id: int) -> bool:
    return bool(db.scalar(select(exists().where(Variante.producto_id.in_(_productos_del_arbol(db, tipo_id))))))


def _validar_asignacion(db: Session, tipo: TipoProducto, a: TipoProductoAtributo, antes: dict | None) -> None:
    atributo = db.get(Atributo, a.atributo_id)
    if atributo is None:
        raise no_existe("El atributo")
    if a.es_eje and a.nivel != "variante":
        raise invalido("Un atributo eje se captura en la variante (nivel = variante).")
    if a.es_eje and atributo.tipo_dato == "opciones":
        raise invalido("Un atributo de selección múltiple no puede distinguir variantes.")
    if a.valor_defecto is not None:
        if a.es_eje:
            raise invalido("Un atributo eje no lleva valor por defecto: cada variante tiene el suyo.")
        try:
            valores.convertir(db, atributo, a.valor_defecto)
        except ValueError as ex:
            raise invalido(f"Valor por defecto de {atributo.nombre}: {ex}.") from ex
    # Lo que cambia la estructura de los datos ya capturados
    era = antes or {"nivel": None, "es_eje": False, "oculto": False}
    eje_antes = era["es_eje"] and not era["oculto"]
    eje_ahora = a.es_eje and not a.oculto
    if eje_antes != eje_ahora and _hay_variantes(db, tipo.id):
        raise conflicto("Los productos de este tipo ya tienen variantes: no se pueden cambiar sus ejes.")
    if antes and era["nivel"] != a.nivel and _hay_valores(db, tipo.id, a.atributo_id):
        raise conflicto("Ya hay valores capturados de este atributo: no puede cambiar de nivel.")


def esquema(db: Session, tipo_id: int) -> dict:
    return esq.a_dict(esq.resolver(CATALOGOS["tipos-producto"].obtener(db, tipo_id)))


def asignar(db: Session, tipo_id: int, datos: e.AsignacionEntrada) -> dict:
    tipo = CATALOGOS["tipos-producto"].obtener(db, tipo_id)
    if any(x.atributo_id == datos.atributo_id for x in tipo.asignaciones):
        raise conflicto("El atributo ya está asignado a este tipo: edítelo.")
    a = TipoProductoAtributo(tipo=tipo, **datos.model_dump())
    heredada = next((c for c in esq.resolver(tipo.padre).campos if c.atributo.id == datos.atributo_id), None) \
        if tipo.padre else None
    _validar_asignacion(db, tipo, a, heredada and {"nivel": heredada.nivel, "es_eje": heredada.es_eje, "oculto": False})
    integridad.guardar(db, a)
    return esquema(db, tipo_id)


def _asignacion(tipo: TipoProducto, atributo_id: int) -> TipoProductoAtributo:
    a = next((x for x in tipo.asignaciones if x.atributo_id == atributo_id), None)
    if a is None:
        raise no_existe("La asignación del atributo")
    return a


def editar_asignacion(db: Session, tipo_id: int, atributo_id: int, datos: BaseModel) -> dict:
    tipo = CATALOGOS["tipos-producto"].obtener(db, tipo_id)
    a = _asignacion(tipo, atributo_id)
    antes = {"nivel": a.nivel, "es_eje": a.es_eje, "oculto": a.oculto}
    cambios = datos.model_dump(exclude_unset=True)
    cambios.pop("atributo_id", None)
    for k, v in cambios.items():
        setattr(a, k, v)
    _validar_asignacion(db, tipo, a, antes)
    integridad.guardar(db)
    return esquema(db, tipo_id)


def quitar_asignacion(db: Session, tipo_id: int, atributo_id: int) -> dict:
    tipo = CATALOGOS["tipos-producto"].obtener(db, tipo_id)
    a = _asignacion(tipo, atributo_id)
    heredada = next((c for c in esq.resolver(tipo.padre).campos if c.atributo.id == atributo_id), None) \
        if tipo.padre else None
    if heredada is None and _hay_valores(db, tipo_id, atributo_id):
        raise conflicto("Ya hay valores capturados de este atributo: márquelo oculto en lugar de quitarlo.")
    if (a.es_eje and not a.oculto) != bool(heredada and heredada.es_eje) and _hay_variantes(db, tipo_id):
        raise conflicto("Los productos de este tipo ya tienen variantes: no se pueden cambiar sus ejes.")
    tipo.asignaciones.remove(a)
    integridad.guardar(db)
    return esquema(db, tipo_id)


def siguiente_codigo(db: Session, tipo: TipoProducto) -> str | None:
    """El próximo código según la plantilla del tipo (o de su antecesor), con el contador bloqueado."""
    numerador = esq.resolver(tipo).tipo_numerador
    if numerador is None:
        return None
    t = db.scalar(select(TipoProducto).where(TipoProducto.id == numerador.id).with_for_update())
    for _ in range(1000):
        codigo = t.plantilla_codigo.format(seq=t.siguiente_numero)
        t.siguiente_numero += 1
        if not db.scalar(select(exists().where(func.lower(Producto.codigo) == codigo.lower()))):
            return codigo
    raise conflicto("No se encontró un código libre con la plantilla del tipo.")


# ---- Estados: transiciones ----------------------------------------------------------------
def transiciones(db: Session, estado_id: int) -> list[int]:
    CATALOGOS["estados"].obtener(db, estado_id)
    return list(db.scalars(select(EstadoTransicion.destino_id).where(EstadoTransicion.origen_id == estado_id)))


def fijar_transiciones(db: Session, estado_id: int, destinos: list[int]) -> list[int]:
    CATALOGOS["estados"].obtener(db, estado_id)
    for d in destinos:
        CATALOGOS["estados"].obtener(db, d)
    if estado_id in destinos:
        raise invalido("Un estado no transita a sí mismo.")
    actuales = {t.destino_id: t for t in db.scalars(select(EstadoTransicion).where(EstadoTransicion.origen_id == estado_id))}
    for d, t in actuales.items():
        if d not in destinos:
            db.delete(t)
    for d in dict.fromkeys(destinos):
        if d not in actuales:
            db.add(EstadoTransicion(origen_id=estado_id, destino_id=d))
    integridad.guardar(db)
    return transiciones(db, estado_id)

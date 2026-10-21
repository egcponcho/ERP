"""Esquema efectivo de un tipo de producto: los atributos que hereda de sus
antecesores más los propios, la unidad y las plantillas.

Un subtipo puede volver a asignar un atributo del padre para cambiar su
nivel, obligatoriedad, orden o valor por defecto, o marcarlo `oculto` para
quitarlo. Se recorre de la raíz al tipo: la asignación más cercana manda.
"""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.errores import invalido
from app.modulos.productos.modelos import Atributo, TipoProducto, TipoProductoAtributo


@dataclass
class Campo:
    atributo: Atributo
    nivel: str
    es_eje: bool
    obligatorio: bool
    valor_defecto: object
    orden: int
    heredado_de: str | None  # código del tipo antecesor que lo asigna, None si es propio

    @property
    def codigo(self) -> str:
        return self.atributo.codigo


@dataclass
class Esquema:
    tipo: TipoProducto
    ruta: list[TipoProducto]  # de la raíz al tipo
    campos: list[Campo]

    def de_nivel(self, nivel: str) -> list[Campo]:
        return [c for c in self.campos if c.nivel == nivel]

    @property
    def ejes(self) -> list[Campo]:
        return [c for c in self.campos if c.es_eje]

    def campo(self, codigo: str) -> Campo | None:
        return next((c for c in self.campos if c.codigo == codigo), None)

    def heredado(self, nombre: str):
        """El primer valor no vacío de una propiedad del tipo, del tipo a la raíz."""
        return next((getattr(t, nombre) for t in reversed(self.ruta) if getattr(t, nombre) not in (None, "")), None)

    @property
    def unidad_defecto_id(self) -> int | None:
        return self.heredado("unidad_defecto_id")

    @property
    def plantilla_sku(self) -> str | None:
        return self.heredado("plantilla_sku")

    @property
    def tipo_numerador(self) -> TipoProducto | None:
        """El tipo (él mismo o un antecesor) cuya plantilla y contador numeran sus productos."""
        return next((t for t in reversed(self.ruta) if t.plantilla_codigo), None)


def ruta(tipo: TipoProducto) -> list[TipoProducto]:
    res, t = [], tipo
    while t is not None:
        if t in res:
            raise invalido(f"El tipo {tipo.codigo} forma un ciclo con sus antecesores.")
        res.insert(0, t)
        t = t.padre
    return res


def resolver(tipo: TipoProducto) -> Esquema:
    camino = ruta(tipo)
    por_atributo: dict[int, tuple[TipoProductoAtributo, TipoProducto]] = {}
    for t in camino:
        for a in t.asignaciones:
            por_atributo[a.atributo_id] = (a, t)
    campos = [
        Campo(a.atributo, a.nivel, a.es_eje, a.obligatorio, a.valor_defecto, a.orden,
              None if t.id == tipo.id else t.codigo)
        for a, t in por_atributo.values() if not a.oculto and a.atributo.activo
    ]
    campos.sort(key=lambda c: (c.nivel != "producto", c.orden, c.atributo.orden, c.atributo.id))
    return Esquema(tipo, camino, campos)


def descendientes(db: Session, tipo_id: int) -> set[int]:
    """El tipo y todos sus subtipos (para filtrar productos por tipo)."""
    from sqlalchemy import select

    hijos: dict[int | None, list[int]] = {}
    for i, p in db.execute(select(TipoProducto.id, TipoProducto.padre_id)):
        hijos.setdefault(p, []).append(i)
    res, pendientes = set(), [tipo_id]
    while pendientes:
        i = pendientes.pop()
        if i not in res:
            res.add(i)
            pendientes.extend(hijos.get(i, []))
    return res


def a_dict(e: Esquema) -> dict:
    from app.modulos.productos.valores import atributo_dict

    return {
        "tipo": {"id": e.tipo.id, "codigo": e.tipo.codigo, "nombre": e.tipo.nombre},
        "ruta": [t.codigo for t in e.ruta],
        "unidad_defecto_id": e.unidad_defecto_id,
        "plantilla_sku": e.plantilla_sku,
        "campos": [{"atributo": atributo_dict(c.atributo), "nivel": c.nivel, "es_eje": c.es_eje,
                    "obligatorio": c.obligatorio, "valor_defecto": c.valor_defecto, "orden": c.orden,
                    "heredado_de": c.heredado_de} for c in e.campos],
    }

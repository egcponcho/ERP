"""Contratos de entrada de la API de productos (pydantic).

Cada catálogo de configuración tiene su modelo de alta; el de edición es el
mismo con todos los campos opcionales (`parcial`).
"""
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

Codigo = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9][A-Za-z0-9._\-]*$")


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")


def parcial(modelo: type[BaseModel]) -> type[BaseModel]:
    """El mismo modelo con todos sus campos opcionales (para PATCH)."""
    campos = {n: (f.annotation | None, None) for n, f in modelo.model_fields.items()}
    return create_model(f"{modelo.__name__}Edicion", __base__=Entrada, **campos)


# ---- Configuración ----------------------------------------------------------------------
class MagnitudEntrada(Entrada):
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    activa: bool = True


class UnidadEntrada(Entrada):
    codigo: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9][A-Za-z0-9._\-/]*$")
    nombre: str = Field(min_length=1, max_length=100)
    simbolo: str | None = Field(default=None, max_length=20)
    magnitud_id: int
    factor: Decimal = Field(default=Decimal(1), gt=0)
    decimales: int = Field(default=0, ge=0, le=10)
    activa: bool = True


class GrupoAtributoEntrada(Entrada):
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    orden: int = 0
    activo: bool = True


class OpcionEntrada(Entrada):
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    orden: int = 0
    activa: bool = True


class AtributoEntrada(Entrada):
    codigo: str = Field(min_length=1, max_length=40, pattern=r"^[a-z][a-z0-9_]*$")
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str | None = Field(default=None, max_length=500)
    tipo_dato: Literal["texto", "entero", "decimal", "booleano", "fecha", "opcion", "opciones", "referencia"]
    magnitud_id: int | None = None
    unidad_defecto_id: int | None = None
    entidad_referencia: str | None = None
    reglas: dict[str, Any] = Field(default_factory=dict)
    grupo_id: int | None = None
    orden: int = 0
    activo: bool = True


class AtributoAlta(AtributoEntrada):
    opciones: list[OpcionEntrada] = Field(default_factory=list)


class TipoProductoEntrada(Entrada):
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str | None = Field(default=None, max_length=500)
    padre_id: int | None = None
    unidad_defecto_id: int | None = None
    plantilla_codigo: str | None = Field(default=None, max_length=60)
    siguiente_numero: int = Field(default=1, ge=1)
    plantilla_sku: str | None = Field(default=None, max_length=120)
    activo: bool = True


class AsignacionEntrada(Entrada):
    atributo_id: int
    nivel: Literal["producto", "variante"] = "producto"
    es_eje: bool = False
    obligatorio: bool = False
    oculto: bool = False
    valor_defecto: Any = None
    orden: int = 0


class TaxonomiaEntrada(Entrada):
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    multiple: bool = False
    obligatoria: bool = False
    activa: bool = True


class CategoriaEntrada(Entrada):
    taxonomia_id: int
    padre_id: int | None = None
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    orden: int = 0
    activa: bool = True


class EstadoEntrada(Entrada):
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    orden: int = 0
    inicial: bool = False
    exige_completo: bool = False
    operable: bool = False
    activo: bool = True


class TransicionesEntrada(Entrada):
    destinos: list[int]


class TipoIdentificadorEntrada(Entrada):
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    patron: str | None = Field(default=None, max_length=200)
    activo: bool = True


class TipoRelacionEntrada(Entrada):
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    nombre_inverso: str | None = Field(default=None, max_length=100)
    con_cantidad: bool = False
    activo: bool = True


# ---- Productos --------------------------------------------------------------------------
class ProductoAlta(Entrada):
    codigo: str | None = Field(default=None, min_length=1, max_length=60)
    nombre: str = Field(min_length=1, max_length=200)
    descripcion: str | None = None
    tipo_id: int
    unidad_id: int | None = None
    estado_id: int | None = None
    atributos: dict[str, Any] = Field(default_factory=dict)
    categorias: list[int] = Field(default_factory=list)


class ProductoEdicion(Entrada):
    version: int  # la que se leyó: si otro la cambió entretanto, 409
    codigo: str | None = Field(default=None, min_length=1, max_length=60)
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    descripcion: str | None = None
    tipo_id: int | None = None
    unidad_id: int | None = None
    atributos: dict[str, Any] | None = None  # se combinan con los actuales; null o "" quita el valor
    categorias: list[int] | None = None  # reemplaza la lista completa
    descartar_atributos: bool = False  # al cambiar de tipo, borrar los valores que el nuevo tipo no tiene


class CambioEstado(Entrada):
    estado_id: int
    version: int | None = None


class VarianteAlta(Entrada):
    codigo: str | None = Field(default=None, min_length=1, max_length=80)
    nombre: str | None = Field(default=None, max_length=250)
    atributos: dict[str, Any] = Field(default_factory=dict)
    activa: bool = True


class VarianteEdicion(Entrada):
    version: int
    codigo: str | None = Field(default=None, min_length=1, max_length=80)
    nombre: str | None = Field(default=None, max_length=250)
    atributos: dict[str, Any] | None = None
    activa: bool | None = None


class GenerarVariantes(Entrada):
    """Combinaciones de los ejes: {"color": ["NEGRO", "BLANCO"], "talla": ["38", "39"]}."""

    ejes: dict[str, list[Any]]
    atributos: dict[str, Any] = Field(default_factory=dict)  # valores comunes de los demás atributos de variante


class PresentacionEntrada(Entrada):
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    unidad_id: int
    cantidad: Decimal = Field(gt=0)
    variante_id: int | None = None
    activa: bool = True


class IdentificadorEntrada(Entrada):
    tipo_id: int
    valor: str = Field(min_length=1, max_length=100)
    variante_id: int | None = None
    presentacion_id: int | None = None


class RelacionEntrada(Entrada):
    tipo_id: int
    destino_id: int
    destino_variante_id: int | None = None
    cantidad: Decimal | None = Field(default=None, gt=0)
    unidad_id: int | None = None
    orden: int = 0


class RevisionAlta(Entrada):
    motivo: str | None = Field(default=None, max_length=500)

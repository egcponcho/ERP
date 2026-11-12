"""Contrato del módulo de productos (ver app/core/modulos.py).

Es lo único que el resto del sistema conoce de este módulo: sus tablas, sus
rutas, sus datos sugeridos y lo que ofrece a otros módulos.

Ofrece a otros módulos:
- La entidad referenciable «producto» (core.referencias): cualquier atributo
  de tipo `referencia` puede apuntar a un producto, y un módulo futuro
  (compras, inventario) puede guardar el id y mostrar su nombre sin importar
  este código.
- El verificador de uso: antes de borrar un registro referenciable de
  cualquier módulo, se pregunta si algún atributo de producto lo usa.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import referencias
from app.core.modulos import Modulo
from app.modulos.productos import api
from app.modulos.productos.instalacion import cargar_base
from app.modulos.productos.modelos import Atributo, Producto, ValorAtributo


def _rutas() -> list:
    # La configuración va primero: /api/productos/config/... no debe tomarse como /api/productos/{id}
    return [api.config, api.router]


def _uso_en_atributos(db: Session, clave: str, id_: int) -> str | None:
    """¿Algún producto tiene un atributo que apunta a este registro?"""
    a = db.scalar(select(Atributo).join(ValorAtributo, ValorAtributo.atributo_id == Atributo.id)
                  .where(Atributo.entidad_referencia == clave, ValorAtributo.referencia_id == id_).limit(1))
    return f"lo referencia el atributo {a.nombre}" if a else None


def _al_cargar() -> None:
    referencias.registrar("producto", Producto)
    referencias.registrar_verificador(_uso_en_atributos)


MODULO = Modulo(
    clave="productos",
    nombre="Productos",
    descripcion="Catálogo universal: tipos, atributos, variantes, presentaciones y códigos.",
    icono="cubo",
    modelos="app.modulos.productos.modelos",
    rutas=_rutas,
    instalar=cargar_base,
    al_cargar=_al_cargar,
)

"""Entidades a las que puede apuntar un atributo de tipo `referencia`.

Cada módulo registra las suyas al importarse (registrar("producto", Producto)).
Cuando se incorpore un maestro nuevo (marcas, proveedores, fabricantes…),
basta registrarlo para que cualquier tipo de producto pueda tener un atributo
que lo referencie, sin cambiar el modelo de productos.
"""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class Entidad:
    clave: str
    modelo: type
    etiqueta: str = "nombre"  # columna con la que se muestra


_REGISTRO: dict[str, Entidad] = {}


def registrar(clave: str, modelo: type, etiqueta: str = "nombre") -> None:
    _REGISTRO[clave] = Entidad(clave, modelo, etiqueta)


def entidades() -> list[str]:
    return sorted(_REGISTRO)


def existe(clave: str) -> bool:
    return clave in _REGISTRO


def obtener(db: Session, clave: str, id_: int):
    """El registro referenciado (filtrado por la organización de la sesión) o None."""
    e = _REGISTRO.get(clave)
    return db.get(e.modelo, id_) if e else None


def etiquetas(db: Session, clave: str, ids: set[int]) -> dict[int, str]:
    e = _REGISTRO.get(clave)
    if not e or not ids:
        return {}
    filas = db.execute(select(e.modelo.id, getattr(e.modelo, e.etiqueta)).where(e.modelo.id.in_(ids)))
    return {i: str(n) for i, n in filas}


# Quién usa un registro referenciable: cada módulo que guarda referencias registra
# una función (db, clave, id) -> descripción del uso o None. Al borrar un registro
# referenciable se consulta antes (en_uso).
_VERIFICADORES: list = []


def registrar_verificador(funcion) -> None:
    _VERIFICADORES.append(funcion)


def en_uso(db: Session, clave: str, id_: int) -> str | None:
    return next((u for f in _VERIFICADORES if (u := f(db, clave, id_))), None)

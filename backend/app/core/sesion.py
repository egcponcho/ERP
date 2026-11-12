"""Sesión de base de datos de cada petición (dependencia de FastAPI).

Las rutas la piden con `db: DB` y confirman con `db.commit()` cuando escriben;
si algo falla antes, la transacción se descarta al cerrar.

Mientras no exista el módulo de acceso, la sesión trabaja en la organización
por defecto (ORGANIZACION_POR_DEFECTO). Al incorporar el inicio de sesión, la
organización saldrá del usuario autenticado y este es el único lugar que cambia.
"""
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core import organizacion
from app.core.config import settings
from app.core.db import SessionLocal


def organizacion_actual() -> int:
    return settings.ORGANIZACION_POR_DEFECTO


def obtener_db() -> Iterator[Session]:
    db = SessionLocal()
    organizacion.fijar(db, organizacion_actual())
    try:
        yield db
    finally:
        db.close()


DB = Annotated[Session, Depends(obtener_db)]

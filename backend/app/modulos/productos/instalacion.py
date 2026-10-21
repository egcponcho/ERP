"""Carga la configuración inicial sugerida (datos/base.json) en una organización.

Solo agrega lo que no existe (por código): se puede correr de nuevo sin
duplicar ni pisar lo que la organización ya cambió.

    python -m app.modulos.productos.instalacion [organizacion_id]
"""
import json
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modulos.productos.modelos import (
    EstadoProducto,
    EstadoTransicion,
    Magnitud,
    TipoIdentificador,
    TipoRelacion,
    UnidadMedida,
)

BASE = Path(__file__).parent / "datos" / "base.json"


def _por_codigo(db: Session, modelo) -> dict:
    return {x.codigo: x for x in db.scalars(select(modelo))}


def _agregar(db: Session, modelo, filas: list[dict], **resolver) -> dict:
    actuales = _por_codigo(db, modelo)
    for f in filas:
        if f["codigo"] not in actuales:
            datos = {k: v for k, v in f.items() if k not in resolver}
            datos.update({destino: fn(f[k]) for k, (destino, fn) in resolver.items()})
            actuales[f["codigo"]] = modelo(**datos)
            db.add(actuales[f["codigo"]])
    db.flush()
    return actuales


def cargar_base(db: Session, archivo: Path = BASE) -> None:
    base = json.loads(archivo.read_text(encoding="utf-8"))
    magnitudes = _agregar(db, Magnitud, base["magnitudes"])
    _agregar(db, UnidadMedida, base["unidades"], magnitud=("magnitud_id", lambda c: magnitudes[c].id))
    hay_inicial = db.scalar(select(EstadoProducto.id).where(EstadoProducto.inicial.is_(True)).limit(1))
    estados = _agregar(db, EstadoProducto, [{**f, "inicial": f.get("inicial", False) and not hay_inicial}
                                            for f in base["estados"]])
    existentes = {tuple(r) for r in db.execute(select(EstadoTransicion.origen_id, EstadoTransicion.destino_id))}
    for origen, destinos in base["transiciones"].items():
        for d in destinos:
            if origen not in estados or d not in estados:
                continue
            par = (estados[origen].id, estados[d].id)
            if par not in existentes:
                db.add(EstadoTransicion(origen_id=par[0], destino_id=par[1]))
    _agregar(db, TipoIdentificador, base["tipos_identificador"])
    _agregar(db, TipoRelacion, base["tipos_relacion"])
    db.flush()


if __name__ == "__main__":
    from app.core import organizacion
    from app.core.db import SessionLocal
    from app.modelos import importar_todo

    importar_todo()
    with SessionLocal() as sesion:
        organizacion.fijar(sesion, int(sys.argv[1]) if len(sys.argv) > 1 else 1)
        cargar_base(sesion)
        sesion.commit()
    print("Configuración base cargada.")

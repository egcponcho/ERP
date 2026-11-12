"""Carga la configuración sugerida de todos los módulos activos en una organización.

    python -m app.instalar [organizacion_id] [--crear "Nombre de la empresa"]

Solo agrega lo que falta (por código), así que se puede correr varias veces sin
duplicar ni pisar lo que la organización ya cambió. Con --crear, si la
organización no existe se crea con ese nombre.
"""
import argparse

from app.core import modulos, organizacion
from app.core.db import SessionLocal
from app.core.organizacion import Organizacion


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("organizacion_id", nargs="?", type=int, default=1)
    p.add_argument("--crear", metavar="NOMBRE", help="crea la organización si no existe")
    args = p.parse_args()

    modulos.importar_modelos()
    with SessionLocal() as db:
        if db.get(Organizacion, args.organizacion_id) is None:
            if not args.crear:
                raise SystemExit(f"La organización {args.organizacion_id} no existe (use --crear \"Nombre\").")
            db.add(Organizacion(id=args.organizacion_id, codigo=f"ORG{args.organizacion_id}", nombre=args.crear))
            db.commit()
        organizacion.fijar(db, args.organizacion_id)
        modulos.instalar(db)
        db.commit()
    print(f"Configuración sugerida cargada en la organización {args.organizacion_id}: "
          + ", ".join(m.nombre for m in modulos.cargar()))


if __name__ == "__main__":
    main()

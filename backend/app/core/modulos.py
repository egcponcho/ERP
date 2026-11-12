"""Contrato y registro de módulos.

Un módulo es una carpeta en `app/modulos/<clave>/` con un archivo `modulo.py`
que expone `MODULO = Modulo(...)`. Ese objeto es lo único que el resto del
sistema conoce del módulo:

    Modulo(
        clave="productos",                       # carpeta y prefijo de la API
        nombre="Productos",                      # cómo se muestra en la interfaz
        modelos="app.modulos.productos.modelos", # tablas (para Alembic y el arranque)
        rutas=lambda: [api.config, api.router],  # routers de FastAPI
        instalar=instalacion.cargar_base,        # datos sugeridos de una organización nueva
        al_cargar=registrar_referencias,         # registra lo que ofrece a otros módulos
        depende_de=(),                           # claves de los módulos que necesita
    )

Reglas que mantienen los módulos independientes (las revisa
tests/test_arquitectura.py):

1. Un módulo solo importa de `app.core` y de sí mismo. Nunca de otro módulo.
2. Lo que un módulo ofrece a otros se publica en un registro de `app.core`
   (por ejemplo `core.referencias`: «un atributo puede apuntar a un producto»).
   El otro módulo lo consume por la clave, sin importar su código.
3. `core` no conoce a ningún módulo.

Qué módulos se cargan lo decide la variable de entorno `MODULOS`
(`MODULOS=productos,compras`). Sin ella se cargan todos los que haya en
`app/modulos/`. Un módulo apagado no expone rutas ni aparece en la interfaz.
"""
from __future__ import annotations

import importlib
import importlib.util
import pkgutil
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

PAQUETE = "app.modulos"


@dataclass(frozen=True)
class Modulo:
    clave: str
    nombre: str
    modelos: str
    rutas: Callable[[], list] = field(default=lambda: [])
    instalar: Callable[[Session], None] | None = None
    al_cargar: Callable[[], None] | None = None
    depende_de: tuple[str, ...] = ()
    descripcion: str = ""
    icono: str = ""  # nombre del ícono en la interfaz (frontend/src/componentes/Icono.vue)

    def resumen(self) -> dict:
        """Lo que la interfaz necesita saber del módulo (GET /api/modulos)."""
        return {"clave": self.clave, "nombre": self.nombre, "descripcion": self.descripcion, "icono": self.icono}


def disponibles() -> list[str]:
    """Las carpetas de app/modulos/ que tienen modulo.py."""
    paquete = importlib.import_module(PAQUETE)
    return sorted(m.name for m in pkgutil.iter_modules(paquete.__path__)
                  if m.ispkg and importlib.util.find_spec(f"{PAQUETE}.{m.name}.modulo") is not None)


def _ordenar(modulos: dict[str, Modulo]) -> list[Modulo]:
    """Orden de carga: cada módulo después de los que necesita."""
    orden: list[Modulo] = []
    visitando: set[str] = set()

    def visitar(m: Modulo) -> None:
        if m in orden:
            return
        if m.clave in visitando:
            raise RuntimeError(f"Dependencia circular entre módulos en «{m.clave}».")
        visitando.add(m.clave)
        for d in m.depende_de:
            if d not in modulos:
                raise RuntimeError(f"El módulo «{m.clave}» necesita «{d}», que no está activo.")
            visitar(modulos[d])
        visitando.discard(m.clave)
        orden.append(m)

    for m in modulos.values():
        visitar(m)
    return orden


_CARGADOS: list[Modulo] | None = None


def cargar(claves: list[str] | None = None) -> list[Modulo]:
    """Importa los módulos activos (una sola vez) y devuelve su contrato en orden de dependencias.

    `claves` None toma la variable MODULOS o, si no está, todos los disponibles."""
    global _CARGADOS
    if _CARGADOS is not None and claves is None:
        return _CARGADOS
    from app.core.config import settings

    elegidos = claves or settings.MODULOS or disponibles()
    faltan = sorted(set(elegidos) - set(disponibles()))
    if faltan:
        raise RuntimeError(f"No existen los módulos: {', '.join(faltan)} (revise la variable MODULOS).")
    contratos = {}
    for clave in elegidos:
        m = importlib.import_module(f"{PAQUETE}.{clave}.modulo").MODULO
        if m.clave != clave:
            raise RuntimeError(f"app/modulos/{clave}/modulo.py declara la clave «{m.clave}».")
        importlib.import_module(m.modelos)
        contratos[clave] = m
    orden = _ordenar(contratos)
    for m in orden:
        if m.al_cargar:
            m.al_cargar()
    if claves is None:
        _CARGADOS = orden
    return orden


def importar_modelos() -> None:
    """Deja registradas en Base.metadata las tablas de core y de los módulos activos."""
    from app.core import organizacion  # noqa: F401  (tabla organizaciones)

    cargar()


def instalar(db: Session) -> None:
    """Carga los datos sugeridos de cada módulo activo en la organización de la sesión.
    Cada `instalar` solo agrega lo que falta: se puede correr varias veces."""
    for m in cargar():
        if m.instalar:
            m.instalar(db)

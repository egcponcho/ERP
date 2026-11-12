"""Configuración por variables de entorno.

| Variable                  | Para qué                                                     | Por defecto              |
|---------------------------|--------------------------------------------------------------|--------------------------|
| DATABASE_URL              | Base de datos (PostgreSQL en producción)                     | sqlite:///./erp.db       |
| MODULOS                   | Módulos activos, separados por coma (productos,compras)      | todos los de app/modulos |
| ORGANIZACION_POR_DEFECTO  | Organización de la API mientras no haya inicio de sesión     | 1                        |
| FRONTEND_DIST             | Carpeta de la interfaz compilada (npm run build)             | frontend/dist            |
"""
import os
from pathlib import Path


def url_base_datos(url: str) -> str:
    """La URL con el controlador psycopg 3: las plataformas (Render, Railway…) la dan
    como postgres:// o postgresql://, que SQLAlchemy asociaría a psycopg2."""
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url


def _lista(valor: str | None) -> list[str]:
    return [x.strip() for x in (valor or "").split(",") if x.strip()]


class Config:
    DATABASE_URL: str = url_base_datos(os.environ.get("DATABASE_URL", "sqlite:///./erp.db"))
    MODULOS: list[str] = _lista(os.environ.get("MODULOS"))
    ORGANIZACION_POR_DEFECTO: int = int(os.environ.get("ORGANIZACION_POR_DEFECTO", "1"))
    FRONTEND_DIST: Path = Path(os.environ.get("FRONTEND_DIST", Path(__file__).resolve().parents[3] / "frontend" / "dist"))


settings = Config()

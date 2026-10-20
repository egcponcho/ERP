"""Configuración por variables de entorno."""
import os


class Config:
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./erp.db").replace("postgres://", "postgresql+psycopg://", 1)
    # Organización con la que trabaja la API mientras no exista el módulo de acceso
    ORGANIZACION_POR_DEFECTO: int = int(os.environ.get("ORGANIZACION_POR_DEFECTO", "1"))


settings = Config()

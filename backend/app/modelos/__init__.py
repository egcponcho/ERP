"""Punto único que importa los modelos de todos los módulos (para Alembic y el arranque)."""


def importar_todo() -> None:
    from app.core import organizacion  # noqa: F401
    from app.modulos.productos import modelos, productos  # noqa: F401  (productos registra sus referencias)

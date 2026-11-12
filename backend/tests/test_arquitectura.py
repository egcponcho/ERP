"""Reglas de arquitectura que mantienen los módulos independientes (app/core/modulos.py).

Se revisan leyendo el código (ast), sin ejecutarlo:

1. `app.core` no importa ningún módulo de negocio.
2. Un módulo solo importa de `app.core` y de sí mismo: nunca de otro módulo.
3. No hay imports dentro de funciones (en facturacion eran la forma de esquivar
   ciclos; aquí un ciclo es un error de diseño que debe verse).
4. Ningún archivo de servicio pasa de 500 líneas.
5. Cada módulo tiene su contrato (modulo.py con MODULO).
"""
import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
MAX_LINEAS = 500


def _archivos(carpeta: Path) -> list[Path]:
    return sorted(p for p in carpeta.rglob("*.py") if "__pycache__" not in p.parts)


def _imports(arbol: ast.AST) -> list[tuple[str, int, bool]]:
    """(módulo importado, línea, ¿está dentro de una función?)"""
    res = []

    def visitar(nodo, en_funcion: bool):
        for hijo in ast.iter_child_nodes(nodo):
            dentro = en_funcion or isinstance(hijo, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda)
            if isinstance(hijo, ast.Import):
                res.extend((a.name, hijo.lineno, en_funcion) for a in hijo.names)
            elif isinstance(hijo, ast.ImportFrom) and hijo.module and hijo.level == 0:
                res.append((hijo.module, hijo.lineno, en_funcion))
            visitar(hijo, dentro)

    visitar(arbol, False)
    return res


def _modulo_de(archivo: Path) -> str | None:
    partes = archivo.relative_to(APP).parts
    return partes[1] if partes[0] == "modulos" and len(partes) > 2 else None


MODULOS = sorted(p.name for p in (APP / "modulos").iterdir() if p.is_dir() and (p / "__init__.py").exists())


def test_core_no_conoce_modulos():
    malos = [f"{a.relative_to(APP)}:{n} importa {m}"
             for a in _archivos(APP / "core") for m, n, _ in _imports(ast.parse(a.read_text()))
             if m.startswith("app.modulos.")]
    assert not malos, "core no debe depender de un módulo:\n" + "\n".join(malos)


def test_modulos_no_se_importan_entre_si():
    malos = []
    for a in _archivos(APP / "modulos"):
        propio = _modulo_de(a)
        for m, n, _ in _imports(ast.parse(a.read_text())):
            if m.startswith("app.") and not (m.startswith("app.core") or m.startswith(f"app.modulos.{propio}")):
                malos.append(f"{a.relative_to(APP)}:{n} importa {m}")
    assert not malos, ("Un módulo solo importa de app.core y de sí mismo; publique lo que otro necesita en un "
                       "registro de core (p. ej. core.referencias):\n" + "\n".join(malos))


def test_sin_imports_dentro_de_funciones():
    malos = [f"{a.relative_to(APP)}:{n} importa {m}"
             for a in _archivos(APP) for m, n, dentro in _imports(ast.parse(a.read_text()))
             if dentro and m.startswith("app.") and a.name != "modulos.py"]
    assert not malos, "Imports dentro de funciones (suelen esconder un ciclo):\n" + "\n".join(malos)


def test_archivos_de_tamano_razonable():
    grandes = [f"{a.relative_to(APP)}: {n} líneas" for a in _archivos(APP)
               if (n := len(a.read_text().splitlines())) > MAX_LINEAS]
    assert not grandes, f"Divida por responsabilidad los archivos de más de {MAX_LINEAS} líneas:\n" + "\n".join(grandes)


@pytest.mark.parametrize("clave", MODULOS)
def test_cada_modulo_tiene_contrato(clave):
    contrato = APP / "modulos" / clave / "modulo.py"
    assert contrato.exists(), f"app/modulos/{clave}/ necesita modulo.py con MODULO = Modulo(...)"
    assert "MODULO = Modulo(" in contrato.read_text()

"""El registro de módulos: carga, orden por dependencias y módulos apagados."""
import pytest

from app.core import modulos
from app.core.modulos import Modulo, _ordenar


def test_productos_esta_disponible_y_activo(cli):
    assert "productos" in modulos.disponibles()
    activos = cli.ok("get", "/api/modulos")
    assert {"clave": "productos", "nombre": "Productos"}.items() <= activos[0].items()


def test_orden_por_dependencias():
    a = Modulo(clave="a", nombre="A", modelos="", depende_de=("b",))
    b = Modulo(clave="b", nombre="B", modelos="")
    assert [m.clave for m in _ordenar({"a": a, "b": b})] == ["b", "a"]


def test_dependencia_faltante_o_circular():
    a = Modulo(clave="a", nombre="A", modelos="", depende_de=("b",))
    with pytest.raises(RuntimeError, match="necesita «b»"):
        _ordenar({"a": a})
    b = Modulo(clave="b", nombre="B", modelos="", depende_de=("a",))
    with pytest.raises(RuntimeError, match="circular"):
        _ordenar({"a": a, "b": b})


def test_modulo_inexistente():
    with pytest.raises(RuntimeError, match="No existen los módulos: inventado"):
        modulos.cargar(["inventado"])

"""Relaciones entre productos, referencias a otras entidades, cambio de tipo,
concurrencia, aislamiento entre organizaciones y migraciones."""
from pathlib import Path

from alembic.config import Config
from sqlalchemy import text

from alembic import command
from app.core.db import crear_motor
from tests.conftest import URL_PRUEBAS, C, Cliente, nuevo_atributo, nuevo_tipo

P = "/api/productos"


def _producto(cli, tipo, codigo, **kw):
    return cli.ok("post", P, json={"tipo_id": tipo, "codigo": codigo, "nombre": codigo, **kw})


def test_lista_de_materiales_sin_ciclos(cli):
    tipo = nuevo_tipo(cli, "GENERAL", [], unidad_defecto_id=cli.id_de("unidades", "UN"))
    comp = cli.id_de("tipos-relacion", "COMPONENTE")
    sust = cli.id_de("tipos-relacion", "SUSTITUTO")
    kg = cli.id_de("unidades", "KG")
    mesa, tablero, tornillo = (_producto(cli, tipo, c) for c in ("MESA", "TABLERO", "TORNILLO"))
    cli.ok("post", f"{P}/{mesa['id']}/relaciones", json={"tipo_id": comp, "destino_id": tablero["id"], "cantidad": 1})
    cli.ok("post", f"{P}/{tablero['id']}/relaciones", json={"tipo_id": comp, "destino_id": tornillo["id"], "cantidad": 8})
    cli.ok("post", f"{P}/{tablero['id']}/relaciones", 409, json={"tipo_id": comp, "destino_id": tornillo["id"], "cantidad": 2})
    cli.ok("post", f"{P}/{tornillo['id']}/relaciones", 409, json={"tipo_id": comp, "destino_id": mesa["id"], "cantidad": 1})
    cli.ok("post", f"{P}/{mesa['id']}/relaciones", 422, json={"tipo_id": comp, "destino_id": mesa["id"], "cantidad": 1})
    cli.ok("post", f"{P}/{mesa['id']}/relaciones", 422, json={"tipo_id": comp, "destino_id": tornillo["id"]})
    cli.ok("post", f"{P}/{mesa['id']}/relaciones", 422, json={"tipo_id": sust, "destino_id": tornillo["id"], "cantidad": 1,
                                                             "unidad_id": kg})
    # Un sustituto en sentido contrario no es un ciclo de componentes
    sustituto = cli.ok("post", f"{P}/{tornillo['id']}/relaciones", json={"tipo_id": sust, "destino_id": mesa["id"]})

    usado = cli.ok("get", f"{P}/{tornillo['id']}/usado-en")
    assert [(u["nombre"], u["origen"]["codigo"], u["cantidad"]) for u in usado] == [("Usado en", "TABLERO", 8)]
    # Un componente en uso no se borra en silencio
    cli.ok("delete", f"{P}/{tornillo['id']}", 409)
    cli.ok("delete", f"{P}/{mesa['id']}", 409)  # la mesa es destino del sustituto
    cli.ok("delete", f"{P}/{tornillo['id']}/relaciones/{sustituto['id']}")
    cli.ok("delete", f"{P}/{mesa['id']}")  # ya no es destino de nada: se borra con sus relaciones de origen
    assert cli.ok("get", f"{P}/{tornillo['id']}/usado-en")[0]["origen"]["codigo"] == "TABLERO"


def test_atributo_referencia_a_otra_entidad(cli):
    assert "producto" in cli.ok("get", f"{C}/entidades-referenciables")
    base = nuevo_atributo(cli, "producto_base", "referencia", entidad_referencia="producto")
    tipo = nuevo_tipo(cli, "REEMPAQUE", [{"atributo_id": base}], unidad_defecto_id=cli.id_de("unidades", "UN"))
    granel = _producto(cli, tipo, "GRANEL")
    cli.ok("post", P, 422, json={"tipo_id": tipo, "codigo": "R1", "nombre": "R1", "atributos": {"producto_base": 999}})
    r = _producto(cli, tipo, "R1", atributos={"producto_base": granel["id"]})
    assert r["atributos"]["producto_base"] == granel["id"]
    assert "Producto base" in cli.ok("delete", f"{P}/{granel['id']}", 409)["mensaje"]


def test_cambio_de_tipo_conserva_o_descarta_atributos(cli):
    color = nuevo_atributo(cli, "color", "texto")
    peso = nuevo_atributo(cli, "peso", "decimal")
    un = cli.id_de("unidades", "UN")
    a = nuevo_tipo(cli, "A", [{"atributo_id": color}, {"atributo_id": peso}], unidad_defecto_id=un)
    b = nuevo_tipo(cli, "B", [{"atributo_id": peso}], unidad_defecto_id=un)
    p = _producto(cli, a, "X", atributos={"color": "Rojo", "peso": 3})
    r = cli.ok("patch", f"{P}/{p['id']}", 409, json={"version": p["version"], "tipo_id": b})
    assert r["detalle"]["atributos"] == ["color"]
    p = cli.ok("patch", f"{P}/{p['id']}", json={"version": p["version"], "tipo_id": b, "descartar_atributos": True})
    assert p["tipo"]["codigo"] == "B" and p["atributos"] == {"peso": 3}

    # Ocultar un atributo en el tipo no borra los valores: quedan aparte
    cli.ok("patch", f"{C}/tipos-producto/{b}/atributos/{peso}", json={"oculto": True})
    p = cli.ok("get", f"{P}/{p['id']}")
    assert p["atributos"] == {} and p["atributos_fuera_de_esquema"] == {"peso": 3}
    # Con valores, no se puede quitar la asignación ni cambiar el tipo de dato del atributo
    cli.ok("delete", f"{C}/tipos-producto/{b}/atributos/{peso}", 409)
    cli.ok("patch", f"{C}/atributos/{peso}", 409, json={"tipo_dato": "texto"})


def test_concurrencia_optimista(cli):
    tipo = nuevo_tipo(cli, "G", [], unidad_defecto_id=cli.id_de("unidades", "UN"))
    p = _producto(cli, tipo, "X")
    cli.ok("patch", f"{P}/{p['id']}", json={"version": p["version"], "nombre": "Primera edición"})
    r = cli.ok("patch", f"{P}/{p['id']}", 409, json={"version": p["version"], "nombre": "Edición atrasada"})
    assert r["detalle"]["version_actual"] == p["version"] + 1


def test_organizaciones_aisladas(fabrica, cli):
    tipo = nuevo_tipo(cli, "G", [], unidad_defecto_id=cli.id_de("unidades", "UN"))
    p = _producto(cli, tipo, "SECRETO")
    unidad_a = cli.id_de("unidades", "KG")
    otra = Cliente(fabrica, org=2)  # desde aquí las peticiones son de la organización 2
    assert otra.ok("get", P)["total"] == 0
    otra.ok("get", f"{P}/{p['id']}", 404)
    otra.ok("patch", f"{P}/{p['id']}", 404, json={"version": 1, "nombre": "x"})
    # No puede usar la configuración de la otra organización
    otra.ok("post", P, 404, json={"tipo_id": tipo, "codigo": "X", "nombre": "X"})
    tipo_b = nuevo_tipo(otra, "G", [], unidad_defecto_id=otra.id_de("unidades", "UN"))
    r = otra.ok("post", P, 422, json={"tipo_id": tipo_b, "codigo": "X", "nombre": "X", "unidad_id": unidad_a})
    assert r["detalle"][0]["campo"] == "unidad_id"
    # El mismo código puede existir en cada organización
    assert otra.ok("post", P, json={"tipo_id": tipo_b, "codigo": "SECRETO", "nombre": "Otro"})["codigo"] == "SECRETO"


def test_migraciones_coinciden_con_los_modelos(tmp_path):
    cfg = Config(str(Path(__file__).parent.parent / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).parent.parent / "alembic"))
    cfg.attributes["url"] = URL_PRUEBAS or f"sqlite:///{tmp_path / 'm.db'}"
    if URL_PRUEBAS:  # parte de una base vacía
        with crear_motor(URL_PRUEBAS).begin() as con:
            con.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
    command.upgrade(cfg, "head")
    command.check(cfg)  # falla si los modelos tienen cambios sin migración
    command.downgrade(cfg, "base")


def test_url_de_la_plataforma_usa_psycopg():
    from app.core.config import url_base_datos

    assert url_base_datos("postgres://u:c@h/b") == "postgresql+psycopg://u:c@h/b"
    assert url_base_datos("postgresql://u:c@h/b") == "postgresql+psycopg://u:c@h/b"
    assert url_base_datos("postgresql+psycopg://u@h/b") == "postgresql+psycopg://u@h/b"
    assert url_base_datos("sqlite:///./erp.db") == "sqlite:///./erp.db"

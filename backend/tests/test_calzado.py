"""Calzado: variantes por color y talla, código automático, SKU por plantilla y estados."""
import pytest

from tests.conftest import C, nuevo_atributo, nuevo_tipo

P = "/api/productos"


@pytest.fixture
def calzado(cli):
    color = nuevo_atributo(cli, "color", "opcion", ["NEGRO", "BLANCO"])
    talla = nuevo_atributo(cli, "talla", "opcion", ["38", "39", "40"])
    material = nuevo_atributo(cli, "material", "opcion", ["CUERO", "LONA"])
    temporada = nuevo_atributo(cli, "temporada", "texto")
    tipo = nuevo_tipo(cli, "CALZADO", [
        {"atributo_id": material, "obligatorio": True},
        {"atributo_id": temporada},
        {"atributo_id": color, "nivel": "variante", "es_eje": True, "orden": 1},
        {"atributo_id": talla, "nivel": "variante", "es_eje": True, "orden": 2},
    ], plantilla_codigo="CAL-{seq:05}", plantilla_sku="{producto}-{color}-{talla}", unidad_defecto_id=cli.id_de("unidades", "PAR"))
    return tipo


def test_producto_con_variantes(cli, calzado):
    p = cli.ok("post", P, json={"nombre": "Bota de trabajo", "tipo_id": calzado, "atributos": {"material": "cuero"}})
    assert p["codigo"] == "CAL-00001" and p["unidad"]["codigo"] == "PAR" and p["estado"]["codigo"] == "BORRADOR"
    assert p["atributos"] == {"material": "CUERO"}

    r = cli.ok("post", f"{P}/{p['id']}/variantes/generar", json={"ejes": {"color": ["NEGRO", "BLANCO"], "talla": ["38", "39", "40"]}})
    assert len(r["creadas"]) == 6 and r["omitidas"] == []
    skus = {v["codigo"] for v in r["creadas"]}
    assert "CAL-00001-NEGRO-38" in skus and "CAL-00001-BLANCO-40" in skus
    assert r["creadas"][0]["nombre"] == "Bota de trabajo Negro / 38"

    # Generar de nuevo no duplica: informa las combinaciones que ya existen
    r = cli.ok("post", f"{P}/{p['id']}/variantes/generar", json={"ejes": {"color": ["NEGRO"], "talla": ["38", "39"]}})
    assert r["creadas"] == [] and len(r["omitidas"]) == 2

    cli.ok("post", f"{P}/{p['id']}/variantes", 409, json={"atributos": {"color": "NEGRO", "talla": "38"}})
    cli.ok("post", f"{P}/{p['id']}/variantes", 422, json={"atributos": {"color": "NEGRO"}})
    cli.ok("post", f"{P}/{p['id']}/variantes", 422, json={"atributos": {"color": "ROJO", "talla": "38"}})

    segundo = cli.ok("post", P, json={"nombre": "Tenis", "tipo_id": calzado, "atributos": {"material": "LONA"}})
    assert segundo["codigo"] == "CAL-00002"


def test_cambiar_un_eje_no_puede_duplicar_otra_variante(cli, calzado):
    p = cli.ok("post", P, json={"nombre": "Sandalia", "tipo_id": calzado, "atributos": {"material": "LONA"}})
    a = cli.ok("post", f"{P}/{p['id']}/variantes", json={"atributos": {"color": "NEGRO", "talla": "38"}})
    b = cli.ok("post", f"{P}/{p['id']}/variantes", json={"atributos": {"color": "NEGRO", "talla": "39"}})
    cli.ok("patch", f"{P}/{p['id']}/variantes/{b['id']}", 409, json={"version": b["version"], "atributos": {"talla": "38"}})
    cli.ok("patch", f"{P}/{p['id']}/variantes/{b['id']}", 422, json={"version": b["version"], "atributos": {"talla": None}})
    b = cli.ok("patch", f"{P}/{p['id']}/variantes/{b['id']}", json={"version": b["version"], "atributos": {"talla": "40"}})
    assert b["atributos"] == {"color": "NEGRO", "talla": "40"} and b["version"] == 2
    assert a["codigo"] != b["codigo"]


def test_estado_activo_exige_ficha_completa(cli, calzado):
    activo = cli.id_de("estados", "ACTIVO")
    descontinuado = cli.id_de("estados", "DESCONTINUADO")
    p = cli.ok("post", P, json={"nombre": "Mocasín", "tipo_id": calzado})
    assert p["faltantes"] == [{"nivel": "producto", "atributo": "material", "nombre": "Material"}]
    r = cli.ok("post", f"{P}/{p['id']}/estado", 422, json={"estado_id": activo})
    assert r["detalle"]["faltantes"][0]["atributo"] == "material"
    # De Borrador no se puede saltar a Descontinuado (transiciones configuradas)
    cli.ok("post", f"{P}/{p['id']}/estado", 409, json={"estado_id": descontinuado})

    p = cli.ok("patch", f"{P}/{p['id']}", json={"version": p["version"], "atributos": {"material": "CUERO"}})
    p = cli.ok("post", f"{P}/{p['id']}/estado", 200, json={"estado_id": activo})
    assert p["estado"]["codigo"] == "ACTIVO" and p["estado"]["operable"]
    # Ya activo, no puede quedar incompleto
    cli.ok("patch", f"{P}/{p['id']}", 422, json={"version": p["version"], "atributos": {"material": None}})


def test_no_se_cambian_ejes_con_variantes(cli, calzado):
    p = cli.ok("post", P, json={"nombre": "Bota", "tipo_id": calzado, "atributos": {"material": "CUERO"}})
    cli.ok("post", f"{P}/{p['id']}/variantes", json={"atributos": {"color": "NEGRO", "talla": "38"}})
    ancho = nuevo_atributo(cli, "ancho", "opcion", ["E", "EE"])
    cli.ok("post", f"{C}/tipos-producto/{calzado}/atributos", 409, json={"atributo_id": ancho, "nivel": "variante", "es_eje": True})
    color = cli.id_de("atributos", "color")
    cli.ok("delete", f"{C}/tipos-producto/{calzado}/atributos/{color}", 409)
    # Agregar un atributo de variante que no es eje sí se puede
    cli.ok("post", f"{C}/tipos-producto/{calzado}/atributos", 201, json={"atributo_id": ancho, "nivel": "variante"})


def test_filtros_por_atributo(cli, calzado):
    a = cli.ok("post", P, json={"nombre": "Bota", "tipo_id": calzado, "atributos": {"material": "CUERO", "temporada": "Invierno 2026"}})
    b = cli.ok("post", P, json={"nombre": "Tenis", "tipo_id": calzado, "atributos": {"material": "LONA"}})
    cli.ok("post", f"{P}/{a['id']}/variantes", json={"atributos": {"color": "NEGRO", "talla": "38"}})
    cli.ok("post", f"{P}/{b['id']}/variantes", json={"atributos": {"color": "BLANCO", "talla": "38"}})

    def codigos(**params):
        return [x["codigo"] for x in cli.ok("get", P, params=params)["datos"]]

    assert codigos(**{"a.material": "LONA"}) == [b["codigo"]]
    assert codigos(**{"a.color": "NEGRO"}) == [a["codigo"]]  # el valor es de una variante
    assert codigos(**{"a.talla": "38"}) == [a["codigo"], b["codigo"]]
    assert codigos(**{"a.temporada": "invierno"}) == [a["codigo"]]
    assert codigos(q="tenis") == [b["codigo"]]
    assert codigos(q="cal-00001-negro") == [a["codigo"]]  # busca también por SKU
    cli.ok("get", P, 422, params={"a.noexiste": "x"})

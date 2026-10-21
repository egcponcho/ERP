"""Asistente de alta: todo junto o nada, vista previa sin guardar y errores con su camino."""
import pytest

from tests.conftest import nuevo_atributo, nuevo_tipo

P = "/api/productos"


@pytest.fixture
def calzado(cli):
    color = nuevo_atributo(cli, "color", "opcion", ["NEGRO", "BLANCO"])
    talla = nuevo_atributo(cli, "talla", "opcion", ["38", "39"])
    material = nuevo_atributo(cli, "material", "opcion", ["CUERO"])
    return nuevo_tipo(cli, "CALZADO", [
        {"atributo_id": material, "obligatorio": True},
        {"atributo_id": color, "nivel": "variante", "es_eje": True},
        {"atributo_id": talla, "nivel": "variante", "es_eje": True},
    ], plantilla_codigo="CAL-{seq:03}", plantilla_sku="{producto}-{color}-{talla}", unidad_defecto_id=cli.id_de("unidades", "PAR"))


def _datos(cli, tipo, **kw):
    return {
        "producto": {"tipo_id": tipo, "nombre": "Bota", "atributos": {"material": "CUERO"}},
        "variantes": [{"atributos": {"color": c, "talla": t}} for c in ("NEGRO", "BLANCO") for t in ("38", "39")],
        "presentaciones": [{"codigo": "CJ6", "nombre": "Caja de 6 pares", "unidad_id": cli.id_de("unidades", "UN"), "cantidad": 6}],
        "identificadores": [{"tipo_id": cli.id_de("tipos-identificador", "EAN13"), "valor": "7501234567890", "presentacion_codigo": "CJ6"}],
        "estado_id": cli.id_de("estados", "ACTIVO"),
        **kw,
    }


def test_validar_no_guarda_nada(cli, calzado):
    r = cli.ok("post", f"{P}/asistente?validar=true", 201, json=_datos(cli, calzado))
    assert r["validado"] and r["id"] is None and r["codigo"] == "CAL-001"
    assert sorted(v["codigo"] for v in r["variantes"]) == ["CAL-001-BLANCO-38", "CAL-001-BLANCO-39", "CAL-001-NEGRO-38", "CAL-001-NEGRO-39"]
    assert r["estado"]["codigo"] == "ACTIVO"
    assert cli.ok("get", P)["total"] == 0
    # El contador del tipo tampoco avanzó
    assert cli.ok("post", f"{P}/asistente?validar=true", 201, json=_datos(cli, calzado))["codigo"] == "CAL-001"


def test_crea_todo_junto(cli, calzado):
    p = cli.ok("post", f"{P}/asistente", 201, json=_datos(cli, calzado))
    assert p["id"] and len(p["variantes"]) == 4 and p["estado"]["codigo"] == "ACTIVO"
    assert p["presentaciones"][0]["codigo"] == "CJ6"
    assert p["identificadores"][0]["presentacion_id"] == p["presentaciones"][0]["id"]


def test_errores_con_su_camino_y_sin_guardar_nada(cli, calzado):
    datos = _datos(cli, calzado)
    datos["variantes"].append({"atributos": {"color": "NEGRO", "talla": "38"}})  # repetida
    datos["presentaciones"].append({"codigo": "X", "nombre": "X", "unidad_id": cli.id_de("unidades", "UN"), "cantidad": 1})
    datos["identificadores"].append({"tipo_id": cli.id_de("tipos-identificador", "EAN13"), "valor": "123"})
    r = cli.ok("post", f"{P}/asistente", 422, json=datos)
    campos = {d["campo"] for d in r["detalle"]}
    assert campos == {"variantes.4", "identificadores.1"}
    assert cli.ok("get", P)["total"] == 0

    sin_material = _datos(cli, calzado)
    sin_material["producto"]["atributos"] = {"material": "PIEL"}
    r = cli.ok("post", f"{P}/asistente", 422, json=sin_material)
    assert r["detalle"][0]["campo"] == "producto.atributos.material"


def test_estado_final_exige_ficha_completa(cli, calzado):
    datos = _datos(cli, calzado)
    datos["producto"]["atributos"] = {}
    r = cli.ok("post", f"{P}/asistente", 422, json=datos)
    assert r["detalle"][0]["campo"] == "estado" and r["detalle"][0]["faltantes"][0]["atributo"] == "material"
    assert cli.ok("get", P)["total"] == 0
    datos["estado_id"] = None  # queda en borrador
    assert cli.ok("post", f"{P}/asistente", 201, json=datos)["estado"]["codigo"] == "BORRADOR"


def test_filtros_por_columna_y_sus_valores(cli, calzado):
    cli.ok("post", f"{P}/asistente", 201, json=_datos(cli, calzado))
    otro = nuevo_tipo(cli, "OTRO", [], unidad_defecto_id=cli.id_de("unidades", "UN"))
    cli.ok("post", P, json={"tipo_id": otro, "codigo": "X1", "nombre": "Otro"})
    assert cli.ok("get", P, params={"tipo": "OTRO"})["total"] == 1
    assert cli.ok("get", P, params=[("estado", "ACTIVO"), ("estado", "BORRADOR")])["total"] == 2
    valores = cli.ok("get", f"{P}/valores/estado")
    assert {(v["valor"], v["n"]) for v in valores} == {("ACTIVO", 1), ("BORRADOR", 1)}
    # Los valores de una columna respetan los demás filtros, no el suyo
    assert [v["valor"] for v in cli.ok("get", f"{P}/valores/estado", params={"tipo": "OTRO", "estado": "ACTIVO"})] == ["BORRADOR"]
    assert [x["codigo"] for x in cli.ok("get", P, params={"orden": "tipo:desc"})["datos"]] == ["X1", "CAL-001"]
    cli.ok("get", f"{P}/valores/nombre", 422)


def test_resumen_del_modulo_y_pendientes(cli, calzado):
    vacio = cli.ok("get", f"{P}/resumen")
    assert vacio["total"] == 0 and vacio["recientes"] == [] and all(x["n"] == 0 for x in vacio["por_estado"])
    cli.ok("post", f"{P}/asistente", 201, json=_datos(cli, calzado))
    cli.ok("post", f"{P}/asistente", 201, json=_datos(cli, calzado, presentaciones=[], identificadores=[], estado_id=None))
    r = cli.ok("get", f"{P}/resumen")
    assert (r["total"], r["operables"], r["variantes"], r["presentaciones"]) == (2, 1, 8, 1)
    assert {x["codigo"]: x["n"] for x in r["por_estado"]}["BORRADOR"] == 1
    assert r["por_tipo"] == [{"codigo": "CALZADO", "nombre": "Calzado", "n": 2}]
    assert r["pendientes"] == {"sin_codigos": 1, "sin_categorias": 2, "sin_presentaciones": 1}
    assert len(r["recientes"]) == 2
    # Cada pendiente lleva a su filtro del catálogo
    assert [p["codigo"] for p in cli.ok("get", P, params={"pendiente": "sin_codigos"})["datos"]] == ["CAL-002"]
    assert cli.ok("get", f"{P}/valores/estado", params={"pendiente": "sin_codigos"}) == [{"valor": "BORRADOR", "texto": "Borrador", "n": 1}]
    cli.ok("get", P, 422, params={"pendiente": "otro"})

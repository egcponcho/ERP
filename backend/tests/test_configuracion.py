from tests.conftest import C, nuevo_atributo, nuevo_tipo


def test_esquema_hereda_cambia_y_oculta_atributos(cli):
    marca = nuevo_atributo(cli, "marca", "texto")
    garantia = nuevo_atributo(cli, "garantia_meses", "entero", reglas={"minimo": 0, "maximo": 120})
    voltaje = nuevo_atributo(cli, "voltaje", "opcion", ["110V", "220V"])
    padre = nuevo_tipo(cli, "ELECTRO", [
        {"atributo_id": marca, "obligatorio": True},
        {"atributo_id": garantia, "valor_defecto": 12},
    ])
    hijo = nuevo_tipo(cli, "REFRI", [
        {"atributo_id": voltaje, "nivel": "variante", "es_eje": True},
        {"atributo_id": garantia, "valor_defecto": 24},  # cambia el valor por defecto del padre
    ], padre_id=padre)
    nieto = nuevo_tipo(cli, "MINIBAR", [{"atributo_id": marca, "oculto": True}], padre_id=hijo)

    e = cli.ok("get", f"{C}/tipos-producto/{hijo}/esquema")
    campos = {c["atributo"]["codigo"]: c for c in e["campos"]}
    assert e["ruta"] == ["ELECTRO", "REFRI"]
    assert campos["marca"]["heredado_de"] == "ELECTRO" and campos["marca"]["obligatorio"]
    assert campos["garantia_meses"]["valor_defecto"] == 24 and campos["garantia_meses"]["heredado_de"] is None
    assert campos["voltaje"]["es_eje"]

    e = cli.ok("get", f"{C}/tipos-producto/{nieto}/esquema")
    assert {c["atributo"]["codigo"] for c in e["campos"]} == {"garantia_meses", "voltaje"}


def test_tipos_no_forman_ciclos(cli):
    a = nuevo_tipo(cli, "A", [])
    b = nuevo_tipo(cli, "B", [], padre_id=a)
    r = cli.ok("patch", f"{C}/tipos-producto/{a}", 422, json={"padre_id": b})
    assert "ciclo" in r["mensaje"]


def test_validaciones_de_definicion(cli):
    masa = cli.id_de("magnitudes", "MASA")
    litro = cli.id_de("unidades", "L")
    base = {"codigo": "peso", "nombre": "Peso"}
    cli.ok("post", f"{C}/atributos", 422, json={**base, "tipo_dato": "texto", "magnitud_id": masa})
    cli.ok("post", f"{C}/atributos", 422, json={**base, "tipo_dato": "decimal", "magnitud_id": masa, "unidad_defecto_id": litro})
    cli.ok("post", f"{C}/atributos", 422, json={**base, "tipo_dato": "texto", "reglas": {"minimo": 1}})
    cli.ok("post", f"{C}/atributos", 422, json={**base, "tipo_dato": "texto", "reglas": {"patron": "("}})
    cli.ok("post", f"{C}/atributos", 422, json={**base, "tipo_dato": "referencia", "entidad_referencia": "nada"})
    cli.ok("post", f"{C}/atributos", 422, json={**base, "tipo_dato": "valor_raro"})
    cli.ok("post", f"{C}/tipos-producto", 422, json={"codigo": "X", "nombre": "X", "plantilla_codigo": "X-{numero}"})
    cli.ok("post", f"{C}/tipos-producto", 422, json={"codigo": "X", "nombre": "X", "plantilla_codigo": "{seq.__class__}"})
    cli.ok("post", f"{C}/tipos-producto", 201, json={"codigo": "Y", "nombre": "Y", "plantilla_codigo": "Y{seq}"})
    cli.ok("post", f"{C}/tipos-producto", 422, json={"codigo": "X", "nombre": "X", "plantilla_sku": "{Producto}"})
    multiple = nuevo_atributo(cli, "alergenos", "opciones", ["GLUTEN"])
    t = nuevo_tipo(cli, "T", [])
    r = cli.ok("post", f"{C}/tipos-producto/{t}/atributos", 422, json={"atributo_id": multiple, "nivel": "variante", "es_eje": True})
    assert "múltiple" in r["mensaje"]
    cli.ok("post", f"{C}/tipos-producto/{t}/atributos", 422, json={"atributo_id": multiple, "es_eje": True})


def test_codigo_repetido_y_borrado_en_uso(cli):
    cli.ok("post", f"{C}/magnitudes", 409, json={"codigo": "MASA", "nombre": "Otra"})
    r = cli.ok("delete", f"{C}/magnitudes/{cli.id_de('magnitudes', 'MASA')}", 409)
    assert "desactívelo" in r["mensaje"]
    tiempo = cli.ok("post", f"{C}/magnitudes", json={"codigo": "TIEMPO", "nombre": "Tiempo"})["id"]
    cli.ok("delete", f"{C}/magnitudes/{tiempo}")


def test_un_solo_estado_inicial(cli):
    nuevo = cli.ok("post", f"{C}/estados", json={"codigo": "PROPUESTO", "nombre": "Propuesto", "inicial": True})
    iniciales = [x["codigo"] for x in cli.ok("get", f"{C}/estados") if x["inicial"]]
    assert iniciales == ["PROPUESTO"] and nuevo["inicial"]


def test_opciones_de_un_atributo(cli):
    color = nuevo_atributo(cli, "color", "opcion", ["ROJO"])
    azul = cli.ok("post", f"{C}/atributos/{color}/opciones", json={"codigo": "AZUL", "nombre": "Azul", "orden": 2})
    cli.ok("post", f"{C}/atributos/{color}/opciones", 409, json={"codigo": "AZUL", "nombre": "Otro azul"})
    cli.ok("patch", f"{C}/atributos/{color}/opciones/{azul['id']}", json={"nombre": "Azul marino"})
    a = cli.ok("get", f"{C}/atributos/{color}")
    assert [o["nombre"] for o in a["opciones"]] == ["Rojo", "Azul marino"]
    texto = nuevo_atributo(cli, "nota", "texto")
    cli.ok("post", f"{C}/atributos/{texto}/opciones", 422, json={"codigo": "X", "nombre": "X"})

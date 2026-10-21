"""Químicos y alimentos: números con unidad, rangos, formatos, fechas, selección
múltiple, presentaciones, identificadores y revisiones. Sin variantes."""
import pytest

from tests.conftest import C, nuevo_atributo, nuevo_tipo

P = "/api/productos"


@pytest.fixture
def quimico(cli):
    masa, vol = cli.id_de("magnitudes", "MASA"), cli.id_de("magnitudes", "VOLUMEN")
    kg, litro = cli.id_de("unidades", "KG"), cli.id_de("unidades", "L")
    cas = nuevo_atributo(cli, "numero_cas", "texto", reglas={"patron": r"\d{2,7}-\d{2}-\d"})
    pureza = nuevo_atributo(cli, "pureza", "decimal", reglas={"minimo": 0, "maximo": 100, "decimales": 2})
    peso = nuevo_atributo(cli, "peso_neto", "decimal", magnitud_id=masa, unidad_defecto_id=kg, reglas={"maximo": 1000})
    contenido = nuevo_atributo(cli, "contenido", "decimal", magnitud_id=vol, unidad_defecto_id=litro)
    peligroso = nuevo_atributo(cli, "peligroso", "booleano")
    return nuevo_tipo(cli, "QUIMICO", [
        {"atributo_id": cas, "obligatorio": True}, {"atributo_id": pureza}, {"atributo_id": peso},
        {"atributo_id": contenido}, {"atributo_id": peligroso, "valor_defecto": False},
    ], unidad_defecto_id=kg)


def test_numeros_con_unidad_y_reglas(cli, quimico):
    base = {"tipo_id": quimico, "codigo": "Q-1", "nombre": "Ácido cítrico"}
    r = cli.ok("post", P, 422, json={**base, "atributos": {"numero_cas": "77-92", "pureza": 100.5,
                                                             "peso_neto": {"valor": 5, "unidad": "L"}}})
    assert {x["campo"] for x in r["detalle"]} == {"atributos.numero_cas", "atributos.pureza", "atributos.peso_neto"}
    cli.ok("post", P, 422, json={**base, "atributos": {"numero_cas": "77-92-9", "pureza": 99.555}})
    cli.ok("post", P, 422, json={**base, "atributos": {"numero_cas": "77-92-9", "peso_neto": {"valor": 1001, "unidad": "KG"}}})
    cli.ok("post", P, 422, json={**base, "atributos": {"numero_cas": "77-92-9", "inventado": 1}})

    p = cli.ok("post", P, json={**base, "atributos": {"numero_cas": "77-92-9", "pureza": "99.5",
                                                       "peso_neto": {"valor": 500, "unidad": "G"}, "contenido": 2}})
    assert p["atributos"] == {"numero_cas": "77-92-9", "pureza": 99.5, "peso_neto": {"valor": 500, "unidad": "G"},
                              "contenido": {"valor": 2, "unidad": "L"}, "peligroso": False}

    otro = cli.ok("post", P, json={**base, "codigo": "Q-2", "nombre": "Soda cáustica",
                                    "atributos": {"numero_cas": "1310-73-2", "peso_neto": {"valor": 25, "unidad": "KG"}}})

    def codigos(**params):
        return [x["codigo"] for x in cli.ok("get", P, params=params)["datos"]]

    # Los rangos comparan en la unidad de referencia: 500 g < 1 kg < 25 kg
    assert codigos(**{"a.peso_neto__min": "1"}) == [otro["codigo"]]
    assert codigos(**{"a.peso_neto__max": "600 G"}) == ["Q-1"]
    assert codigos(**{"a.peso_neto": "0.5"}) == ["Q-1"]
    assert codigos(**{"a.peligroso": "no"}) == ["Q-1", "Q-2"]


def test_cambiar_factor_de_unidad_recalcula_valores(cli, quimico):
    cli.ok("post", P, json={"tipo_id": quimico, "codigo": "Q-1", "nombre": "X",
                            "atributos": {"numero_cas": "77-92-9", "peso_neto": {"valor": 2, "unidad": "LB"}}})
    assert [x["codigo"] for x in cli.ok("get", P, params={"a.peso_neto__min": "0.9"})["datos"]] == ["Q-1"]
    lb = cli.id_de("unidades", "LB")
    cli.ok("patch", f"{C}/unidades/{lb}", json={"factor": 0.4})  # 2 lb pasan a valer 0.8 kg
    assert cli.ok("get", P, params={"a.peso_neto__min": "0.9"})["datos"] == []


def test_presentaciones_e_identificadores(cli, quimico):
    p = cli.ok("post", P, json={"tipo_id": quimico, "codigo": "Q-1", "nombre": "Glicerina", "atributos": {"numero_cas": "56-81-5"}})
    kg = cli.id_de("unidades", "KG")
    tambor = cli.ok("post", f"{P}/{p['id']}/presentaciones", json={"codigo": "TAMBOR", "nombre": "Tambor 250 kg",
                                                                   "unidad_id": cli.id_de("unidades", "UN"), "cantidad": 250})
    cli.ok("post", f"{P}/{p['id']}/presentaciones", 409, json={"codigo": "TAMBOR", "nombre": "Otro", "unidad_id": kg, "cantidad": 1})
    cli.ok("post", f"{P}/{p['id']}/presentaciones", 422, json={"codigo": "X", "nombre": "X", "unidad_id": kg, "cantidad": 0})

    ean = cli.id_de("tipos-identificador", "EAN13")
    cli.ok("post", f"{P}/{p['id']}/identificadores", 422, json={"tipo_id": ean, "valor": "123"})
    cli.ok("post", f"{P}/{p['id']}/identificadores", json={"tipo_id": ean, "valor": "7501234567890", "presentacion_id": tambor["id"]})
    otro = cli.ok("post", P, json={"tipo_id": quimico, "codigo": "Q-2", "nombre": "Otro", "atributos": {"numero_cas": "56-81-5"}})
    cli.ok("post", f"{P}/{otro['id']}/identificadores", 409, json={"tipo_id": ean, "valor": "7501234567890"})
    cli.ok("post", f"{P}/{otro['id']}/identificadores", 422, json={"tipo_id": ean, "valor": "7501234567891",
                                                                   "presentacion_id": tambor["id"]})

    encontrado = cli.ok("get", f"{P}/por-identificador", params={"valor": "7501234567890"})
    assert encontrado[0]["producto"]["codigo"] == "Q-1" and encontrado[0]["presentacion_id"] == tambor["id"]
    detalle = cli.ok("get", f"{P}/{p['id']}")
    assert detalle["presentaciones"][0]["cantidad"] == 250 and detalle["identificadores"][0]["tipo"] == "EAN13"


def test_alimento_fechas_seleccion_multiple_y_revisiones(cli):
    alergenos = nuevo_atributo(cli, "alergenos", "opciones", ["GLUTEN", "LACTOSA", "NUECES"], reglas={"maximo": 2})
    vence = nuevo_atributo(cli, "vence", "fecha", reglas={"minimo": "2026-01-01"})
    vida = nuevo_atributo(cli, "vida_util_dias", "entero", reglas={"minimo": 1})
    tipo = nuevo_tipo(cli, "ALIMENTO", [{"atributo_id": alergenos}, {"atributo_id": vence}, {"atributo_id": vida, "obligatorio": True}],
                      plantilla_codigo="ALI{seq:03}", unidad_defecto_id=cli.id_de("unidades", "UN"))
    cli.ok("post", P, 422, json={"tipo_id": tipo, "nombre": "Galleta", "atributos": {"alergenos": ["GLUTEN", "LACTOSA", "NUECES"]}})
    cli.ok("post", P, 422, json={"tipo_id": tipo, "nombre": "Galleta", "atributos": {"vence": "2025-12-31"}})
    cli.ok("post", P, 422, json={"tipo_id": tipo, "nombre": "Galleta", "atributos": {"vida_util_dias": 1.5}})
    p = cli.ok("post", P, json={"tipo_id": tipo, "nombre": "Galleta", "atributos": {
        "alergenos": ["lactosa", "GLUTEN"], "vence": "2027-03-01", "vida_util_dias": 180}})
    assert p["codigo"] == "ALI001" and p["atributos"]["alergenos"] == ["GLUTEN", "LACTOSA"]
    assert [x["codigo"] for x in cli.ok("get", P, params={"a.alergenos": "NUECES,LACTOSA"})["datos"]] == ["ALI001"]
    assert cli.ok("get", P, params={"a.alergenos": "NUECES"})["datos"] == []
    assert len(cli.ok("get", P, params={"a.vence__max": "2027-12-31"})["datos"]) == 1

    # Un tipo sin ejes no maneja variantes
    cli.ok("post", f"{P}/{p['id']}/variantes", 409, json={"atributos": {}})

    r1 = cli.ok("post", f"{P}/{p['id']}/revisiones", json={"motivo": "Ficha inicial"})
    p = cli.ok("patch", f"{P}/{p['id']}", json={"version": cli.ok("get", f"{P}/{p['id']}")["version"],
                                                 "atributos": {"vida_util_dias": 200, "alergenos": None}})
    assert "alergenos" not in p["atributos"]
    r2 = cli.ok("post", f"{P}/{p['id']}/revisiones", json={"motivo": "Nueva receta"})
    revisiones = cli.ok("get", f"{P}/{p['id']}/revisiones")
    assert [r["numero"] for r in revisiones] == [1, 2]
    assert revisiones[0]["vigente_hasta"] == r2["vigente_desde"] and revisiones[1]["vigente_hasta"] is None
    assert r1["datos"]["atributos"]["vida_util_dias"] == 180
    assert cli.ok("get", f"{P}/{p['id']}/revisiones/2")["datos"]["atributos"]["vida_util_dias"] == 200
    assert cli.ok("get", f"{P}/{p['id']}")["revision"] == 2

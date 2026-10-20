from tests.conftest import C, nuevo_tipo

P = "/api/productos"


def test_taxonomias_y_arbol_de_categorias(cli):
    linea = cli.ok("post", f"{C}/taxonomias", json={"codigo": "LINEA", "nombre": "Línea comercial", "obligatoria": True})["id"]
    canal = cli.ok("post", f"{C}/taxonomias", json={"codigo": "CANAL", "nombre": "Canal", "multiple": True})["id"]

    def cat(tax, codigo, padre=None, esperado=201):
        return cli.ok("post", f"{C}/categorias", esperado, json={"taxonomia_id": tax, "codigo": codigo, "nombre": codigo,
                                                                 "padre_id": padre})

    hogar = cat(linea, "HOGAR")["id"]
    cocina = cat(linea, "COCINA", hogar)["id"]
    deportes = cat(linea, "DEPORTES")["id"]
    web, tienda = cat(canal, "WEB")["id"], cat(canal, "TIENDA")["id"]
    cat(canal, "X", hogar, 422)  # el padre es de otra taxonomía
    cli.ok("patch", f"{C}/categorias/{hogar}", 422, json={"padre_id": cocina})  # ciclo

    tipo = nuevo_tipo(cli, "G", [], unidad_defecto_id=cli.id_de("unidades", "UN"))
    cli.ok("post", P, 422, json={"tipo_id": tipo, "codigo": "A", "nombre": "A", "categorias": [cocina, deportes]})
    p = cli.ok("post", P, json={"tipo_id": tipo, "codigo": "SARTEN", "nombre": "Sartén", "categorias": [cocina, web, tienda]})
    assert {c["codigo"] for c in p["categorias"]} == {"COCINA", "WEB", "TIENDA"}
    sin = cli.ok("post", P, json={"tipo_id": tipo, "codigo": "B", "nombre": "B"})
    assert sin["faltantes"] == [{"nivel": "categoria", "taxonomia": "LINEA", "nombre": "Línea comercial"}]

    # Filtrar por una categoría incluye sus subcategorías
    assert [x["codigo"] for x in cli.ok("get", P, params={"categoria_id": hogar})["datos"]] == ["SARTEN"]
    cli.ok("delete", f"{C}/categorias/{cocina}", 409)  # en uso

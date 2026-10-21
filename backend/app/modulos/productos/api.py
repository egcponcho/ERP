"""Rutas del módulo de productos.

/api/productos/config/...   catálogos de configuración (unidades, atributos, tipos…)
/api/productos/...          productos, variantes, presentaciones, identificadores, relaciones y revisiones
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core import referencias
from app.modulos.productos import asistente
from app.modulos.productos import complementos as comp
from app.modulos.productos import configuracion as conf
from app.modulos.productos import esquemas as e
from app.modulos.productos import productos as prod
from app.web.dependencias import obtener_db

DB = Annotated[Session, Depends(obtener_db)]
Codigos = Annotated[list[str] | None, Query()]  # parámetro repetible: ?tipo=A&tipo=B

router = APIRouter(prefix="/api/productos", tags=["productos"])
config = APIRouter(prefix="/api/productos/config", tags=["productos: configuración"])


def _rutas_catalogo(c: conf.Catalogo) -> None:
    Alta, Edicion = c.alta, c.edicion  # noqa: N806

    @config.get(f"/{c.ruta}", name=f"listar_{c.ruta}")
    def listar(db: DB, activos: bool = False):
        return c.listar(db, activos)

    @config.get(f"/{c.ruta}/{{id_}}", name=f"ver_{c.ruta}")
    def ver(db: DB, id_: int):
        return c.a_dict(c.obtener(db, id_))

    if c.ruta != "atributos":  # el alta de atributos lleva sus opciones (abajo)
        @config.post(f"/{c.ruta}", status_code=status.HTTP_201_CREATED, name=f"crear_{c.ruta}")
        def crear(db: DB, datos: Alta):
            res = c.crear(db, datos)
            db.commit()
            return res

    @config.patch(f"/{c.ruta}/{{id_}}", name=f"editar_{c.ruta}")
    def editar(db: DB, id_: int, datos: Edicion):
        res = c.editar(db, id_, datos)
        db.commit()
        return res

    @config.delete(f"/{c.ruta}/{{id_}}", status_code=status.HTTP_204_NO_CONTENT, name=f"borrar_{c.ruta}")
    def borrar(db: DB, id_: int):
        c.borrar(db, id_)
        db.commit()


for _c in conf.CATALOGOS.values():
    _rutas_catalogo(_c)

OpcionEdicion = e.parcial(e.OpcionEntrada)
AsignacionEdicion = e.parcial(e.AsignacionEntrada)


@config.post("/atributos", status_code=status.HTTP_201_CREATED)
def crear_atributo(db: DB, datos: e.AtributoAlta):
    res = conf.crear_atributo(db, datos)
    db.commit()
    return res


@config.get("/entidades-referenciables")
def entidades_referenciables():
    return referencias.entidades()


@config.post("/atributos/{atributo_id}/opciones", status_code=status.HTTP_201_CREATED)
def crear_opcion(db: DB, atributo_id: int, datos: e.OpcionEntrada):
    res = conf.crear_opcion(db, atributo_id, datos)
    db.commit()
    return res


@config.patch("/atributos/{atributo_id}/opciones/{opcion_id}")
def editar_opcion(db: DB, atributo_id: int, opcion_id: int, datos: OpcionEdicion):
    res = conf.editar_opcion(db, atributo_id, opcion_id, datos)
    db.commit()
    return res


@config.delete("/atributos/{atributo_id}/opciones/{opcion_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_opcion(db: DB, atributo_id: int, opcion_id: int):
    conf.borrar_opcion(db, atributo_id, opcion_id)
    db.commit()


@config.get("/tipos-producto/{tipo_id}/esquema")
def esquema(db: DB, tipo_id: int):
    return conf.esquema(db, tipo_id)


@config.post("/tipos-producto/{tipo_id}/atributos", status_code=status.HTTP_201_CREATED)
def asignar(db: DB, tipo_id: int, datos: e.AsignacionEntrada):
    res = conf.asignar(db, tipo_id, datos)
    db.commit()
    return res


@config.patch("/tipos-producto/{tipo_id}/atributos/{atributo_id}")
def editar_asignacion(db: DB, tipo_id: int, atributo_id: int, datos: AsignacionEdicion):
    res = conf.editar_asignacion(db, tipo_id, atributo_id, datos)
    db.commit()
    return res


@config.delete("/tipos-producto/{tipo_id}/atributos/{atributo_id}")
def quitar_asignacion(db: DB, tipo_id: int, atributo_id: int):
    res = conf.quitar_asignacion(db, tipo_id, atributo_id)
    db.commit()
    return res


@config.get("/estados/{estado_id}/transiciones")
def transiciones(db: DB, estado_id: int):
    return conf.transiciones(db, estado_id)


@config.put("/estados/{estado_id}/transiciones")
def fijar_transiciones(db: DB, estado_id: int, datos: e.TransicionesEntrada):
    res = conf.fijar_transiciones(db, estado_id, datos.destinos)
    db.commit()
    return res


# ---- Productos ----------------------------------------------------------------------------
@router.get("")
def listar(db: DB, request: Request, q: str | None = None, tipo_id: int | None = None, estado_id: int | None = None,
           categoria_id: int | None = None, orden: str = "codigo", pagina: int = 1, tamano: int = 50,
           tipo: Codigos = None, estado: Codigos = None, unidad: Codigos = None):
    """Filtros por columna (uno o varios códigos): tipo, estado, unidad. Los parámetros `a.<atributo>`
    filtran por atributo: a.color=ROJO, a.peso__min=2, a.peso__max=5 kg."""
    atributos = {k[2:]: v for k, v in request.query_params.items() if k.startswith("a.")}
    return prod.listar(db, q, tipo_id, estado_id, categoria_id, atributos, orden, max(pagina, 1), min(max(tamano, 1), 200),
                       {"tipo": tipo or [], "estado": estado or [], "unidad": unidad or []})


@router.get("/valores/{columna}")
def valores(db: DB, request: Request, columna: str, buscar: str | None = None, q: str | None = None,
            categoria_id: int | None = None, tipo: Codigos = None, estado: Codigos = None,
            unidad: Codigos = None):
    """Valores de una columna (tipo, estado, unidad) con cuántos productos tiene cada uno, con los demás filtros."""
    atributos = {k[2:]: v for k, v in request.query_params.items() if k.startswith("a.")}
    return prod.valores_columna(db, columna, buscar, q=q, categoria_id=categoria_id, atributos=atributos,
                                columnas={"tipo": tipo or [], "estado": estado or [], "unidad": unidad or []})


@router.post("/asistente", status_code=status.HTTP_201_CREATED)
def crear_con_asistente(db: DB, datos: e.AsistenteEntrada, validar: bool = False):
    """Alta completa (producto, variantes, presentaciones, códigos y estado) en una sola transacción.
    Con validar=true se revisa todo y no se guarda nada (vista previa del último paso)."""
    res = asistente.ejecutar(db, datos)
    if validar:
        db.rollback()
        return {**res, "id": None, "validado": True}
    db.commit()
    return res


@router.get("/por-identificador")
def por_identificador(db: DB, valor: str, tipo_id: int | None = None):
    return comp.buscar_por_identificador(db, valor, tipo_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(db: DB, datos: e.ProductoAlta):
    res = prod.crear(db, datos)
    db.commit()
    return res


@router.get("/{producto_id}")
def ver(db: DB, producto_id: int):
    return prod.ver(db, producto_id)


@router.patch("/{producto_id}")
def editar(db: DB, producto_id: int, datos: e.ProductoEdicion):
    res = prod.editar(db, producto_id, datos)
    db.commit()
    return res


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(db: DB, producto_id: int):
    prod.eliminar(db, producto_id)
    db.commit()


@router.post("/{producto_id}/estado")
def cambiar_estado(db: DB, producto_id: int, datos: e.CambioEstado):
    res = prod.cambiar_estado(db, producto_id, datos)
    db.commit()
    return res


@router.get("/{producto_id}/faltantes")
def faltantes(db: DB, producto_id: int):
    return prod.faltantes(db, prod.obtener(db, producto_id))


# ---- Variantes ----------------------------------------------------------------------------
@router.post("/{producto_id}/variantes", status_code=status.HTTP_201_CREATED)
def crear_variante(db: DB, producto_id: int, datos: e.VarianteAlta):
    res = prod.crear_variante(db, producto_id, datos)
    db.commit()
    return res


@router.post("/{producto_id}/variantes/generar", status_code=status.HTTP_201_CREATED)
def generar_variantes(db: DB, producto_id: int, datos: e.GenerarVariantes):
    res = prod.generar_variantes(db, producto_id, datos)
    db.commit()
    return res


@router.patch("/{producto_id}/variantes/{variante_id}")
def editar_variante(db: DB, producto_id: int, variante_id: int, datos: e.VarianteEdicion):
    res = prod.editar_variante(db, producto_id, variante_id, datos)
    db.commit()
    return res


@router.delete("/{producto_id}/variantes/{variante_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_variante(db: DB, producto_id: int, variante_id: int):
    prod.eliminar_variante(db, producto_id, variante_id)
    db.commit()


# ---- Presentaciones, identificadores y relaciones -----------------------------------------
PresentacionEdicion = e.parcial(e.PresentacionEntrada)
RelacionEdicion = e.parcial(e.RelacionEntrada)


@router.post("/{producto_id}/presentaciones", status_code=status.HTTP_201_CREATED)
def crear_presentacion(db: DB, producto_id: int, datos: e.PresentacionEntrada):
    res = comp.crear_presentacion(db, producto_id, datos)
    db.commit()
    return res


@router.patch("/{producto_id}/presentaciones/{id_}")
def editar_presentacion(db: DB, producto_id: int, id_: int, datos: PresentacionEdicion):
    res = comp.editar_presentacion(db, producto_id, id_, datos)
    db.commit()
    return res


@router.delete("/{producto_id}/presentaciones/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_presentacion(db: DB, producto_id: int, id_: int):
    comp.borrar_presentacion(db, producto_id, id_)
    db.commit()


@router.post("/{producto_id}/identificadores", status_code=status.HTTP_201_CREATED)
def crear_identificador(db: DB, producto_id: int, datos: e.IdentificadorEntrada):
    res = comp.crear_identificador(db, producto_id, datos)
    db.commit()
    return res


@router.delete("/{producto_id}/identificadores/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_identificador(db: DB, producto_id: int, id_: int):
    comp.borrar_identificador(db, producto_id, id_)
    db.commit()


@router.post("/{producto_id}/relaciones", status_code=status.HTTP_201_CREATED)
def crear_relacion(db: DB, producto_id: int, datos: e.RelacionEntrada):
    res = comp.crear_relacion(db, producto_id, datos)
    db.commit()
    return res


@router.patch("/{producto_id}/relaciones/{id_}")
def editar_relacion(db: DB, producto_id: int, id_: int, datos: RelacionEdicion):
    res = comp.editar_relacion(db, producto_id, id_, datos)
    db.commit()
    return res


@router.delete("/{producto_id}/relaciones/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_relacion(db: DB, producto_id: int, id_: int):
    comp.borrar_relacion(db, producto_id, id_)
    db.commit()


@router.get("/{producto_id}/usado-en")
def usado_en(db: DB, producto_id: int):
    return comp.usado_en(db, producto_id)


# ---- Revisiones ---------------------------------------------------------------------------
@router.get("/{producto_id}/revisiones")
def revisiones(db: DB, producto_id: int):
    return comp.revisiones(db, producto_id)


@router.post("/{producto_id}/revisiones", status_code=status.HTTP_201_CREATED)
def publicar_revision(db: DB, producto_id: int, datos: e.RevisionAlta):
    res = comp.publicar_revision(db, producto_id, datos)
    db.commit()
    return res


@router.get("/{producto_id}/revisiones/{numero}")
def revision(db: DB, producto_id: int, numero: int):
    return comp.revision(db, producto_id, numero)

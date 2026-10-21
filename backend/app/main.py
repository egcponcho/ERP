"""Aplicación FastAPI: rutas de los módulos y errores como {mensaje, codigo, detalle}."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm.exc import StaleDataError

from app.core.config import settings
from app.core.errores import ErrorNegocio
from app.modelos import importar_todo
from app.modulos.productos import api as productos

importar_todo()

app = FastAPI(title="ERP", version="0.1.0")


@app.exception_handler(ErrorNegocio)
def _error_negocio(_request: Request, exc: ErrorNegocio):
    return JSONResponse({"mensaje": exc.mensaje, "codigo": exc.codigo, "detalle": exc.detalle}, status_code=exc.status)


@app.exception_handler(StaleDataError)
def _concurrencia(_request: Request, _exc: StaleDataError):
    return JSONResponse({"mensaje": "Otra persona modificó el registro mientras tanto: vuelva a cargarlo.",
                         "codigo": "conflicto", "detalle": None}, status_code=409)


@app.exception_handler(RequestValidationError)
def _validacion(_request: Request, exc: RequestValidationError):
    detalle = [{"campo": ".".join(str(x) for x in err["loc"][1:]), "mensaje": err["msg"]} for err in exc.errors()]
    return JSONResponse({"mensaje": "Revise los datos.", "codigo": "validacion", "detalle": detalle}, status_code=422)


@app.get("/api/salud")
def salud():
    return {"estado": "ok"}


# La configuración va antes: /api/productos/config/... no debe tomarse como /api/productos/{producto_id}
app.include_router(productos.config)
app.include_router(productos.router)


# ---- Interfaz ----------------------------------------------------------------------------
# Con el frontend compilado (frontend/dist), el mismo servidor sirve la interfaz: los archivos
# de /assets y, para cualquier otra ruta que no sea de la API, index.html (la app decide la vista).
DIST = settings.FRONTEND_DIST
if DIST.is_dir() and (DIST / "index.html").is_file():
    if (DIST / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{ruta:path}", include_in_schema=False)
    def interfaz(ruta: str):
        if ruta.startswith("api/"):
            return JSONResponse({"mensaje": "Ruta no encontrada.", "codigo": "no_existe", "detalle": None}, status_code=404)
        archivo = (DIST / ruta).resolve()
        if ruta and archivo.is_file() and archivo.is_relative_to(DIST.resolve()):
            return FileResponse(archivo)
        return FileResponse(DIST / "index.html", headers={"Cache-Control": "no-cache"})
else:

    @app.get("/", include_in_schema=False)
    def inicio():
        # Sin interfaz compilada, la raíz lleva a la documentación interactiva de la API
        return RedirectResponse("/docs")

"""Aplicación FastAPI: rutas de los módulos y errores como {mensaje, codigo, detalle}."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm.exc import StaleDataError

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

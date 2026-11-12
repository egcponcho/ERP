"""Búsqueda y tablero: la lista con filtros (texto, tipo, estado, categoría,
columnas y atributos), los valores de cada columna para el filtro tipo Excel
y el resumen del módulo.

Los filtros por atributo buscan en el producto y en sus variantes, y los
rangos de números con unidad comparan en la unidad de referencia
(`a.peso__max=600 G` encuentra 0.5 kg).
"""
from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.errores import invalido
from app.modulos.productos import esquema as esq
from app.modulos.productos import valores as val
from app.modulos.productos.modelos import (
    Atributo,
    EstadoProducto,
    Identificador,
    Presentacion,
    Producto,
    ProductoCategoria,
    TipoProducto,
    UnidadMedida,
    ValorAtributo,
    ValorAtributoOpcion,
    Variante,
)
from app.modulos.productos.soporte import subcategorias


def _dueno_de_valor():
    """Condición: el valor es del producto o de alguna de sus variantes."""
    return or_(ValorAtributo.producto_id == Producto.id,
               ValorAtributo.variante_id.in_(select(Variante.id).where(Variante.producto_id == Producto.id)
                                             .correlate(Producto)))


def _filtro_atributo(db: Session, codigo: str, operador: str, crudo):
    a = db.scalar(select(Atributo).where(Atributo.codigo == codigo))
    if a is None:
        raise invalido(f"El atributo {codigo} no existe.")
    base = [ValorAtributo.atributo_id == a.id, _dueno_de_valor()]
    try:
        if operador in ("min", "max"):
            if a.tipo_dato not in ("entero", "decimal", "fecha"):
                raise ValueError("solo los números y fechas admiten rangos")
            n = val.convertir(db, a, crudo, reglas={})
            if a.tipo_dato == "fecha":
                col, v = ValorAtributo.valor_fecha, n.fecha
            else:
                col = ValorAtributo.valor_numero_base if a.magnitud_id else ValorAtributo.valor_numero
                v = n.numero_base if a.magnitud_id else n.numero
            base.append(col >= v if operador == "min" else col <= v)
        elif a.tipo_dato == "opciones":
            ids = [val._opcion(a, x).id for x in str(crudo).split(",")]
            base.append(exists().where(ValorAtributoOpcion.valor_id == ValorAtributo.id,
                                       ValorAtributoOpcion.opcion_id.in_(ids)))
        elif a.tipo_dato == "texto":
            base.append(func.lower(ValorAtributo.valor_texto).contains(str(crudo).strip().lower(), autoescape=True))
        elif a.tipo_dato == "referencia":
            base.append(ValorAtributo.referencia_id == int(crudo))
        else:
            n = val.convertir(db, a, crudo, reglas={})
            if n.opcion is not None:
                base.append(ValorAtributo.opcion_id == n.opcion.id)
            elif n.booleano is not None:
                base.append(ValorAtributo.valor_booleano.is_(n.booleano))
            elif n.fecha is not None:
                base.append(ValorAtributo.valor_fecha == n.fecha)
            elif a.magnitud_id:
                base.append(ValorAtributo.valor_numero_base == n.numero_base)
            else:
                base.append(ValorAtributo.valor_numero == n.numero)
    except ValueError as ex:
        raise invalido(f"Filtro {codigo}: {ex}.") from ex
    return exists().where(and_(*base)).correlate(Producto)


ORDEN = {"codigo": Producto.codigo, "nombre": Producto.nombre, "actualizado": Producto.actualizado_en,
         "tipo": TipoProducto.nombre, "estado": EstadoProducto.orden, "unidad": UnidadMedida.codigo}
# Columnas de la tabla que se filtran por sus valores (como en Excel): columna → (columna del código, del nombre)
COLUMNAS_VALORES = {"tipo": (TipoProducto.codigo, TipoProducto.nombre), "estado": (EstadoProducto.codigo, EstadoProducto.nombre),
                    "unidad": (UnidadMedida.codigo, UnidadMedida.nombre)}


# Productos a los que les falta algo que se suele completar después del alta (resumen y filtro «pendiente»)
PENDIENTES = {
    "sin_codigos": lambda: ~exists().where(Identificador.producto_id == Producto.id),
    "sin_categorias": lambda: ~exists().where(ProductoCategoria.producto_id == Producto.id),
    "sin_presentaciones": lambda: ~exists().where(Presentacion.producto_id == Producto.id),
}


def _filtros(db: Session, q: str | None, tipo_id: int | None, estado_id: int | None, categoria_id: int | None,
             atributos: dict | None, columnas: dict[str, list[str]] | None, excepto: str | None = None,
             pendiente: str | None = None) -> list:
    """Condiciones de la lista. `columnas`: {"tipo": [códigos], "estado": […], "unidad": […]};
    `excepto` deja fuera el filtro de una columna (para calcular sus propios valores);
    `pendiente`: una clave de PENDIENTES."""
    filtros = []
    if pendiente:
        if pendiente not in PENDIENTES:
            raise invalido(f"Pendiente no válido: use {', '.join(PENDIENTES)}.")
        filtros.append(PENDIENTES[pendiente]())
    if q:
        t = q.strip().lower()
        filtros.append(or_(func.lower(Producto.codigo).contains(t, autoescape=True),
                           func.lower(Producto.nombre).contains(t, autoescape=True),
                           exists().where(Variante.producto_id == Producto.id,
                                          func.lower(Variante.codigo).contains(t, autoescape=True))))
    if tipo_id:
        filtros.append(Producto.tipo_id.in_(esq.descendientes(db, tipo_id)))
    if estado_id:
        filtros.append(Producto.estado_id == estado_id)
    if categoria_id:
        filtros.append(exists().where(ProductoCategoria.producto_id == Producto.id,
                                      ProductoCategoria.categoria_id.in_(subcategorias(db, categoria_id))))
    for columna, codigos in (columnas or {}).items():
        if columna == excepto or not codigos:
            continue
        if columna not in COLUMNAS_VALORES:
            raise invalido(f"No se puede filtrar por {columna}.")
        filtros.append(COLUMNAS_VALORES[columna][0].in_(codigos))
    for clave, crudo in (atributos or {}).items():
        codigo, _, operador = clave.partition("__")
        if operador not in ("", "min", "max"):
            raise invalido(f"Filtro {clave}: use codigo, codigo__min o codigo__max.")
        if operador and isinstance(crudo, str) and " " in crudo.strip():
            numero_txt, unidad = crudo.strip().split(None, 1)
            crudo = {"valor": numero_txt, "unidad": unidad}
        filtros.append(_filtro_atributo(db, codigo, operador, crudo))
    return filtros


def _con_columnas(consulta):
    return (consulta.join(TipoProducto, TipoProducto.id == Producto.tipo_id)
            .join(EstadoProducto, EstadoProducto.id == Producto.estado_id)
            .join(UnidadMedida, UnidadMedida.id == Producto.unidad_id))


def listar(db: Session, q: str | None = None, tipo_id: int | None = None, estado_id: int | None = None,
           categoria_id: int | None = None, atributos: dict[str, str] | None = None, orden: str = "codigo",
           pagina: int = 1, tamano: int = 50, columnas: dict[str, list[str]] | None = None,
           pendiente: str | None = None) -> dict:
    """Productos con filtros. `atributos`: {"color": "ROJO", "peso__min": "2", "peso__max": "5 kg"}
    (sobre el producto o cualquiera de sus variantes). `orden`: "campo", "-campo" o "campo:asc|desc"."""
    filtros = _filtros(db, q, tipo_id, estado_id, categoria_id, atributos, columnas, pendiente=pendiente)
    total = db.scalar(_con_columnas(select(func.count(Producto.id))).where(*filtros))
    campo, _, direccion = (orden or "codigo").partition(":")
    desc = direccion == "desc" or campo.startswith("-")
    col = ORDEN.get(campo.lstrip("-"))
    if col is None:
        raise invalido(f"Orden no válido: use {', '.join(ORDEN)}.")
    consulta = (_con_columnas(select(Producto)).where(*filtros)
                .options(selectinload(Producto.tipo), selectinload(Producto.estado), selectinload(Producto.unidad),
                         selectinload(Producto.variantes).load_only(Variante.id))
                .order_by(col.desc() if desc else col, Producto.id)
                .offset((pagina - 1) * tamano).limit(tamano))
    return {"total": total, "pagina": pagina, "tamano": tamano, "datos": [
        {"id": p.id, "codigo": p.codigo, "nombre": p.nombre, "tipo": p.tipo.codigo, "tipo_nombre": p.tipo.nombre,
         "estado": p.estado.codigo, "estado_nombre": p.estado.nombre, "operable": p.estado.operable,
         "unidad": p.unidad.codigo, "variantes": len(p.variantes), "version": p.version,
         "actualizado_en": p.actualizado_en.isoformat() if p.actualizado_en else None}
        for p in db.scalars(consulta)]}


def valores_columna(db: Session, columna: str, buscar: str | None = None, **filtros) -> list[dict]:
    """Valores de una columna con cuántos productos tiene cada uno, con los demás filtros puestos."""
    if columna not in COLUMNAS_VALORES:
        raise invalido(f"La columna {columna} no se filtra por valores.")
    codigo, nombre = COLUMNAS_VALORES[columna]
    condiciones = _filtros(db, filtros.get("q"), filtros.get("tipo_id"), filtros.get("estado_id"), filtros.get("categoria_id"),
                           filtros.get("atributos"), filtros.get("columnas"), excepto=columna,
                           pendiente=filtros.get("pendiente"))
    if buscar:
        condiciones.append(func.lower(nombre).contains(buscar.strip().lower(), autoescape=True))
    filas = db.execute(_con_columnas(select(codigo, nombre, func.count(Producto.id))).where(*condiciones)
                       .group_by(codigo, nombre).order_by(nombre))
    return [{"valor": c, "texto": n, "n": k} for c, n, k in filas]


def resumen(db: Session, recientes: int = 6) -> dict:
    """Tablero del módulo: cifras generales, productos por estado y por tipo, pendientes y lo último modificado."""
    total = db.scalar(select(func.count(Producto.id))) or 0
    por_estado = db.execute(
        select(EstadoProducto.codigo, EstadoProducto.nombre, EstadoProducto.operable, EstadoProducto.inicial,
               func.count(Producto.id))
        .outerjoin(Producto, Producto.estado_id == EstadoProducto.id)
        .where(EstadoProducto.activo.is_(True))
        .group_by(EstadoProducto.id, EstadoProducto.codigo, EstadoProducto.nombre, EstadoProducto.operable,
                  EstadoProducto.inicial, EstadoProducto.orden)
        .order_by(EstadoProducto.orden, EstadoProducto.id))
    por_tipo = db.execute(
        select(TipoProducto.codigo, TipoProducto.nombre, func.count(Producto.id))
        .join(Producto, Producto.tipo_id == TipoProducto.id)
        .group_by(TipoProducto.codigo, TipoProducto.nombre)
        .order_by(func.count(Producto.id).desc(), TipoProducto.nombre))
    estados = [{"codigo": c, "nombre": n, "operable": o, "inicial": i, "n": k} for c, n, o, i, k in por_estado]
    return {
        "total": total,
        "operables": sum(x["n"] for x in estados if x["operable"]),
        "variantes": db.scalar(select(func.count(Variante.id))) or 0,
        "presentaciones": db.scalar(select(func.count(Presentacion.id))) or 0,
        "por_estado": estados,
        "por_tipo": [{"codigo": c, "nombre": n, "n": k} for c, n, k in por_tipo],
        "pendientes": {k: db.scalar(select(func.count(Producto.id)).where(f())) or 0 for k, f in PENDIENTES.items()},
        "recientes": listar(db, orden="actualizado:desc", tamano=recientes)["datos"],
    }

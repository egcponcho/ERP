"""Productos y variantes: alta, edición, atributos, categorías, estado y búsqueda.

Todo lo que depende del rubro sale del esquema del tipo (esquema.py): qué
atributos se capturan, en qué nivel, cuáles son obligatorios y cuáles
distinguen variantes. Este servicio no conoce ningún rubro.
"""
import hashlib
import itertools
import re

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core import integridad, referencias
from app.core.errores import ErrorNegocio, conflicto, invalido, no_existe
from app.core.modelo import ahora
from app.modulos.productos import configuracion as conf
from app.modulos.productos import esquema as esq
from app.modulos.productos import esquemas as e
from app.modulos.productos import valores as val
from app.modulos.productos.modelos import (
    Atributo,
    Categoria,
    EstadoProducto,
    EstadoTransicion,
    Producto,
    ProductoCategoria,
    Taxonomia,
    TipoProducto,
    UnidadMedida,
    ValorAtributo,
    ValorAtributoOpcion,
    Variante,
)


def obtener(db: Session, producto_id: int) -> Producto:
    p = db.get(Producto, producto_id)
    if p is None:
        raise no_existe("El producto")
    return p


def _version(obj, version: int | None) -> None:
    if version is not None and version != obj.version:
        raise conflicto("Otra persona modificó el registro mientras tanto: vuelva a cargarlo.",
                        {"version_actual": obj.version})


def _tipo_activo(db: Session, tipo_id: int) -> TipoProducto:
    t = db.get(TipoProducto, tipo_id)
    if t is None:
        raise no_existe("El tipo de producto")
    if not t.activo:
        raise invalido("El tipo de producto está inactivo.")
    return t


# ---- Valores de atributos -----------------------------------------------------------------
def _fijar_valores(db: Session, filas: list[ValorAtributo], campos: list[esq.Campo], entrada: dict,
                   nuevo: bool, crear) -> dict:
    """Escribe en `filas` los valores de `entrada` para los `campos` del nivel.
    En un alta se ponen los valores por defecto que no lleguen. Devuelve
    {código: Normalizado} de lo escrito. `crear()` hace una fila nueva del dueño."""
    por_codigo = {c.codigo: c for c in campos}
    errores = [{"campo": f"atributos.{k}", "mensaje": "No es un atributo de este nivel del tipo."}
               for k in entrada if k not in por_codigo]
    actuales = {f.atributo.id: f for f in filas}
    escritos = {}
    pendientes = dict(entrada)
    if nuevo:
        for c in campos:
            if c.codigo not in pendientes and c.valor_defecto is not None:
                pendientes[c.codigo] = c.valor_defecto
    for codigo, crudo in pendientes.items():
        c = por_codigo.get(codigo)
        if c is None:
            continue
        fila = actuales.get(c.atributo.id)
        if val.vacio(crudo):
            if fila is not None:
                filas.remove(fila)
            continue
        try:
            n = val.convertir(db, c.atributo, crudo)
        except ValueError as ex:
            errores.append({"campo": f"atributos.{codigo}", "mensaje": f"{c.atributo.nombre}: {ex}."})
            continue
        if fila is None:
            fila = crear(c.atributo)
            filas.append(fila)
        val.aplicar(fila, n)
        escritos[codigo] = n
    if errores:
        raise invalido("Revise los atributos.", errores)
    return escritos


def _valores_dict(filas: list[ValorAtributo]) -> dict:
    return {f.atributo.codigo: val.leer(f) for f in filas}


# ---- Categorías ---------------------------------------------------------------------------
def _fijar_categorias(db: Session, p: Producto, ids: list[int]) -> None:
    cats = []
    for i in dict.fromkeys(ids):
        c = db.get(Categoria, i)
        if c is None:
            raise invalido("Revise las categorías.", [{"campo": "categorias", "mensaje": f"La categoría {i} no existe."}])
        if not c.activa:
            raise invalido(f"La categoría {c.nombre} está inactiva.")
        cats.append(c)
    por_tax: dict[int, list[Categoria]] = {}
    for c in cats:
        por_tax.setdefault(c.taxonomia_id, []).append(c)
    for lista in por_tax.values():
        if len(lista) > 1 and not lista[0].taxonomia.multiple:
            raise invalido(f"En {lista[0].taxonomia.nombre} el producto va en una sola categoría.")
    actuales = {pc.categoria_id: pc for pc in p.categorias}
    p.categorias = [actuales.get(c.id) or ProductoCategoria(categoria=c) for c in cats]


# ---- Completitud y estado -----------------------------------------------------------------
def faltantes(db: Session, p: Producto, e_: esq.Esquema | None = None) -> list[dict]:
    """Lo obligatorio que falta: atributos del producto, de cada variante y taxonomías."""
    e_ = e_ or esq.resolver(p.tipo)
    res = []
    tiene = {f.atributo.id for f in p.valores}
    res += [{"nivel": "producto", "atributo": c.codigo, "nombre": c.atributo.nombre}
            for c in e_.de_nivel("producto") if c.obligatorio and c.atributo.id not in tiene]
    obligatorios_var = [c for c in e_.de_nivel("variante") if c.obligatorio or c.es_eje]
    for v in p.variantes:
        tiene_v = {f.atributo.id for f in v.valores}
        res += [{"nivel": "variante", "variante": v.codigo, "atributo": c.codigo, "nombre": c.atributo.nombre}
                for c in obligatorios_var if c.atributo.id not in tiene_v]
    con_categoria = {pc.categoria.taxonomia_id for pc in p.categorias}
    for t in db.scalars(select(Taxonomia).where(Taxonomia.obligatoria.is_(True), Taxonomia.activa.is_(True))):
        if t.id not in con_categoria:
            res.append({"nivel": "categoria", "taxonomia": t.codigo, "nombre": t.nombre})
    return res


def _exigir_completo(db: Session, p: Producto, estado: EstadoProducto) -> None:
    if estado.exige_completo:
        falta = faltantes(db, p)
        if falta:
            raise invalido(f"Para pasar a {estado.nombre} el producto debe estar completo.", {"faltantes": falta})


def cambiar_estado(db: Session, producto_id: int, datos: e.CambioEstado) -> dict:
    p = obtener(db, producto_id)
    _version(p, datos.version)
    destino = db.get(EstadoProducto, datos.estado_id)
    if destino is None or not destino.activo:
        raise no_existe("El estado")
    if destino.id == p.estado_id:
        return detalle(db, p)
    permitidos = set(db.scalars(select(EstadoTransicion.destino_id).where(EstadoTransicion.origen_id == p.estado_id)))
    if permitidos and destino.id not in permitidos:
        raise conflicto(f"No se puede pasar de {p.estado.nombre} a {destino.nombre}.")
    _exigir_completo(db, p, destino)
    p.estado = destino
    integridad.guardar(db)
    return detalle(db, p)


# ---- Alta y edición -----------------------------------------------------------------------
def crear(db: Session, datos: e.ProductoAlta) -> dict:
    tipo = _tipo_activo(db, datos.tipo_id)
    e_ = esq.resolver(tipo)
    unidad_id = datos.unidad_id or e_.unidad_defecto_id
    if unidad_id is None:
        raise invalido("Indique la unidad base (el tipo no tiene una por defecto).")
    if datos.estado_id:
        estado = db.get(EstadoProducto, datos.estado_id)
        if estado is None or not estado.activo:
            raise no_existe("El estado")
    else:
        estado = db.scalar(select(EstadoProducto).where(EstadoProducto.inicial.is_(True), EstadoProducto.activo.is_(True)))
        if estado is None:
            raise invalido("Configure un estado inicial o indique el estado.")
    codigo = datos.codigo.strip() if datos.codigo else conf.siguiente_codigo(db, tipo)
    if not codigo:
        raise invalido("Indique el código (el tipo no tiene plantilla de código).")
    p = Producto(codigo=codigo, nombre=datos.nombre.strip(), descripcion=datos.descripcion, tipo=tipo,
                 unidad_id=unidad_id, estado_id=estado.id)
    integridad.verificar_referencias(db, p)
    p.estado = estado
    _fijar_valores(db, p.valores, e_.de_nivel("producto"), datos.atributos, True,
                   lambda a: ValorAtributo(atributo=a))
    _fijar_categorias(db, p, datos.categorias)
    _exigir_completo(db, p, estado)
    integridad.guardar(db, p, "Ya existe un producto con ese código.")
    return detalle(db, p)


def editar(db: Session, producto_id: int, datos: e.ProductoEdicion) -> dict:
    p = obtener(db, producto_id)
    _version(p, datos.version)
    cambios = datos.model_dump(exclude_unset=True, exclude={"version", "atributos", "categorias", "descartar_atributos"})
    if "tipo_id" in cambios and cambios["tipo_id"] != p.tipo_id:
        _cambiar_tipo(db, p, _tipo_activo(db, cambios.pop("tipo_id")), datos.descartar_atributos)
    cambios.pop("tipo_id", None)
    for k, v in cambios.items():
        if v is None and k in ("codigo", "nombre", "unidad_id"):
            raise invalido(f"El campo {k} no puede quedar vacío.")
        setattr(p, k, v.strip() if isinstance(v, str) and k != "descripcion" else v)
    integridad.verificar_referencias(db, p)
    e_ = esq.resolver(p.tipo)
    if datos.atributos is not None:
        _fijar_valores(db, p.valores, e_.de_nivel("producto"), datos.atributos, False,
                       lambda a: ValorAtributo(atributo=a))
    if datos.categorias is not None:
        _fijar_categorias(db, p, datos.categorias)
    _exigir_completo(db, p, p.estado)
    p.actualizado_en = ahora()  # nueva versión del producto aunque solo cambien filas hijas
    db.add(p)
    integridad.guardar(db, None, "Ya existe un producto con ese código.")
    return detalle(db, p)


def _cambiar_tipo(db: Session, p: Producto, nuevo: TipoProducto, descartar: bool) -> None:
    antes, despues = esq.resolver(p.tipo), esq.resolver(nuevo)
    if p.variantes and {c.atributo.id for c in antes.ejes} != {c.atributo.id for c in despues.ejes}:
        raise conflicto("El producto tiene variantes y el nuevo tipo las distingue con otros ejes.")
    nivel_p = {c.atributo.id for c in despues.de_nivel("producto")}
    nivel_v = {c.atributo.id for c in despues.de_nivel("variante")}
    sobran = [f for f in p.valores if f.atributo.id not in nivel_p]
    sobran_v = [(v, f) for v in p.variantes for f in v.valores if f.atributo.id not in nivel_v]
    if (sobran or sobran_v) and not descartar:
        raise conflicto("El nuevo tipo no tiene algunos atributos con valor. Confirme con descartar_atributos.",
                        {"atributos": sorted({f.atributo.codigo for f in sobran} | {f.atributo.codigo for _, f in sobran_v})})
    for f in sobran:
        p.valores.remove(f)
    for v, f in sobran_v:
        v.valores.remove(f)
    p.tipo = nuevo


def eliminar(db: Session, producto_id: int) -> None:
    p = obtener(db, producto_id)
    uso = referencias.en_uso(db, "producto", p.id)
    if uso:
        raise conflicto(f"El producto está en uso ({uso}): cámbielo a un estado inactivo en lugar de borrarlo.")
    integridad.borrar(db, p, "El producto")


def _uso_en_atributos(db: Session, clave: str, id_: int) -> str | None:
    a = db.scalar(select(Atributo).join(ValorAtributo, ValorAtributo.atributo_id == Atributo.id)
                  .where(Atributo.entidad_referencia == clave, ValorAtributo.referencia_id == id_).limit(1))
    return f"lo referencia el atributo {a.nombre}" if a else None


referencias.registrar("producto", Producto)
referencias.registrar_verificador(_uso_en_atributos)


# ---- Variantes ----------------------------------------------------------------------------
def _ficha(n: val.Normalizado, a: Atributo) -> str:
    """El valor de un eje como parte de un código (opción → su código)."""
    if n.opcion is not None:
        return n.opcion.codigo
    if n.numero is not None:
        return str(val.numero(n.numero)) + (n.unidad.codigo if n.unidad else "")
    if n.booleano is not None:
        return "S" if n.booleano else "N"
    if n.fecha is not None:
        return n.fecha.strftime("%Y%m%d")
    if n.referencia_id is not None:
        return str(n.referencia_id)
    return re.sub(r"[^A-Za-z0-9]+", "", (n.texto or "").upper())


def _firma(ejes: list[esq.Campo], escritos: dict[str, val.Normalizado]) -> str:
    base = "|".join(f"{c.atributo.id}={escritos[c.codigo].clave()}" for c in sorted(ejes, key=lambda c: c.atributo.id))
    return hashlib.sha256(base.encode()).hexdigest()


def _codigo_variante(p: Producto, e_: esq.Esquema, escritos: dict) -> str:
    fichas = {c.codigo: _ficha(escritos[c.codigo], c.atributo) for c in e_.ejes}
    plantilla = e_.plantilla_sku
    if not plantilla:
        return "-".join([p.codigo, *fichas.values()])
    try:
        return plantilla.format(producto=p.codigo, **fichas)
    except KeyError as ex:
        raise invalido(f"La plantilla de SKU del tipo usa {ex}, que no es un eje del tipo.") from ex


def _nombre_variante(p: Producto, e_: esq.Esquema, v: Variante) -> str:
    por_id = {f.atributo.id: f for f in v.valores}
    partes = [val.texto(por_id[c.atributo.id]) for c in e_.ejes if c.atributo.id in por_id]
    return f"{p.nombre} {' / '.join(partes)}".strip()[:250]


def _valores_de_variante(v: Variante) -> dict[str, val.Normalizado]:
    return {f.atributo.codigo: val.normalizado_de(f) for f in v.valores}


def _nueva_variante(db: Session, p: Producto, e_: esq.Esquema, datos: e.VarianteAlta) -> Variante:
    ejes = e_.ejes
    if not ejes:
        raise conflicto("El tipo de este producto no tiene atributos eje: no maneja variantes.")
    faltan = [c.codigo for c in ejes if val.vacio(datos.atributos.get(c.codigo))]
    if faltan:
        raise invalido("Indique los valores de todos los ejes.", {"faltan": faltan})
    v = Variante(activa=datos.activa, firma="")  # se une al producto solo si es válida
    escritos = _fijar_valores(db, v.valores, e_.de_nivel("variante"), datos.atributos, True,
                              lambda a: ValorAtributo(atributo=a))
    v.firma = _firma(ejes, escritos)
    if any(x.firma == v.firma for x in p.variantes if x is not v):
        raise conflicto("Ya existe una variante con esos valores.",
                        {"valores": {c.codigo: datos.atributos[c.codigo] for c in ejes}})
    v.codigo = datos.codigo.strip() if datos.codigo else _codigo_variante(p, e_, escritos)
    if db.scalar(select(exists().where(func.lower(Variante.codigo) == v.codigo.lower()))):
        raise conflicto(f"El código {v.codigo} ya es de otra variante.")
    v.nombre = datos.nombre or _nombre_variante(p, e_, v)
    v.producto = p
    return v


def crear_variante(db: Session, producto_id: int, datos: e.VarianteAlta) -> dict:
    p = obtener(db, producto_id)
    v = _nueva_variante(db, p, esq.resolver(p.tipo), datos)
    integridad.guardar(db, v, "Ya existe una variante con ese código o con esos valores.")
    return variante_dict(v)


def generar_variantes(db: Session, producto_id: int, datos: e.GenerarVariantes) -> dict:
    """Crea todas las combinaciones de los valores de los ejes; omite las que ya existen."""
    p = obtener(db, producto_id)
    e_ = esq.resolver(p.tipo)
    ejes = [c.codigo for c in e_.ejes]
    if set(datos.ejes) != set(ejes):
        raise invalido("Indique los valores de cada eje del tipo.", {"ejes": ejes})
    creadas, omitidas = [], []
    for combinacion in itertools.product(*(datos.ejes[c] for c in ejes)):
        valores_eje = dict(zip(ejes, combinacion, strict=True))
        try:
            with db.begin_nested():
                v = _nueva_variante(db, p, e_, e.VarianteAlta(atributos={**datos.atributos, **valores_eje}))
                db.add(v)
                db.flush()
            creadas.append(v)
        except ErrorNegocio as ex:  # combinación repetida o código ocupado: se informa y se sigue
            if ex.status != 409:
                raise
            omitidas.append({"valores": valores_eje, "motivo": ex.mensaje})
    return {"creadas": [variante_dict(v) for v in creadas], "omitidas": omitidas}


def _variante(db: Session, producto_id: int, variante_id: int) -> Variante:
    v = db.get(Variante, variante_id)
    if v is None or v.producto_id != producto_id:
        raise no_existe("La variante")
    return v


def editar_variante(db: Session, producto_id: int, variante_id: int, datos: e.VarianteEdicion) -> dict:
    v = _variante(db, producto_id, variante_id)
    _version(v, datos.version)
    e_ = esq.resolver(v.producto.tipo)
    if datos.atributos is not None:
        ejes = {c.codigo for c in e_.ejes}
        if any(k in ejes and val.vacio(x) for k, x in datos.atributos.items()):
            raise invalido("Los ejes de una variante no pueden quedar vacíos.")
        _fijar_valores(db, v.valores, e_.de_nivel("variante"), datos.atributos, False,
                       lambda a: ValorAtributo(atributo=a))
        if ejes & set(datos.atributos):
            v.firma = _firma(e_.ejes, _valores_de_variante(v))
    for k in ("codigo", "nombre", "activa"):
        if k in datos.model_fields_set:
            valor = getattr(datos, k)
            if valor is None and k != "nombre":
                raise invalido(f"El campo {k} no puede quedar vacío.")
            setattr(v, k, valor)
    v.actualizado_en = ahora()
    db.add(v)
    integridad.guardar(db, None, "Ya existe una variante con ese código o con esos valores.")
    return variante_dict(v)


def eliminar_variante(db: Session, producto_id: int, variante_id: int) -> None:
    integridad.borrar(db, _variante(db, producto_id, variante_id), "La variante")


def variante_dict(v: Variante) -> dict:
    return {"id": v.id, "codigo": v.codigo, "nombre": v.nombre, "activa": v.activa, "version": v.version,
            "atributos": _valores_dict(v.valores)}


# ---- Lectura ------------------------------------------------------------------------------
def detalle(db: Session, p: Producto) -> dict:
    from app.modulos.productos import complementos

    e_ = esq.resolver(p.tipo)
    en_esquema = {c.atributo.id for c in e_.de_nivel("producto")}
    return {
        "id": p.id, "codigo": p.codigo, "nombre": p.nombre, "descripcion": p.descripcion,
        "tipo": {"id": p.tipo.id, "codigo": p.tipo.codigo, "nombre": p.tipo.nombre},
        "unidad": {"id": p.unidad.id, "codigo": p.unidad.codigo, "nombre": p.unidad.nombre},
        "estado": {"id": p.estado.id, "codigo": p.estado.codigo, "nombre": p.estado.nombre, "operable": p.estado.operable},
        "atributos": _valores_dict([f for f in p.valores if f.atributo.id in en_esquema]),
        # Valores de atributos que el tipo ya no tiene (se ocultaron o se quitaron): se conservan, no se pierden
        "atributos_fuera_de_esquema": _valores_dict([f for f in p.valores if f.atributo.id not in en_esquema]),
        "categorias": [{"id": pc.categoria.id, "codigo": pc.categoria.codigo, "nombre": pc.categoria.nombre,
                        "taxonomia": pc.categoria.taxonomia.codigo} for pc in p.categorias],
        "variantes": [variante_dict(v) for v in p.variantes],
        **complementos.de_producto(p),
        "faltantes": faltantes(db, p, e_),
        "revision": p.revision,
        "version": p.version,
        "creado_en": p.creado_en.isoformat() if p.creado_en else None,
        "actualizado_en": p.actualizado_en.isoformat() if p.actualizado_en else None,
    }


def ver(db: Session, producto_id: int) -> dict:
    return detalle(db, obtener(db, producto_id))


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


def _filtros(db: Session, q: str | None, tipo_id: int | None, estado_id: int | None, categoria_id: int | None,
             atributos: dict | None, columnas: dict[str, list[str]] | None, excepto: str | None = None) -> list:
    """Condiciones de la lista. `columnas`: {"tipo": [códigos], "estado": […], "unidad": […]};
    `excepto` deja fuera el filtro de una columna (para calcular sus propios valores)."""
    filtros = []
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
                                      ProductoCategoria.categoria_id.in_(_subcategorias(db, categoria_id))))
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
           pagina: int = 1, tamano: int = 50, columnas: dict[str, list[str]] | None = None) -> dict:
    """Productos con filtros. `atributos`: {"color": "ROJO", "peso__min": "2", "peso__max": "5 kg"}
    (sobre el producto o cualquiera de sus variantes). `orden`: "campo", "-campo" o "campo:asc|desc"."""
    filtros = _filtros(db, q, tipo_id, estado_id, categoria_id, atributos, columnas)
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
                           filtros.get("atributos"), filtros.get("columnas"), excepto=columna)
    if buscar:
        condiciones.append(func.lower(nombre).contains(buscar.strip().lower(), autoescape=True))
    filas = db.execute(_con_columnas(select(codigo, nombre, func.count(Producto.id))).where(*condiciones)
                       .group_by(codigo, nombre).order_by(nombre))
    return [{"valor": c, "texto": n, "n": k} for c, n, k in filas]


def _subcategorias(db: Session, categoria_id: int) -> set[int]:
    hijos: dict[int | None, list[int]] = {}
    for i, padre in db.execute(select(Categoria.id, Categoria.padre_id)):
        hijos.setdefault(padre, []).append(i)
    res, pendientes = set(), [categoria_id]
    while pendientes:
        i = pendientes.pop()
        if i not in res:
            res.add(i)
            pendientes.extend(hijos.get(i, []))
    return res


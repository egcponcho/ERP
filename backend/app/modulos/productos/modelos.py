"""Productos: un modelo único para cualquier rubro (docs/PRODUCTOS.md).

El producto solo guarda lo universal: código, nombre, tipo, unidad base y
estado. Todo lo particular de un rubro (talla, color, concentración, voltaje,
vida útil…) es un atributo definido en la configuración y asignado a un tipo
de producto. Nada de esto está escrito en el código.

Configuración (la administra cada organización):
    Magnitud ─< UnidadMedida
    GrupoAtributo ─< Atributo ─< AtributoOpcion
    TipoProducto (árbol) ─< TipoProductoAtributo >─ Atributo
    Taxonomia ─< Categoria (árbol)
    EstadoProducto ─< EstadoTransicion
    TipoIdentificador, TipoRelacion

Datos:
    Producto ─< Variante
    Producto / Variante ─< ValorAtributo ─< ValorAtributoOpcion
    Producto ─< ProductoCategoria >─ Categoria
    Producto ─< Presentacion
    Producto ─< Identificador (del producto, de una variante o de una presentación)
    Producto ─< RelacionProducto >─ Producto (componentes, sustitutos, accesorios…)
    Producto ─< RevisionProducto (copias inmutables con vigencia)
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.modelo import Base, ConTiempos, ConVersion
from app.core.organizacion import DeOrganizacion

# Primitivas del motor (no son reglas de negocio): cómo se guarda y valida un valor
TIPOS_DATO = ("texto", "entero", "decimal", "booleano", "fecha", "opcion", "opciones", "referencia")
# En qué nivel se captura un atributo de un tipo de producto
NIVELES = ("producto", "variante")

Cantidad = Numeric(28, 10)


# ---- Unidades -----------------------------------------------------------------------------
class Magnitud(DeOrganizacion, ConTiempos, Base):
    """Lo que se mide (masa, volumen, longitud, cantidad…). Las unidades de una
    misma magnitud se convierten entre sí por su factor."""

    __tablename__ = "magnitudes"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(100))
    activa: Mapped[bool] = mapped_column(default=True)

    unidades: Mapped[list[UnidadMedida]] = relationship(back_populates="magnitud", order_by="UnidadMedida.codigo")


class UnidadMedida(DeOrganizacion, ConTiempos, Base):
    """Unidad de una magnitud: `factor` dice cuántas unidades de referencia de su
    magnitud contiene (kg = 1, g = 0.001). `decimales` = 0 la hace contable."""

    __tablename__ = "unidades_medida"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),
                      CheckConstraint("factor > 0", name="factor_positivo"),
                      CheckConstraint("decimales BETWEEN 0 AND 10", name="decimales"))
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20))
    nombre: Mapped[str] = mapped_column(String(100))
    simbolo: Mapped[str | None] = mapped_column(String(20))
    magnitud_id: Mapped[int] = mapped_column(ForeignKey("magnitudes.id"), index=True)
    factor: Mapped[Decimal] = mapped_column(Cantidad, default=1)
    decimales: Mapped[int] = mapped_column(Integer, default=0)
    activa: Mapped[bool] = mapped_column(default=True)

    magnitud: Mapped[Magnitud] = relationship(back_populates="unidades")


# ---- Atributos ----------------------------------------------------------------------------
class GrupoAtributo(DeOrganizacion, ConTiempos, Base):
    """Sección en la que se muestran los atributos (Dimensiones, Seguridad…)."""

    __tablename__ = "grupos_atributo"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(100))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    activo: Mapped[bool] = mapped_column(default=True)


class Atributo(DeOrganizacion, ConTiempos, Base):
    """Definición de una característica que puede tener un producto o una variante.

    `reglas` según el tipo de dato: texto {longitud_min, longitud_max, patron};
    entero/decimal {minimo, maximo, decimales} (en la unidad por defecto si tiene
    magnitud); fecha {minimo, maximo};
    opciones {minimo, maximo} (cuántas elegir). Un número con `magnitud_id` se
    captura con su unidad (5 kg, 500 g) y se compara en la unidad de referencia.
    Un atributo `referencia` apunta a un registro de otra entidad registrada
    (core/referencias.py): así se enlazan los maestros que se vayan agregando.
    """

    __tablename__ = "atributos"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40))
    nombre: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str | None] = mapped_column(String(500))
    tipo_dato: Mapped[str] = mapped_column(String(15))
    magnitud_id: Mapped[int | None] = mapped_column(ForeignKey("magnitudes.id"), index=True)
    unidad_defecto_id: Mapped[int | None] = mapped_column(ForeignKey("unidades_medida.id"))
    entidad_referencia: Mapped[str | None] = mapped_column(String(40))
    reglas: Mapped[dict] = mapped_column(JSON, default=dict)
    grupo_id: Mapped[int | None] = mapped_column(ForeignKey("grupos_atributo.id"), index=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)
    activo: Mapped[bool] = mapped_column(default=True)

    magnitud: Mapped[Magnitud | None] = relationship()
    unidad_defecto: Mapped[UnidadMedida | None] = relationship()
    grupo: Mapped[GrupoAtributo | None] = relationship()
    opciones: Mapped[list[AtributoOpcion]] = relationship(
        back_populates="atributo", cascade="all, delete-orphan", order_by="(AtributoOpcion.orden, AtributoOpcion.id)")


class AtributoOpcion(DeOrganizacion, ConTiempos, Base):
    """Valor permitido de un atributo de tipo opcion u opciones."""

    __tablename__ = "atributo_opciones"
    __table_args__ = (UniqueConstraint("atributo_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    atributo_id: Mapped[int] = mapped_column(ForeignKey("atributos.id", ondelete="CASCADE"), index=True)
    codigo: Mapped[str] = mapped_column(String(40))
    nombre: Mapped[str] = mapped_column(String(100))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    activa: Mapped[bool] = mapped_column(default=True)

    atributo: Mapped[Atributo] = relationship(back_populates="opciones")


# ---- Tipos de producto --------------------------------------------------------------------
class TipoProducto(DeOrganizacion, ConTiempos, Base):
    """Plantilla de un rubro (Calzado, Químico, Alimento…). Forma un árbol: un
    subtipo hereda los atributos, la unidad y las plantillas de sus antecesores
    y puede agregar, cambiar u ocultar atributos.

    `plantilla_codigo`: cómo se numeran sus productos ("CAL-{seq:05}").
    `plantilla_sku`: cómo se arma el código de sus variantes
    ("{producto}-{color}-{talla}", con los códigos de los atributos eje).
    """

    __tablename__ = "tipos_producto"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str | None] = mapped_column(String(500))
    padre_id: Mapped[int | None] = mapped_column(ForeignKey("tipos_producto.id"), index=True)
    unidad_defecto_id: Mapped[int | None] = mapped_column(ForeignKey("unidades_medida.id"))
    plantilla_codigo: Mapped[str | None] = mapped_column(String(60))
    siguiente_numero: Mapped[int] = mapped_column(Integer, default=1)
    plantilla_sku: Mapped[str | None] = mapped_column(String(120))
    activo: Mapped[bool] = mapped_column(default=True)

    padre: Mapped[TipoProducto | None] = relationship(remote_side=lambda: TipoProducto.id)
    unidad_defecto: Mapped[UnidadMedida | None] = relationship()
    asignaciones: Mapped[list[TipoProductoAtributo]] = relationship(
        back_populates="tipo", cascade="all, delete-orphan", order_by="(TipoProductoAtributo.orden, TipoProductoAtributo.id)")


class TipoProductoAtributo(DeOrganizacion, ConTiempos, Base):
    """Un atributo dentro de un tipo: en qué nivel se captura, si es obligatorio,
    si distingue variantes (eje) y su valor por defecto. Un subtipo puede
    volver a asignar el mismo atributo para cambiarlo, u ocultarlo."""

    __tablename__ = "tipo_producto_atributos"
    __table_args__ = (UniqueConstraint("tipo_id", "atributo_id"),
                      CheckConstraint("nivel IN ('producto', 'variante')", name="nivel"),
                      CheckConstraint("NOT es_eje OR nivel = 'variante'", name="eje_en_variante"))
    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_id: Mapped[int] = mapped_column(ForeignKey("tipos_producto.id", ondelete="CASCADE"), index=True)
    atributo_id: Mapped[int] = mapped_column(ForeignKey("atributos.id"), index=True)
    nivel: Mapped[str] = mapped_column(String(10), default="producto")
    es_eje: Mapped[bool] = mapped_column(default=False)
    obligatorio: Mapped[bool] = mapped_column(default=False)
    oculto: Mapped[bool] = mapped_column(default=False)
    valor_defecto: Mapped[object | None] = mapped_column(JSON)
    orden: Mapped[int] = mapped_column(Integer, default=0)

    tipo: Mapped[TipoProducto] = relationship(back_populates="asignaciones")
    atributo: Mapped[Atributo] = relationship(lazy="joined")


# ---- Clasificaciones ----------------------------------------------------------------------
class Taxonomia(DeOrganizacion, ConTiempos, Base):
    """Una forma de agrupar productos (Línea comercial, Familia contable,
    Departamento…). Cada una es un árbol de categorías independiente."""

    __tablename__ = "taxonomias"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(100))
    multiple: Mapped[bool] = mapped_column(default=False)  # un producto puede estar en varias categorías
    obligatoria: Mapped[bool] = mapped_column(default=False)  # se exige para un estado que pide ficha completa
    activa: Mapped[bool] = mapped_column(default=True)


class Categoria(DeOrganizacion, ConTiempos, Base):
    __tablename__ = "categorias"
    __table_args__ = (UniqueConstraint("taxonomia_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    taxonomia_id: Mapped[int] = mapped_column(ForeignKey("taxonomias.id"), index=True)
    padre_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(100))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    activa: Mapped[bool] = mapped_column(default=True)

    taxonomia: Mapped[Taxonomia] = relationship()
    padre: Mapped[Categoria | None] = relationship(remote_side=lambda: Categoria.id)


# ---- Ciclo de vida ------------------------------------------------------------------------
class EstadoProducto(DeOrganizacion, ConTiempos, Base):
    """Estado del ciclo de vida (Borrador, Activo, Descontinuado…).
    `exige_completo`: para entrar, el producto debe tener todos sus obligatorios.
    `operable`: los demás módulos (compras, ventas, inventario) pueden usarlo."""

    __tablename__ = "estados_producto"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(100))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    inicial: Mapped[bool] = mapped_column(default=False)
    exige_completo: Mapped[bool] = mapped_column(default=False)
    operable: Mapped[bool] = mapped_column(default=False)
    activo: Mapped[bool] = mapped_column(default=True)


class EstadoTransicion(DeOrganizacion, ConTiempos, Base):
    """Paso permitido entre estados. Un estado sin transiciones configuradas
    puede pasar a cualquier otro."""

    __tablename__ = "estado_transiciones"
    __table_args__ = (UniqueConstraint("origen_id", "destino_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    origen_id: Mapped[int] = mapped_column(ForeignKey("estados_producto.id", ondelete="CASCADE"), index=True)
    destino_id: Mapped[int] = mapped_column(ForeignKey("estados_producto.id", ondelete="CASCADE"), index=True)


# ---- Identificadores y relaciones ---------------------------------------------------------
class TipoIdentificador(DeOrganizacion, ConTiempos, Base):
    """Clase de código alterno (EAN-13, UPC, código del proveedor, CAS…).
    `patron`: expresión regular que debe cumplir el valor."""

    __tablename__ = "tipos_identificador"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(100))
    patron: Mapped[str | None] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(default=True)


class TipoRelacion(DeOrganizacion, ConTiempos, Base):
    """Clase de vínculo entre productos (Componente, Sustituto, Accesorio,
    Materia prima…). `con_cantidad`: el vínculo lleva cantidad y unidad
    (lista de materiales, kits)."""

    __tablename__ = "tipos_relacion"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(100))
    nombre_inverso: Mapped[str | None] = mapped_column(String(100))
    con_cantidad: Mapped[bool] = mapped_column(default=False)
    activo: Mapped[bool] = mapped_column(default=True)


# ---- Datos --------------------------------------------------------------------------------
class Producto(DeOrganizacion, ConTiempos, ConVersion, Base):
    __tablename__ = "productos"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60))
    nombre: Mapped[str] = mapped_column(String(200), index=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    tipo_id: Mapped[int] = mapped_column(ForeignKey("tipos_producto.id"), index=True)
    unidad_id: Mapped[int] = mapped_column(ForeignKey("unidades_medida.id"))
    estado_id: Mapped[int] = mapped_column(ForeignKey("estados_producto.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer, default=0)  # última revisión publicada

    tipo: Mapped[TipoProducto] = relationship()
    unidad: Mapped[UnidadMedida] = relationship()
    estado: Mapped[EstadoProducto] = relationship()
    valores: Mapped[list[ValorAtributo]] = relationship(
        primaryjoin="ValorAtributo.producto_id == Producto.id", cascade="all, delete-orphan", back_populates="producto")
    variantes: Mapped[list[Variante]] = relationship(
        back_populates="producto", cascade="all, delete-orphan", order_by="Variante.id")
    categorias: Mapped[list[ProductoCategoria]] = relationship(back_populates="producto", cascade="all, delete-orphan")
    presentaciones: Mapped[list[Presentacion]] = relationship(
        back_populates="producto", cascade="all, delete-orphan", order_by="Presentacion.id")
    identificadores: Mapped[list[Identificador]] = relationship(
        back_populates="producto", cascade="all, delete-orphan", order_by="Identificador.id")
    relaciones: Mapped[list[RelacionProducto]] = relationship(
        foreign_keys="RelacionProducto.origen_id", back_populates="origen", cascade="all, delete-orphan",
        order_by="(RelacionProducto.tipo_id, RelacionProducto.orden, RelacionProducto.id)")
    revisiones: Mapped[list[RevisionProducto]] = relationship(
        back_populates="producto", cascade="all, delete-orphan", order_by="RevisionProducto.numero")


class Variante(DeOrganizacion, ConTiempos, ConVersion, Base):
    """Versión comercializable de un producto (un SKU), distinguida por los
    valores de sus atributos eje. `firma` resume esa combinación: no puede
    haber dos variantes iguales del mismo producto."""

    __tablename__ = "variantes"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"), UniqueConstraint("producto_id", "firma"))
    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), index=True)
    codigo: Mapped[str] = mapped_column(String(80))
    nombre: Mapped[str | None] = mapped_column(String(250))
    firma: Mapped[str] = mapped_column(String(64))
    activa: Mapped[bool] = mapped_column(default=True)

    producto: Mapped[Producto] = relationship(back_populates="variantes")
    valores: Mapped[list[ValorAtributo]] = relationship(
        primaryjoin="ValorAtributo.variante_id == Variante.id", cascade="all, delete-orphan", back_populates="variante")


class ValorAtributo(DeOrganizacion, ConTiempos, Base):
    """Valor de un atributo en un producto o en una variante (exactamente uno).
    Cada tipo de dato usa su columna; los números con magnitud guardan además
    el valor en la unidad de referencia para comparar y filtrar."""

    __tablename__ = "valores_atributo"
    __table_args__ = (
        UniqueConstraint("producto_id", "atributo_id"),
        UniqueConstraint("variante_id", "atributo_id"),
        CheckConstraint("(producto_id IS NULL) <> (variante_id IS NULL)", name="un_dueno"),
        Index("ix_valores_atributo_texto", "atributo_id", "valor_texto"),
        Index("ix_valores_atributo_numero", "atributo_id", "valor_numero_base"),
        Index("ix_valores_atributo_opcion", "atributo_id", "opcion_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int | None] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), index=True)
    variante_id: Mapped[int | None] = mapped_column(ForeignKey("variantes.id", ondelete="CASCADE"), index=True)
    atributo_id: Mapped[int] = mapped_column(ForeignKey("atributos.id"), index=True)
    valor_texto: Mapped[str | None] = mapped_column(String(1000))
    valor_numero: Mapped[Decimal | None] = mapped_column(Cantidad)
    valor_numero_base: Mapped[Decimal | None] = mapped_column(Cantidad)
    unidad_id: Mapped[int | None] = mapped_column(ForeignKey("unidades_medida.id"))
    valor_booleano: Mapped[bool | None] = mapped_column()
    valor_fecha: Mapped[date | None] = mapped_column(Date)
    opcion_id: Mapped[int | None] = mapped_column(ForeignKey("atributo_opciones.id"))
    referencia_id: Mapped[int | None] = mapped_column(Integer)

    producto: Mapped[Producto | None] = relationship(back_populates="valores", foreign_keys=[producto_id])
    variante: Mapped[Variante | None] = relationship(back_populates="valores", foreign_keys=[variante_id])
    atributo: Mapped[Atributo] = relationship(lazy="joined")
    unidad: Mapped[UnidadMedida | None] = relationship(lazy="joined")
    opcion: Mapped[AtributoOpcion | None] = relationship(lazy="joined")
    seleccion: Mapped[list[ValorAtributoOpcion]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", back_populates="valor")


class ValorAtributoOpcion(DeOrganizacion, Base):
    """Cada opción elegida de un atributo de selección múltiple."""

    __tablename__ = "valor_atributo_opciones"
    valor_id: Mapped[int] = mapped_column(ForeignKey("valores_atributo.id", ondelete="CASCADE"), primary_key=True)
    opcion_id: Mapped[int] = mapped_column(ForeignKey("atributo_opciones.id"), primary_key=True, index=True)

    valor: Mapped[ValorAtributo] = relationship(back_populates="seleccion")
    opcion: Mapped[AtributoOpcion] = relationship(lazy="joined")


class ProductoCategoria(DeOrganizacion, Base):
    __tablename__ = "producto_categorias"
    __table_args__ = (UniqueConstraint("producto_id", "categoria_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), index=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"), index=True)

    producto: Mapped[Producto] = relationship(back_populates="categorias")
    categoria: Mapped[Categoria] = relationship(lazy="joined")


class Presentacion(DeOrganizacion, ConTiempos, Base):
    """Forma en que se empaca o se comercia el producto (caja de 12, tambor de
    200 L, bulto de 50 kg): `cantidad` en la unidad base del producto. Puede
    ser de una variante en particular."""

    __tablename__ = "presentaciones"
    __table_args__ = (UniqueConstraint("producto_id", "codigo"), CheckConstraint("cantidad > 0", name="cantidad_positiva"))
    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), index=True)
    variante_id: Mapped[int | None] = mapped_column(ForeignKey("variantes.id", ondelete="CASCADE"), index=True)
    codigo: Mapped[str] = mapped_column(String(40))
    nombre: Mapped[str] = mapped_column(String(100))
    unidad_id: Mapped[int] = mapped_column(ForeignKey("unidades_medida.id"))
    cantidad: Mapped[Decimal] = mapped_column(Cantidad)
    activa: Mapped[bool] = mapped_column(default=True)

    producto: Mapped[Producto] = relationship(back_populates="presentaciones")
    unidad: Mapped[UnidadMedida] = relationship(lazy="joined")


class Identificador(DeOrganizacion, ConTiempos, Base):
    """Código alterno del producto, de una de sus variantes o de una de sus
    presentaciones. Un mismo código no se repite dentro de su tipo."""

    __tablename__ = "identificadores"
    __table_args__ = (UniqueConstraint("organizacion_id", "tipo_id", "valor"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), index=True)
    variante_id: Mapped[int | None] = mapped_column(ForeignKey("variantes.id", ondelete="CASCADE"), index=True)
    presentacion_id: Mapped[int | None] = mapped_column(ForeignKey("presentaciones.id", ondelete="CASCADE"), index=True)
    tipo_id: Mapped[int] = mapped_column(ForeignKey("tipos_identificador.id"), index=True)
    valor: Mapped[str] = mapped_column(String(100))

    producto: Mapped[Producto] = relationship(back_populates="identificadores")
    tipo: Mapped[TipoIdentificador] = relationship(lazy="joined")


class RelacionProducto(DeOrganizacion, ConTiempos, Base):
    """Vínculo dirigido entre dos productos (o con una variante del destino)."""

    __tablename__ = "relaciones_producto"
    __table_args__ = (UniqueConstraint("tipo_id", "origen_id", "destino_id", "destino_variante_id"),
                      CheckConstraint("origen_id <> destino_id", name="no_a_si_mismo"),
                      CheckConstraint("cantidad IS NULL OR cantidad > 0", name="cantidad_positiva"))
    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_id: Mapped[int] = mapped_column(ForeignKey("tipos_relacion.id"), index=True)
    origen_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), index=True)
    # Sin cascada: un producto que es destino de un vínculo (componente de otro) no se borra en silencio
    destino_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)
    destino_variante_id: Mapped[int | None] = mapped_column(ForeignKey("variantes.id"))
    cantidad: Mapped[Decimal | None] = mapped_column(Cantidad)
    unidad_id: Mapped[int | None] = mapped_column(ForeignKey("unidades_medida.id"))
    orden: Mapped[int] = mapped_column(Integer, default=0)

    tipo: Mapped[TipoRelacion] = relationship(lazy="joined")
    origen: Mapped[Producto] = relationship(foreign_keys=[origen_id], back_populates="relaciones")
    destino: Mapped[Producto] = relationship(foreign_keys=[destino_id], lazy="joined")
    unidad: Mapped[UnidadMedida | None] = relationship(lazy="joined")


class RevisionProducto(DeOrganizacion, Base):
    """Copia inmutable de la ficha completa (datos, atributos, categorías,
    variantes, presentaciones…) al publicarla, con su vigencia."""

    __tablename__ = "revisiones_producto"
    __table_args__ = (UniqueConstraint("producto_id", "numero"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), index=True)
    numero: Mapped[int] = mapped_column(Integer)
    motivo: Mapped[str | None] = mapped_column(String(500))
    vigente_desde: Mapped[datetime] = mapped_column(DateTime)
    vigente_hasta: Mapped[datetime | None] = mapped_column(DateTime)
    datos: Mapped[dict] = mapped_column(JSON)

    producto: Mapped[Producto] = relationship(back_populates="revisiones")

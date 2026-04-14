from sqlalchemy import Column, Integer, String, Numeric, Boolean, Date, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    comision_por_item = Column(Numeric(10, 2), default=0.50)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    aliases = relationship("ClienteAlias", back_populates="cliente", cascade="all, delete-orphan")
    pedido_clientes = relationship("PedidoCliente", back_populates="cliente")


class ClienteAlias(Base):
    __tablename__ = "cliente_aliases"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    alias = Column(String(100), nullable=False, unique=True)

    cliente = relationship("Cliente", back_populates="aliases")


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, nullable=True)
    fecha = Column(Date, nullable=False)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    pedido_clientes = relationship("PedidoCliente", back_populates="pedido", cascade="all, delete-orphan")


class PedidoCliente(Base):
    __tablename__ = "pedido_clientes"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    estado_pago = Column(String(20), default="PENDIENTE")  # PAGADO / PENDIENTE

    __table_args__ = (UniqueConstraint("pedido_id", "cliente_id", name="uq_pedido_cliente"),)

    pedido = relationship("Pedido", back_populates="pedido_clientes")
    cliente = relationship("Cliente", back_populates="pedido_clientes")
    items = relationship("Item", back_populates="pedido_cliente", cascade="all, delete-orphan")
    pagos = relationship("Pago", back_populates="pedido_cliente", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    pedido_cliente_id = Column(Integer, ForeignKey("pedido_clientes.id", ondelete="CASCADE"), nullable=False)
    numero = Column(Integer, nullable=True)
    link = Column(Text, nullable=True)
    articulo = Column(String(200), nullable=True)
    imagen_url = Column(Text, nullable=True)
    llegado = Column(Boolean, default=False)
    precio = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    pedido_cliente = relationship("PedidoCliente", back_populates="items")


class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    pedido_cliente_id = Column(Integer, ForeignKey("pedido_clientes.id", ondelete="CASCADE"), nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    tipo = Column(String(50), default="transferencia")  # transferencia / efectivo / otro
    comprobante_url = Column(Text, nullable=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    notas = Column(Text, nullable=True)

    pedido_cliente = relationship("PedidoCliente", back_populates="pagos")

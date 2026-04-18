from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# ── Alias ──────────────────────────────────────────────
class AliasBase(BaseModel):
    alias: str

class AliasOut(AliasBase):
    id: int
    model_config = {"from_attributes": True}


# ── Cliente ────────────────────────────────────────────
class ClienteCreate(BaseModel):
    nombre: str
    comision_por_item: Optional[Decimal] = Decimal("0.50")
    aliases: Optional[List[str]] = []

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    comision_por_item: Optional[Decimal] = None

class ClienteOut(BaseModel):
    id: int
    nombre: str
    comision_por_item: Decimal
    aliases: List[AliasOut] = []
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Item ───────────────────────────────────────────────
class ItemCreate(BaseModel):
    numero: Optional[int] = None
    link: Optional[str] = None
    articulo: Optional[str] = None
    precio: Optional[Decimal] = None
    llegado: Optional[bool] = False

class ItemUpdate(BaseModel):
    numero: Optional[int] = None
    link: Optional[str] = None
    articulo: Optional[str] = None
    precio: Optional[Decimal] = None
    llegado: Optional[bool] = None
    imagen_url: Optional[str] = None

class ItemOut(BaseModel):
    id: int
    pedido_cliente_id: int
    numero: Optional[int]
    link: Optional[str]
    articulo: Optional[str]
    imagen_url: Optional[str]
    llegado: bool
    precio: Optional[Decimal]
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Pago ───────────────────────────────────────────────
class PagoCreate(BaseModel):
    monto: Decimal
    tipo: Optional[str] = "transferencia"
    notas: Optional[str] = None

class PagoOut(BaseModel):
    id: int
    pedido_cliente_id: int
    monto: Decimal
    tipo: str
    comprobante_url: Optional[str]
    fecha: datetime
    notas: Optional[str]
    model_config = {"from_attributes": True}


# ── PedidoCliente ──────────────────────────────────────
class PedidoClienteComisionUpdate(BaseModel):
    comision_por_item: Decimal

class PedidoClienteOut(BaseModel):
    id: int
    cliente_id: int
    cliente_nombre: str
    cliente_comision: Decimal
    estado_pago: str
    token_publico: Optional[str] = None
    items: List[ItemOut] = []
    pagos: List[PagoOut] = []
    # calculados
    subtotal: Decimal = Decimal("0")
    comision: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    total_pagado: Decimal = Decimal("0")
    saldo: Decimal = Decimal("0")
    model_config = {"from_attributes": True}


# ── Pedido ─────────────────────────────────────────────
class PedidoCreate(BaseModel):
    numero: Optional[int] = None
    fecha: date
    notas: Optional[str] = None

class PedidoUpdate(BaseModel):
    numero: Optional[int] = None
    fecha: Optional[date] = None
    notas: Optional[str] = None

class PedidoOut(BaseModel):
    id: int
    numero: Optional[int]
    fecha: date
    notas: Optional[str]
    created_at: datetime
    clientes: List[PedidoClienteOut] = []
    model_config = {"from_attributes": True}

class PedidoListOut(BaseModel):
    id: int
    numero: Optional[int]
    fecha: date
    notas: Optional[str]
    total_clientes: int = 0
    total_pendientes: int = 0
    clientes_nombres: List[str] = []
    total_por_cobrar: Decimal = Decimal("0")
    total_cobrado: Decimal = Decimal("0")
    model_config = {"from_attributes": True}

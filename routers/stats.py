from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, contains_eager, selectinload

from database import get_db
from models import Cliente, Item, Pago, Pedido, PedidoCliente

router = APIRouter(prefix="/stats", tags=["stats"])


def _calcular_saldo(pc: PedidoCliente) -> Decimal:
    comision_unit = Decimal(str(pc.comision_por_item if pc.comision_por_item is not None else pc.cliente.comision_por_item))
    items_llegados = [i for i in pc.items if i.llegado and i.deleted_at is None]
    subtotal = sum(Decimal(str(i.precio or 0)) for i in items_llegados)
    comision = Decimal(len(items_llegados)) * comision_unit
    total = subtotal + comision
    total_pagado = sum(Decimal(str(p.monto)) for p in pc.pagos if p.deleted_at is None)
    return total - total_pagado


@router.get("/dashboard")
def dashboard_stats(db: Session = Depends(get_db)):
    total_pedidos = db.query(func.count(Pedido.id)).scalar() or 0
    total_clientes = db.query(func.count(Cliente.id)).scalar() or 0
    total_cobrado = Decimal(str(db.query(func.sum(Pago.monto)).scalar() or 0))

    pedido_clientes = (
        db.query(PedidoCliente)
        .options(
            selectinload(PedidoCliente.cliente),
            selectinload(PedidoCliente.items),
            selectinload(PedidoCliente.pagos),
        )
        .filter(PedidoCliente.deleted_at.is_(None))
        .all()
    )

    total_pendiente = Decimal("0")
    clientes_con_deuda: set[int] = set()

    for pc in pedido_clientes:
        saldo = _calcular_saldo(pc)
        if saldo > 0:
            total_pendiente += saldo
            clientes_con_deuda.add(pc.cliente_id)

    return {
        "total_pedidos": total_pedidos,
        "total_clientes": total_clientes,
        "clientes_con_deuda": len(clientes_con_deuda),
        "total_cobrado": float(total_cobrado),
        "total_pendiente": float(total_pendiente),
    }


@router.get("/clientes/{cliente_id}")
def historial_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    pedido_clientes = (
        db.query(PedidoCliente)
        .join(PedidoCliente.pedido)
        .options(
            contains_eager(PedidoCliente.pedido),
            selectinload(PedidoCliente.items),
            selectinload(PedidoCliente.pagos),
        )
        .filter(PedidoCliente.cliente_id == cliente_id, PedidoCliente.deleted_at.is_(None))
        .order_by(Pedido.fecha.desc())
        .all()
    )

    total_gastado = Decimal("0")
    total_pagado_global = Decimal("0")
    total_pendiente_global = Decimal("0")
    historial = []

    for pc in pedido_clientes:
        comision_unit = Decimal(str(pc.comision_por_item if pc.comision_por_item is not None else cliente.comision_por_item))
        items_llegados = [i for i in pc.items if i.llegado and i.deleted_at is None]
        subtotal = sum(Decimal(str(i.precio or 0)) for i in items_llegados)
        comision = Decimal(len(items_llegados)) * comision_unit
        total = subtotal + comision
        pagado = sum(Decimal(str(p.monto)) for p in pc.pagos if p.deleted_at is None)
        saldo = total - pagado

        total_gastado += total
        total_pagado_global += pagado
        total_pendiente_global += max(saldo, Decimal("0"))

        historial.append({
            "pedido_cliente_id": pc.id,
            "pedido_id": pc.pedido.id,
            "pedido_numero": pc.pedido.numero,
            "fecha": str(pc.pedido.fecha),
            "total_items": len(pc.items),
            "items_llegados": len(items_llegados),
            "subtotal": float(subtotal),
            "comision": float(comision),
            "total": float(total),
            "pagado": float(pagado),
            "saldo": float(saldo),
            "estado_pago": "PAGADO" if saldo <= 0 else "PENDIENTE",
        })

    return {
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "comision_por_item": float(cliente.comision_por_item),
        },
        "resumen": {
            "total_pedidos": len(historial),
            "total_gastado": float(total_gastado),
            "total_pagado": float(total_pagado_global),
            "total_pendiente": float(total_pendiente_global),
        },
        "historial": historial,
    }

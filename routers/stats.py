from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, contains_eager, selectinload

from database import get_db
from models import Cliente, Item, Pago, Pedido, PedidoCliente
from utils.facturacion import items_a_facturar

router = APIRouter(prefix="/stats", tags=["stats"])


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
    total_general = Decimal("0")
    total_items = 0
    clientes_con_deuda: set[int] = set()

    for pc in pedido_clientes:
        comision_unit = Decimal(str(pc.comision_por_item if pc.comision_por_item is not None else pc.cliente.comision_por_item))
        items_activos = [i for i in pc.items if i.deleted_at is None]
        items_facturables = items_a_facturar(items_activos)
        subtotal = sum(Decimal(str(i.precio or 0)) for i in items_facturables)
        comision = Decimal(len(items_facturables)) * comision_unit
        total = subtotal + comision
        total_pagado_pc = sum(Decimal(str(p.monto)) for p in pc.pagos if p.deleted_at is None)
        saldo = total - total_pagado_pc

        total_items += len(items_activos)
        total_general += total

        if saldo > 0:
            total_pendiente += saldo
            clientes_con_deuda.add(pc.cliente_id)

    return {
        "total_pedidos": total_pedidos,
        "total_clientes": total_clientes,
        "clientes_con_deuda": len(clientes_con_deuda),
        "total_cobrado": float(total_cobrado),
        "total_pendiente": float(total_pendiente),
        "total_items": total_items,
        "total_general": float(total_general),
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
    transacciones = []

    for pc in pedido_clientes:
        comision_unit = Decimal(str(pc.comision_por_item if pc.comision_por_item is not None else cliente.comision_por_item))
        items_facturables = items_a_facturar([i for i in pc.items if i.deleted_at is None])
        subtotal = sum(Decimal(str(i.precio or 0)) for i in items_facturables)
        comision = Decimal(len(items_facturables)) * comision_unit
        total = subtotal + comision
        pagos_activos = [p for p in pc.pagos if p.deleted_at is None]
        pagado = sum(Decimal(str(p.monto)) for p in pagos_activos)
        saldo = total - pagado

        total_gastado += total
        total_pagado_global += pagado
        total_pendiente_global += max(saldo, Decimal("0"))

        for p in pagos_activos:
            transacciones.append({
                "pago_id": p.id,
                "pedido_cliente_id": pc.id,
                "pedido_id": pc.pedido.id,
                "pedido_numero": pc.pedido.numero,
                "fecha": p.fecha.isoformat() if p.fecha else None,
                "monto": float(p.monto),
                "tipo": p.tipo,
                "notas": p.notas,
                "comprobante_url": p.comprobante_url,
            })

        historial.append({
            "pedido_cliente_id": pc.id,
            "pedido_id": pc.pedido.id,
            "pedido_numero": pc.pedido.numero,
            "fecha": str(pc.pedido.fecha),
            "total_items": len(pc.items),
            "items_activos": len(items_facturables),
            "subtotal": float(subtotal),
            "comision": float(comision),
            "total": float(total),
            "pagado": float(pagado),
            "saldo": float(saldo),
            "estado_pago": "PAGADO" if saldo <= 0 else "PENDIENTE",
        })

    # Linea de tiempo: todos los pagos de todos los pedidos. El acumulado se
    # calcula en orden cronologico (total pagado por el cliente hasta ese pago),
    # pero se devuelve con los mas recientes primero para mostrarlos arriba.
    transacciones.sort(key=lambda t: (t["fecha"] or "", t["pago_id"]))
    acumulado = Decimal("0")
    for t in transacciones:
        acumulado += Decimal(str(t["monto"]))
        t["acumulado_pagado"] = float(acumulado)
    transacciones.reverse()

    return {
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "comision_por_item": float(cliente.comision_por_item),
            "token_publico": cliente.token_publico,
        },
        "resumen": {
            "total_pedidos": len(historial),
            "total_gastado": float(total_gastado),
            "total_pagado": float(total_pagado_global),
            "total_pendiente": float(total_pendiente_global),
            "total_transacciones": len(transacciones),
        },
        "historial": historial,
        "transacciones": transacciones,
    }

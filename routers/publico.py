from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import PedidoCliente

router = APIRouter(prefix="/public", tags=["publico"])


@router.get("/factura/{token}")
def factura_publica(token: str, db: Session = Depends(get_db)):
    pc = (
        db.query(PedidoCliente)
        .options(
            selectinload(PedidoCliente.cliente),
            selectinload(PedidoCliente.pedido),
            selectinload(PedidoCliente.items),
            selectinload(PedidoCliente.pagos),
        )
        .filter(PedidoCliente.token_publico == token)
        .first()
    )

    if not pc:
        raise HTTPException(status_code=404, detail="Enlace no valido")

    comision_unit = Decimal(str(pc.cliente.comision_por_item))
    items_llegados = [i for i in pc.items if i.llegado]
    subtotal = sum(Decimal(str(i.precio or 0)) for i in items_llegados)
    comision = Decimal(len(items_llegados)) * comision_unit
    total = subtotal + comision
    total_pagado = sum(Decimal(str(p.monto)) for p in pc.pagos)
    saldo = total - total_pagado

    return {
        "pedido_numero": pc.pedido.numero,
        "pedido_id": pc.pedido.id,
        "fecha": str(pc.pedido.fecha),
        "cliente_nombre": pc.cliente.nombre,
        "cliente_comision": float(comision_unit),
        "items": [
            {
                "id": i.id,
                "articulo": i.articulo,
                "link": i.link,
                "imagen_url": i.imagen_url,
                "precio": float(i.precio or 0),
                "llegado": i.llegado,
                "numero": i.numero,
            }
            for i in pc.items
        ],
        "pagos": [
            {
                "id": p.id,
                "monto": float(p.monto),
                "tipo": p.tipo,
                "notas": p.notas,
                "fecha": p.fecha.isoformat(),
            }
            for p in pc.pagos
        ],
        "subtotal": float(subtotal),
        "comision": float(comision),
        "total": float(total),
        "total_pagado": float(total_pagado),
        "saldo": float(saldo),
    }

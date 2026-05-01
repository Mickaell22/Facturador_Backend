import html as html_lib
import json
import os
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, contains_eager, selectinload

from database import get_db
from models import Cliente, Pedido, PedidoCliente

router = APIRouter(prefix="/public", tags=["publico"])

_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


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

    comision_unit = Decimal(str(pc.comision_por_item if pc.comision_por_item is not None else pc.cliente.comision_por_item))
    items_activos = [i for i in pc.items if i.deleted_at is None]
    pagos_activos = [p for p in pc.pagos if p.deleted_at is None]
    items_llegados = [i for i in items_activos if i.llegado]
    subtotal = sum(Decimal(str(i.precio or 0)) for i in items_llegados)
    comision = Decimal(len(items_llegados)) * comision_unit
    total = subtotal + comision
    total_pagado = sum(Decimal(str(p.monto)) for p in pagos_activos)
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
            for i in items_activos
        ],
        "pagos": [
            {
                "id": p.id,
                "monto": float(p.monto),
                "tipo": p.tipo,
                "notas": p.notas,
                "fecha": p.fecha.isoformat(),
            }
            for p in pagos_activos
        ],
        "subtotal": float(subtotal),
        "comision": float(comision),
        "total": float(total),
        "total_pagado": float(total_pagado),
        "saldo": float(saldo),
    }


@router.get("/cliente/{token}")
def historial_cliente_publico(token: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.token_publico == token).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Enlace no valido")

    pedido_clientes = (
        db.query(PedidoCliente)
        .join(PedidoCliente.pedido)
        .options(
            contains_eager(PedidoCliente.pedido),
            selectinload(PedidoCliente.items),
            selectinload(PedidoCliente.pagos),
        )
        .filter(PedidoCliente.cliente_id == cliente.id, PedidoCliente.deleted_at.is_(None))
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
            "pedido_numero": pc.pedido.numero,
            "pedido_id": pc.pedido.id,
            "fecha": str(pc.pedido.fecha),
            "total_items": len([i for i in pc.items if i.deleted_at is None]),
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
            "nombre": cliente.nombre,
        },
        "resumen": {
            "total_pedidos": len(historial),
            "total_gastado": float(total_gastado),
            "total_pagado": float(total_pagado_global),
            "total_pendiente": float(total_pendiente_global),
        },
        "historial": historial,
    }


@router.get("/p/{token}", response_class=HTMLResponse)
def og_preview(token: str, db: Session = Depends(get_db)):
    """Sirve HTML con OG meta tags para previews en WhatsApp/Telegram y redirige al SPA."""
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

    comision_unit = Decimal(str(pc.comision_por_item if pc.comision_por_item is not None else pc.cliente.comision_por_item))
    items_activos = [i for i in pc.items if i.deleted_at is None]
    pagos_activos = [p for p in pc.pagos if p.deleted_at is None]
    items_llegados = [i for i in items_activos if i.llegado]
    subtotal = sum(Decimal(str(i.precio or 0)) for i in items_llegados)
    comision = Decimal(len(items_llegados)) * comision_unit
    total = subtotal + comision
    total_pagado = sum(Decimal(str(p.monto)) for p in pagos_activos)
    saldo = total - total_pagado

    nombre = html_lib.escape(pc.cliente.nombre)
    pedido_num = pc.pedido.numero or pc.pedido.id
    estado_txt = "Pagado" if saldo <= 0 else f"Saldo pendiente: ${float(saldo):.2f}"
    descripcion = html_lib.escape(
        f"Pedido #{pedido_num} — {len(items_activos)} articulo{'s' if len(items_activos) != 1 else ''} "
        f"— Total: ${float(total):.2f} — {estado_txt}"
    )
    destino_url = f"{_FRONTEND_URL}/p/{token}"
    destino_attr = html_lib.escape(destino_url, quote=True)
    destino_js = json.dumps(destino_url)

    content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Pedido de {nombre}</title>
  <meta name="description" content="{descripcion}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{destino_attr}" />
  <meta property="og:title" content="Pedido de {nombre}" />
  <meta property="og:description" content="{descripcion}" />
  <meta property="og:site_name" content="Facturador" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="Pedido de {nombre}" />
  <meta name="twitter:description" content="{descripcion}" />
  <meta http-equiv="refresh" content="0;url={destino_attr}" />
  <script>window.location.replace({destino_js});</script>
</head>
<body>
  <p>Redirigiendo... <a href="{destino_attr}">Haz click aqui si no redirige automaticamente</a></p>
</body>
</html>"""

    return HTMLResponse(content=content)

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from decimal import Decimal

from database import get_db
from models import Pedido, PedidoCliente, Cliente, Item, Pago
from schemas import PedidoCreate, PedidoUpdate, PedidoOut, PedidoListOut, PedidoClienteOut, PedidoClienteComisionUpdate

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


def calcular_totales(pc: PedidoCliente) -> PedidoClienteOut:
    comision_unit = Decimal(str(pc.comision_por_item if pc.comision_por_item is not None else pc.cliente.comision_por_item))
    items_activos = [i for i in pc.items if i.deleted_at is None]
    items_llegados = [i for i in items_activos if i.llegado]
    pagos_activos = [p for p in pc.pagos if p.deleted_at is None]

    subtotal = sum(Decimal(str(i.precio or 0)) for i in items_llegados)
    comision = Decimal(len(items_llegados)) * comision_unit
    total = subtotal + comision
    total_pagado = sum(Decimal(str(p.monto)) for p in pagos_activos)
    saldo = total - total_pagado

    estado_pago = "PAGADO" if saldo <= 0 else "PENDIENTE"

    return PedidoClienteOut(
        id=pc.id,
        cliente_id=pc.cliente_id,
        cliente_nombre=pc.cliente.nombre,
        cliente_comision=comision_unit,
        estado_pago=estado_pago,
        token_publico=pc.token_publico,
        items=items_activos,
        pagos=pagos_activos,
        subtotal=subtotal,
        comision=comision,
        total=total,
        total_pagado=total_pagado,
        saldo=saldo,
    )


@router.get("", response_model=List[PedidoListOut])
def listar_pedidos(db: Session = Depends(get_db)):
    pedidos = (
        db.query(Pedido)
        .options(
            joinedload(Pedido.pedido_clientes).joinedload(PedidoCliente.cliente),
            joinedload(Pedido.pedido_clientes).joinedload(PedidoCliente.items),
            joinedload(Pedido.pedido_clientes).joinedload(PedidoCliente.pagos),
        )
        .filter(Pedido.deleted_at.is_(None))
        .order_by(Pedido.fecha.desc())
        .all()
    )
    result = []
    for p in pedidos:
        pcs_activos = [pc for pc in p.pedido_clientes if pc.deleted_at is None]
        total_clientes = len(pcs_activos)
        clientes_nombres = [pc.cliente.nombre for pc in pcs_activos if pc.cliente]

        total_pendientes = 0
        total_por_cobrar = Decimal("0")
        total_cobrado = Decimal("0")
        for pc in pcs_activos:
            totales = calcular_totales(pc)
            if totales.saldo > 0:
                total_pendientes += 1
                total_por_cobrar += totales.saldo
            total_cobrado += totales.total_pagado

        result.append(PedidoListOut(
            id=p.id,
            numero=p.numero,
            fecha=p.fecha,
            notas=p.notas,
            total_clientes=total_clientes,
            total_pendientes=total_pendientes,
            clientes_nombres=clientes_nombres,
            total_por_cobrar=total_por_cobrar,
            total_cobrado=total_cobrado,
        ))
    return result


@router.get("/{pedido_id}", response_model=PedidoOut)
def obtener_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = (
        db.query(Pedido)
        .options(
            joinedload(Pedido.pedido_clientes).joinedload(PedidoCliente.cliente),
            joinedload(Pedido.pedido_clientes).joinedload(PedidoCliente.items),
            joinedload(Pedido.pedido_clientes).joinedload(PedidoCliente.pagos),
        )
        .filter(Pedido.id == pedido_id, Pedido.deleted_at.is_(None))
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    pcs_activos = [pc for pc in pedido.pedido_clientes if pc.deleted_at is None]
    clientes_out = [calcular_totales(pc) for pc in pcs_activos]

    return PedidoOut(
        id=pedido.id,
        numero=pedido.numero,
        fecha=pedido.fecha,
        notas=pedido.notas,
        created_at=pedido.created_at,
        clientes=clientes_out,
    )


@router.post("", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def crear_pedido(data: PedidoCreate, db: Session = Depends(get_db)):
    pedido = Pedido(numero=data.numero, fecha=data.fecha, notas=data.notas)
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return PedidoOut(
        id=pedido.id,
        numero=pedido.numero,
        fecha=pedido.fecha,
        notas=pedido.notas,
        created_at=pedido.created_at,
        clientes=[],
    )


@router.put("/{pedido_id}", response_model=PedidoOut)
def actualizar_pedido(pedido_id: int, data: PedidoUpdate, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id, Pedido.deleted_at.is_(None)
    ).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    if data.numero is not None:
        pedido.numero = data.numero
    if data.fecha is not None:
        pedido.fecha = data.fecha
    if data.notas is not None:
        pedido.notas = data.notas

    db.commit()
    db.refresh(pedido)
    return obtener_pedido(pedido_id, db)


@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id, Pedido.deleted_at.is_(None)
    ).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    now = datetime.now(timezone.utc)
    pedido.deleted_at = now
    # Marcar en cascada pedido_clientes, items y pagos
    for pc in pedido.pedido_clientes:
        if pc.deleted_at is None:
            pc.deleted_at = now
            for item in pc.items:
                if item.deleted_at is None:
                    item.deleted_at = now
            for pago in pc.pagos:
                if pago.deleted_at is None:
                    pago.deleted_at = now
    db.commit()


@router.post("/{pedido_id}/clientes/{cliente_id}", response_model=PedidoClienteOut, status_code=status.HTTP_201_CREATED)
def agregar_cliente_a_pedido(pedido_id: int, cliente_id: int, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id, Pedido.deleted_at.is_(None)
    ).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    cliente = db.query(Cliente).filter(
        Cliente.id == cliente_id, Cliente.deleted_at.is_(None)
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    existente = db.query(PedidoCliente).filter(
        PedidoCliente.pedido_id == pedido_id,
        PedidoCliente.cliente_id == cliente_id,
        PedidoCliente.deleted_at.is_(None),
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="El cliente ya está en este pedido")

    pc = PedidoCliente(
        pedido_id=pedido_id,
        cliente_id=cliente_id,
        comision_por_item=cliente.comision_por_item,
    )
    db.add(pc)
    db.commit()
    db.refresh(pc)
    return calcular_totales(pc)


@router.patch("/{pedido_id}/clientes/{cliente_id}/comision", response_model=PedidoClienteOut)
def actualizar_comision(pedido_id: int, cliente_id: int, data: PedidoClienteComisionUpdate, db: Session = Depends(get_db)):
    pc = db.query(PedidoCliente).filter(
        PedidoCliente.pedido_id == pedido_id,
        PedidoCliente.cliente_id == cliente_id,
        PedidoCliente.deleted_at.is_(None),
    ).first()
    if not pc:
        raise HTTPException(status_code=404, detail="Relacion no encontrada")
    pc.comision_por_item = data.comision_por_item
    db.commit()
    db.refresh(pc)
    return calcular_totales(pc)


@router.delete("/{pedido_id}/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_cliente_de_pedido(pedido_id: int, cliente_id: int, db: Session = Depends(get_db)):
    pc = db.query(PedidoCliente).filter(
        PedidoCliente.pedido_id == pedido_id,
        PedidoCliente.cliente_id == cliente_id,
        PedidoCliente.deleted_at.is_(None),
    ).first()
    if not pc:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    now = datetime.now(timezone.utc)
    pc.deleted_at = now
    for item in pc.items:
        if item.deleted_at is None:
            item.deleted_at = now
    for pago in pc.pagos:
        if pago.deleted_at is None:
            pago.deleted_at = now
    db.commit()

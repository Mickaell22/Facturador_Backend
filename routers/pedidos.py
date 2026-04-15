from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from decimal import Decimal
from database import get_db
from models import Pedido, PedidoCliente, Cliente
from schemas import PedidoCreate, PedidoUpdate, PedidoOut, PedidoListOut, PedidoClienteOut

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


def calcular_totales(pc: PedidoCliente) -> PedidoClienteOut:
    comision_unit = Decimal(str(pc.cliente.comision_por_item))
    items_llegados = [i for i in pc.items if i.llegado]

    subtotal = sum(Decimal(str(i.precio or 0)) for i in items_llegados)
    comision = Decimal(len(items_llegados)) * comision_unit
    total = subtotal + comision
    total_pagado = sum(Decimal(str(p.monto)) for p in pc.pagos)
    saldo = total - total_pagado

    estado_pago = "PAGADO" if saldo <= 0 else "PENDIENTE"

    return PedidoClienteOut(
        id=pc.id,
        cliente_id=pc.cliente_id,
        cliente_nombre=pc.cliente.nombre,
        cliente_comision=comision_unit,
        estado_pago=estado_pago,
        items=pc.items,
        pagos=pc.pagos,
        subtotal=subtotal,
        comision=comision,
        total=total,
        total_pagado=total_pagado,
        saldo=saldo,
    )


@router.get("/", response_model=List[PedidoListOut])
def listar_pedidos(db: Session = Depends(get_db)):
    pedidos = (
        db.query(Pedido)
        .options(joinedload(Pedido.pedido_clientes).joinedload(PedidoCliente.cliente))
        .order_by(Pedido.fecha.desc())
        .all()
    )
    result = []
    for p in pedidos:
        total_clientes = len(p.pedido_clientes)
        total_pendientes = sum(
            1 for pc in p.pedido_clientes if pc.estado_pago == "PENDIENTE"
        )
        clientes_nombres = [pc.cliente.nombre for pc in p.pedido_clientes if pc.cliente]
        result.append(PedidoListOut(
            id=p.id,
            numero=p.numero,
            fecha=p.fecha,
            notas=p.notas,
            total_clientes=total_clientes,
            total_pendientes=total_pendientes,
            clientes_nombres=clientes_nombres,
        ))
    return result


@router.get("/{pedido_id}", response_model=PedidoOut)
def obtener_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = (
        db.query(Pedido)
        .options(
            joinedload(Pedido.pedido_clientes)
            .joinedload(PedidoCliente.cliente),
            joinedload(Pedido.pedido_clientes)
            .joinedload(PedidoCliente.items),
            joinedload(Pedido.pedido_clientes)
            .joinedload(PedidoCliente.pagos),
        )
        .filter(Pedido.id == pedido_id)
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    clientes_out = [calcular_totales(pc) for pc in pedido.pedido_clientes]

    return PedidoOut(
        id=pedido.id,
        numero=pedido.numero,
        fecha=pedido.fecha,
        notas=pedido.notas,
        created_at=pedido.created_at,
        clientes=clientes_out,
    )


@router.post("/", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
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
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
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
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    db.delete(pedido)
    db.commit()


@router.post("/{pedido_id}/clientes/{cliente_id}", response_model=PedidoClienteOut, status_code=status.HTTP_201_CREATED)
def agregar_cliente_a_pedido(pedido_id: int, cliente_id: int, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    existente = db.query(PedidoCliente).filter(
        PedidoCliente.pedido_id == pedido_id,
        PedidoCliente.cliente_id == cliente_id
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="El cliente ya está en este pedido")

    pc = PedidoCliente(pedido_id=pedido_id, cliente_id=cliente_id)
    db.add(pc)
    db.commit()
    db.refresh(pc)
    return calcular_totales(pc)


@router.delete("/{pedido_id}/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_cliente_de_pedido(pedido_id: int, cliente_id: int, db: Session = Depends(get_db)):
    pc = db.query(PedidoCliente).filter(
        PedidoCliente.pedido_id == pedido_id,
        PedidoCliente.cliente_id == cliente_id
    ).first()
    if not pc:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    db.delete(pc)
    db.commit()

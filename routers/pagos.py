from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Pago, PedidoCliente
from schemas import PagoCreate, PagoOut
from utils.cloudinary_helper import upload_image

router = APIRouter(prefix="/pedido-clientes", tags=["pagos"])


def _get_pc(pc_id: int, db: Session) -> PedidoCliente:
    pc = db.query(PedidoCliente).filter(
        PedidoCliente.id == pc_id, PedidoCliente.deleted_at.is_(None)
    ).first()
    if not pc:
        raise HTTPException(status_code=404, detail="Relación pedido-cliente no encontrada")
    return pc


@router.get("/{pc_id}/pagos", response_model=List[PagoOut])
def listar_pagos(pc_id: int, db: Session = Depends(get_db)):
    _get_pc(pc_id, db)
    return (
        db.query(Pago)
        .filter(Pago.pedido_cliente_id == pc_id, Pago.deleted_at.is_(None))
        .order_by(Pago.fecha)
        .all()
    )


@router.post("/{pc_id}/pagos", response_model=PagoOut, status_code=status.HTTP_201_CREATED)
def registrar_pago(pc_id: int, data: PagoCreate, db: Session = Depends(get_db)):
    _get_pc(pc_id, db)
    pago = Pago(pedido_cliente_id=pc_id, **data.model_dump())
    db.add(pago)
    db.commit()
    db.refresh(pago)
    return pago


@router.delete("/{pc_id}/pagos/{pago_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pago(pc_id: int, pago_id: int, db: Session = Depends(get_db)):
    pago = db.query(Pago).filter(
        Pago.id == pago_id,
        Pago.pedido_cliente_id == pc_id,
        Pago.deleted_at.is_(None),
    ).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    pago.deleted_at = datetime.now(timezone.utc)
    db.commit()


@router.post("/{pc_id}/pagos/{pago_id}/comprobante", response_model=PagoOut)
async def subir_comprobante(
    pc_id: int,
    pago_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    pago = db.query(Pago).filter(
        Pago.id == pago_id,
        Pago.pedido_cliente_id == pc_id,
        Pago.deleted_at.is_(None),
    ).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    content = await file.read()
    url = upload_image(content, folder="facturador/comprobantes")
    pago.comprobante_url = url
    db.commit()
    db.refresh(pago)
    return pago

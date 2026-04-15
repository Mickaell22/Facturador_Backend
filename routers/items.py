from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Item, PedidoCliente
from schemas import ItemCreate, ItemUpdate, ItemOut
from utils.cloudinary_helper import upload_image

router = APIRouter(prefix="/pedido-clientes", tags=["items"])


def _get_pc(pc_id: int, db: Session) -> PedidoCliente:
    pc = db.query(PedidoCliente).filter(
        PedidoCliente.id == pc_id, PedidoCliente.deleted_at.is_(None)
    ).first()
    if not pc:
        raise HTTPException(status_code=404, detail="Relación pedido-cliente no encontrada")
    return pc


@router.get("/{pc_id}/items", response_model=List[ItemOut])
def listar_items(pc_id: int, db: Session = Depends(get_db)):
    _get_pc(pc_id, db)
    return (
        db.query(Item)
        .filter(Item.pedido_cliente_id == pc_id, Item.deleted_at.is_(None))
        .order_by(Item.numero)
        .all()
    )


@router.post("/{pc_id}/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def crear_item(pc_id: int, data: ItemCreate, db: Session = Depends(get_db)):
    _get_pc(pc_id, db)
    item = Item(pedido_cliente_id=pc_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{pc_id}/items/{item_id}", response_model=ItemOut)
def actualizar_item(pc_id: int, item_id: int, data: ItemUpdate, db: Session = Depends(get_db)):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.pedido_cliente_id == pc_id,
        Item.deleted_at.is_(None),
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{pc_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_item(pc_id: int, item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.pedido_cliente_id == pc_id,
        Item.deleted_at.is_(None),
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    item.deleted_at = datetime.now(timezone.utc)
    db.commit()


@router.post("/{pc_id}/items/{item_id}/imagen", response_model=ItemOut)
async def subir_imagen_item(
    pc_id: int,
    item_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.pedido_cliente_id == pc_id,
        Item.deleted_at.is_(None),
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    content = await file.read()
    url = upload_image(content, folder="facturador/productos")
    item.imagen_url = url
    db.commit()
    db.refresh(item)
    return item

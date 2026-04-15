from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Cliente, ClienteAlias, PedidoCliente
from schemas import ClienteCreate, ClienteUpdate, ClienteOut, AliasBase

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("/", response_model=List[ClienteOut])
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(Cliente).order_by(Cliente.nombre).all()


@router.get("/{cliente_id}", response_model=ClienteOut)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.post("/", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def crear_cliente(data: ClienteCreate, db: Session = Depends(get_db)):
    existente = db.query(Cliente).filter(Cliente.nombre == data.nombre).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un cliente con ese nombre")

    cliente = Cliente(nombre=data.nombre, comision_por_item=data.comision_por_item)
    db.add(cliente)
    db.flush()

    for alias_str in (data.aliases or []):
        alias_str = alias_str.strip()
        if alias_str:
            db.add(ClienteAlias(cliente_id=cliente.id, alias=alias_str))

    db.commit()
    db.refresh(cliente)
    return cliente


@router.put("/{cliente_id}", response_model=ClienteOut)
def actualizar_cliente(cliente_id: int, data: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if data.nombre is not None:
        cliente.nombre = data.nombre
    if data.comision_por_item is not None:
        cliente.comision_por_item = data.comision_por_item

    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    total_pedidos = (
        db.query(PedidoCliente)
        .filter(PedidoCliente.cliente_id == cliente_id)
        .count()
    )
    if total_pedidos > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar: {cliente.nombre} tiene {total_pedidos} pedido(s) asociado(s). Elimina primero los pedidos.",
        )

    db.delete(cliente)
    db.commit()


@router.post("/{cliente_id}/aliases", response_model=ClienteOut)
def agregar_alias(cliente_id: int, data: AliasBase, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    existente = db.query(ClienteAlias).filter(ClienteAlias.alias == data.alias).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ese alias ya está en uso")

    db.add(ClienteAlias(cliente_id=cliente_id, alias=data.alias))
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}/aliases/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_alias(cliente_id: int, alias_id: int, db: Session = Depends(get_db)):
    alias = db.query(ClienteAlias).filter(
        ClienteAlias.id == alias_id,
        ClienteAlias.cliente_id == cliente_id
    ).first()
    if not alias:
        raise HTTPException(status_code=404, detail="Alias no encontrado")
    db.delete(alias)
    db.commit()

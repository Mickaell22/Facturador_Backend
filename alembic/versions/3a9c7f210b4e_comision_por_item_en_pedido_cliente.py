"""comision_por_item_en_pedido_cliente

Revision ID: 3a9c7f210b4e
Revises: 1e87eaf58567
Create Date: 2026-04-18 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '3a9c7f210b4e'
down_revision: Union[str, None] = '1e87eaf58567'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pedido_clientes', sa.Column('comision_por_item', sa.Numeric(10, 2), nullable=True))
    # Backfill: copiar comision actual del cliente a cada pedido_cliente existente
    op.execute("""
        UPDATE pedido_clientes pc
        SET comision_por_item = c.comision_por_item
        FROM clientes c
        WHERE pc.cliente_id = c.id
          AND pc.comision_por_item IS NULL
    """)


def downgrade() -> None:
    op.drop_column('pedido_clientes', 'comision_por_item')

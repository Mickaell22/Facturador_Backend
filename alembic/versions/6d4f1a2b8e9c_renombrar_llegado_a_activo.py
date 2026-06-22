"""renombrar items.llegado a items.activo

Cambia la semantica de "llego/no llego" a "activo/inactivo": un item se factura
cuando esta activo. Los items existentes quedan todos activos para no alterar los
totales de pedidos previos.

Revision ID: 6d4f1a2b8e9c
Revises: 5c3d9e2f0a1b
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '6d4f1a2b8e9c'
down_revision: Union[str, None] = '5c3d9e2f0a1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('items', 'llegado', new_column_name='activo')
    op.execute("UPDATE items SET activo = TRUE")
    op.alter_column(
        'items', 'activo',
        server_default=sa.text('true'),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'items', 'activo',
        server_default=sa.text('false'),
        nullable=True,
    )
    op.alter_column('items', 'activo', new_column_name='llegado')

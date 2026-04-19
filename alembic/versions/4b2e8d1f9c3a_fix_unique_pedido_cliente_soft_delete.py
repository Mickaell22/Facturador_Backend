"""fix unique constraint pedido_cliente para soft delete

Revision ID: 4b2e8d1f9c3a
Revises: 3a9c7f210b4e
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op


revision: str = '4b2e8d1f9c3a'
down_revision: Union[str, None] = '3a9c7f210b4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('uq_pedido_cliente', 'pedido_clientes', type_='unique')
    op.execute("""
        CREATE UNIQUE INDEX uq_pedido_cliente_activo
        ON pedido_clientes (pedido_id, cliente_id)
        WHERE deleted_at IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX uq_pedido_cliente_activo")
    op.create_unique_constraint('uq_pedido_cliente', 'pedido_clientes', ['pedido_id', 'cliente_id'])

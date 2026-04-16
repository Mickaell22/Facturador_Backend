"""estado_inicial

Revision ID: 18fdc49838dd
Revises:
Create Date: 2026-04-15 16:04:54.906090

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '18fdc49838dd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'clientes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('comision_por_item', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )
    op.create_index('ix_clientes_id', 'clientes', ['id'])

    op.create_table(
        'cliente_aliases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('alias', sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alias'),
    )
    op.create_index('ix_cliente_aliases_id', 'cliente_aliases', ['id'])

    op.create_table(
        'pedidos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('numero', sa.Integer(), nullable=True),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pedidos_id', 'pedidos', ['id'])

    op.create_table(
        'pedido_clientes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('estado_pago', sa.String(20), nullable=True),
        sa.Column('token_publico', sa.String(36), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pedido_id', 'cliente_id', name='uq_pedido_cliente'),
        sa.UniqueConstraint('token_publico'),
    )
    op.create_index('ix_pedido_clientes_id', 'pedido_clientes', ['id'])

    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_cliente_id', sa.Integer(), nullable=False),
        sa.Column('numero', sa.Integer(), nullable=True),
        sa.Column('link', sa.Text(), nullable=True),
        sa.Column('articulo', sa.String(200), nullable=True),
        sa.Column('imagen_url', sa.Text(), nullable=True),
        sa.Column('llegado', sa.Boolean(), nullable=True),
        sa.Column('precio', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pedido_cliente_id'], ['pedido_clientes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_items_id', 'items', ['id'])

    op.create_table(
        'pagos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_cliente_id', sa.Integer(), nullable=False),
        sa.Column('monto', sa.Numeric(10, 2), nullable=False),
        sa.Column('tipo', sa.String(50), nullable=True),
        sa.Column('comprobante_url', sa.Text(), nullable=True),
        sa.Column('fecha', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pedido_cliente_id'], ['pedido_clientes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pagos_id', 'pagos', ['id'])


def downgrade() -> None:
    op.drop_table('pagos')
    op.drop_table('items')
    op.drop_table('pedido_clientes')
    op.drop_table('pedidos')
    op.drop_table('cliente_aliases')
    op.drop_table('clientes')

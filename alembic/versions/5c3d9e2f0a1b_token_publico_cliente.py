"""token_publico en clientes para historial publico

Revision ID: 5c3d9e2f0a1b
Revises: 4b2e8d1f9c3a
Create Date: 2026-04-29 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '5c3d9e2f0a1b'
down_revision: Union[str, None] = '4b2e8d1f9c3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clientes', sa.Column('token_publico', sa.String(36), nullable=True))
    op.execute("UPDATE clientes SET token_publico = gen_random_uuid()::text WHERE token_publico IS NULL")
    op.alter_column('clientes', 'token_publico', nullable=False)
    op.create_unique_constraint('uq_clientes_token_publico', 'clientes', ['token_publico'])


def downgrade() -> None:
    op.drop_constraint('uq_clientes_token_publico', 'clientes', type_='unique')
    op.drop_column('clientes', 'token_publico')

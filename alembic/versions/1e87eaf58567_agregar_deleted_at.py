"""agregar_deleted_at

Revision ID: 1e87eaf58567
Revises: 18fdc49838dd
Create Date: 2026-04-15 17:05:44.260254

"""
from typing import Sequence, Union

revision: str = '1e87eaf58567'
down_revision: Union[str, None] = '18fdc49838dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # deleted_at ya incluido en la migracion inicial
    pass


def downgrade() -> None:
    pass

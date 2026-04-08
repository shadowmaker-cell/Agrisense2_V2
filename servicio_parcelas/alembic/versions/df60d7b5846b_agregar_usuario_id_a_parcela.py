"""agregar usuario_id a parcela

Revision ID: df60d7b5846b
Revises: 6fe79a4b3ebc
Create Date: 2026-04-07 19:42:57.223661

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'df60d7b5846b'
down_revision: Union[str, None] = '6fe79a4b3ebc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('parcela', sa.Column('usuario_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_parcela_usuario_id'), 'parcela', ['usuario_id'], unique=False)
    op.execute("UPDATE parcela SET usuario_id = 1 WHERE usuario_id IS NULL")


def downgrade() -> None:
    op.drop_index(op.f('ix_parcela_usuario_id'), table_name='parcela')
    op.drop_column('parcela', 'usuario_id')
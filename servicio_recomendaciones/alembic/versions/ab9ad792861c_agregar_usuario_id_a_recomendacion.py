"""agregar usuario_id a recomendacion

Revision ID: ab9ad792861c
Revises: 
Create Date: 2026-04-08 06:46:22.243265

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'ab9ad792861c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('recomendacion', sa.Column('usuario_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_recomendacion_usuario_id'), 'recomendacion', ['usuario_id'], unique=False)
    op.execute("UPDATE recomendacion SET usuario_id = 1 WHERE usuario_id IS NULL")


def downgrade() -> None:
    op.drop_index(op.f('ix_recomendacion_usuario_id'), table_name='recomendacion')
    op.drop_column('recomendacion', 'usuario_id')
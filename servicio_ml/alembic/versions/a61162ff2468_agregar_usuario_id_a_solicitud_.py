"""agregar usuario_id a solicitud_prediccion

Revision ID: a61162ff2468
Revises: fa0d2bd49a2c
Create Date: 2026-04-07 20:59:12.182835

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a61162ff2468'
down_revision: Union[str, None] = 'fa0d2bd49a2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('solicitud_prediccion', sa.Column('usuario_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_solicitud_prediccion_usuario_id'), 'solicitud_prediccion', ['usuario_id'], unique=False)
    op.execute("UPDATE solicitud_prediccion SET usuario_id = 1 WHERE usuario_id IS NULL")


def downgrade() -> None:
    op.drop_index(op.f('ix_solicitud_prediccion_usuario_id'), table_name='solicitud_prediccion')
    op.drop_column('solicitud_prediccion', 'usuario_id')
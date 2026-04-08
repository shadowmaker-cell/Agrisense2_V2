"""agregar usuario_id a lectura y alerta

Revision ID: 116df047d3fe
Revises: 903c8157fe4e
Create Date: 2026-04-07 20:10:58.580824

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '116df047d3fe'
down_revision: Union[str, None] = '903c8157fe4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('lectura_sensor', sa.Column('usuario_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_lectura_sensor_usuario_id'), 'lectura_sensor', ['usuario_id'], unique=False)
    op.add_column('alerta_generada', sa.Column('usuario_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_alerta_generada_usuario_id'), 'alerta_generada', ['usuario_id'], unique=False)
    op.execute("UPDATE lectura_sensor SET usuario_id = 1 WHERE usuario_id IS NULL")
    op.execute("UPDATE alerta_generada SET usuario_id = 1 WHERE usuario_id IS NULL")


def downgrade() -> None:
    op.drop_index(op.f('ix_alerta_generada_usuario_id'), table_name='alerta_generada')
    op.drop_column('alerta_generada', 'usuario_id')
    op.drop_index(op.f('ix_lectura_sensor_usuario_id'), table_name='lectura_sensor')
    op.drop_column('lectura_sensor', 'usuario_id')
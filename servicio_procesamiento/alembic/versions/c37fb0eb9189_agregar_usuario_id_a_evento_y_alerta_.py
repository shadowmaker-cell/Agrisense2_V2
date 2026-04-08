"""agregar usuario_id a evento y alerta_stream

Revision ID: c37fb0eb9189
Revises: 2a4059122f46
Create Date: 2026-04-07 20:35:36.243012

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c37fb0eb9189'
down_revision: Union[str, None] = '2a4059122f46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('evento_procesado', sa.Column('usuario_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_evento_procesado_usuario_id'), 'evento_procesado', ['usuario_id'], unique=False)
    op.add_column('alerta_stream', sa.Column('usuario_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_alerta_stream_usuario_id'), 'alerta_stream', ['usuario_id'], unique=False)
    op.execute("UPDATE evento_procesado SET usuario_id = 1 WHERE usuario_id IS NULL")
    op.execute("UPDATE alerta_stream SET usuario_id = 1 WHERE usuario_id IS NULL")


def downgrade() -> None:
    op.drop_index(op.f('ix_alerta_stream_usuario_id'), table_name='alerta_stream')
    op.drop_column('alerta_stream', 'usuario_id')
    op.drop_index(op.f('ix_evento_procesado_usuario_id'), table_name='evento_procesado')
    op.drop_column('evento_procesado', 'usuario_id')
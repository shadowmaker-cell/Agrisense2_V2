"""agregar registro mantenimiento

Revision ID: 47d26e13739a
Revises: 7d78e5c1eff6
Create Date: 2026-04-14 15:35:44.538984

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '47d26e13739a'
down_revision: Union[str, None] = '7d78e5c1eff6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('registro_mantenimiento',
        sa.Column('id',               sa.Integer(),                  nullable=False),
        sa.Column('dispositivo_id',   sa.Integer(),                  nullable=False),
        sa.Column('usuario_id',       sa.Integer(),                  nullable=True),
        sa.Column('tipo',             sa.String(20),                 nullable=False, server_default='preventivo'),
        sa.Column('titulo',           sa.String(100),                nullable=False),
        sa.Column('descripcion',      sa.String(500),                nullable=True),
        sa.Column('causa',            sa.String(200),                nullable=True),
        sa.Column('acciones',         sa.String(500),                nullable=True),
        sa.Column('resultado',        sa.String(20),                 nullable=True, server_default='exitoso'),
        sa.Column('tecnico',          sa.String(100),                nullable=True),
        sa.Column('costo',            sa.Float(),                    nullable=True),
        sa.Column('fecha_inicio',     sa.DateTime(timezone=True),    nullable=False, server_default=sa.func.now()),
        sa.Column('fecha_fin',        sa.DateTime(timezone=True),    nullable=True),
        sa.Column('proxima_revision', sa.DateTime(timezone=True),    nullable=True),
        sa.Column('creado_en',        sa.DateTime(timezone=True),    server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['dispositivo_id'], ['dispositivo.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("tipo IN ('correctivo','preventivo','calibracion','inspeccion')", name='ck_mantenimiento_tipo'),
        sa.CheckConstraint("resultado IN ('exitoso','fallido','pendiente','parcial')", name='ck_mantenimiento_resultado'),
    )
    op.create_index('ix_registro_mantenimiento_dispositivo_id', 'registro_mantenimiento', ['dispositivo_id'])
    op.create_index('ix_registro_mantenimiento_usuario_id',     'registro_mantenimiento', ['usuario_id'])

def downgrade() -> None:
    op.drop_table('registro_mantenimiento')
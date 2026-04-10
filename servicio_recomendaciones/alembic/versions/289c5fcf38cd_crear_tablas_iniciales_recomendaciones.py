"""crear tablas iniciales recomendaciones

Revision ID: 289c5fcf38cd
Revises: ab9ad792861c
Create Date: 2026-04-09 21:26:47.572030

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '289c5fcf38cd'
down_revision: Union[str, None] = 'ab9ad792861c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('categoria_recomendacion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('icono', sa.String(10), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True, default=True),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )
    op.create_table('recomendacion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('parcela_id', sa.Integer(), nullable=True),
        sa.Column('dispositivo_id', sa.Integer(), nullable=True),
        sa.Column('id_logico', sa.String(50), nullable=True),
        sa.Column('categoria_id', sa.Integer(), sa.ForeignKey('categoria_recomendacion.id'), nullable=True),
        sa.Column('titulo', sa.String(200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('accion_sugerida', sa.Text(), nullable=True),
        sa.Column('prioridad', sa.String(20), nullable=True, default='media'),
        sa.Column('estado', sa.String(20), nullable=True, default='pendiente'),
        sa.Column('origen', sa.String(50), nullable=True),
        sa.Column('metrica_origen', sa.String(50), nullable=True),
        sa.Column('valor_detectado', sa.Float(), nullable=True),
        sa.Column('generada_en', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('aplicada_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valida_hasta', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_recomendacion_usuario_id', 'recomendacion', ['usuario_id'])
    op.create_index('ix_recomendacion_parcela_id', 'recomendacion', ['parcela_id'])


def downgrade() -> None:
    op.drop_table('recomendacion')
    op.drop_table('categoria_recomendacion')
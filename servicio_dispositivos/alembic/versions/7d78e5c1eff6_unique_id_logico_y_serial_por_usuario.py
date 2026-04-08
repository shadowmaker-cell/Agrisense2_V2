"""unique id_logico y serial por usuario

Revision ID: 7d78e5c1eff6
Revises: 16064b7455f7
Create Date: 2026-04-08 15:28:30.191246

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '7d78e5c1eff6'
down_revision: Union[str, None] = '16064b7455f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Eliminar constraints globales
    op.drop_constraint('dispositivo_id_logico_key', 'dispositivo', type_='unique')
    op.drop_constraint('dispositivo_numero_serial_key', 'dispositivo', type_='unique')
    # Crear constraints por usuario
    op.create_unique_constraint(
        'uq_dispositivo_id_logico_usuario',
        'dispositivo',
        ['usuario_id', 'id_logico']
    )
    op.create_unique_constraint(
        'uq_dispositivo_serial_usuario',
        'dispositivo',
        ['usuario_id', 'numero_serial']
    )


def downgrade() -> None:
    op.drop_constraint('uq_dispositivo_id_logico_usuario', 'dispositivo', type_='unique')
    op.drop_constraint('uq_dispositivo_serial_usuario', 'dispositivo', type_='unique')
    op.create_unique_constraint('dispositivo_id_logico_key', 'dispositivo', ['id_logico'])
    op.create_unique_constraint('dispositivo_numero_serial_key', 'dispositivo', ['numero_serial'])
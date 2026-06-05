"""add access log

Revision ID: b01346c95ba9
Revises: 8e06856bbcdf
Create Date: 2026-06-05 11:38:08.881163

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b01346c95ba9'
down_revision: Union[str, None] = '8e06856bbcdf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'access_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('ts', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ip', postgresql.INET(), nullable=True),
        sa.Column('country', sa.Text(), nullable=True),
        sa.Column('region', sa.Text(), nullable=True),
        sa.Column('city', sa.Text(), nullable=True),
        sa.Column('lat', sa.Numeric(precision=7, scale=4), nullable=True),
        sa.Column('lon', sa.Numeric(precision=7, scale=4), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('path', sa.Text(), nullable=False),
        sa.Column('referer', sa.Text(), nullable=True),
        sa.Column('gate', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_access_log_country'), 'access_log', ['country'], unique=False)
    op.create_index(op.f('ix_access_log_gate'), 'access_log', ['gate'], unique=False)
    op.create_index(op.f('ix_access_log_ts'), 'access_log', ['ts'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_access_log_ts'), table_name='access_log')
    op.drop_index(op.f('ix_access_log_gate'), table_name='access_log')
    op.drop_index(op.f('ix_access_log_country'), table_name='access_log')
    op.drop_table('access_log')

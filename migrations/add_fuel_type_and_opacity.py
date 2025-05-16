"""add fuel_type and opacity columns

Revision ID: 123456789abc
Revises: 
Create Date: 2025-05-12 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '123456789abc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add fuel_type column to kendaraan table
    op.add_column('kendaraan', 
                 sa.Column('fuel_type', sa.String(10), nullable=False, server_default='petrol'))
    
    # Add check constraint for fuel_type
    op.create_check_constraint(
        'ck_kendaraan_fuel_type',
        'kendaraan',
        sa.text("fuel_type IN ('petrol', 'diesel')")
    )
    
    # Add opacity column to hasil_uji table
    op.add_column('hasil_uji', 
                 sa.Column('opacity', sa.Float(), nullable=True))
    
    # Add check constraint for opacity
    op.create_check_constraint(
        'ck_opacity_nonneg',
        'hasil_uji',
        sa.text('opacity IS NULL OR opacity >= 0')
    )
    
    # Add opacity_max column to config table
    op.add_column('config', 
                 sa.Column('opacity_max', sa.Float(), nullable=False, server_default='50.0'))


def downgrade():
    # Remove columns and constraints in reverse order
    op.drop_column('config', 'opacity_max')
    op.drop_constraint('ck_opacity_nonneg', 'hasil_uji', type_='check')
    op.drop_column('hasil_uji', 'opacity')
    op.drop_constraint('ck_kendaraan_fuel_type', 'kendaraan', type_='check')
    op.drop_column('kendaraan', 'fuel_type')

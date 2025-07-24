"""Add contact fields to Invite model

Revision ID: add_contact_fields
Revises: a08ee25575d6
Create Date: 2025-07-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_contact_fields'
down_revision = 'a08ee25575d6'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to the invites table
    op.add_column('invites', sa.Column('ansprechpartner', sa.String(200), nullable=True))
    op.add_column('invites', sa.Column('strasse', sa.String(200), nullable=True))
    op.add_column('invites', sa.Column('plz', sa.String(10), nullable=True))
    op.add_column('invites', sa.Column('ort', sa.String(200), nullable=True))
    op.add_column('invites', sa.Column('telefon', sa.String(50), nullable=True))
    op.add_column('invites', sa.Column('email', sa.String(200), nullable=True))
    op.add_column('invites', sa.Column('qr_code_path', sa.String(512), nullable=True))


def downgrade():
    # Remove the columns added in upgrade
    op.drop_column('invites', 'ansprechpartner')
    op.drop_column('invites', 'strasse')
    op.drop_column('invites', 'plz')
    op.drop_column('invites', 'ort')
    op.drop_column('invites', 'telefon')
    op.drop_column('invites', 'email')
    op.drop_column('invites', 'qr_code_path')

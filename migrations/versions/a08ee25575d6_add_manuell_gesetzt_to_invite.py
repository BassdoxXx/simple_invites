"""Add manuell_gesetzt to Invite

Revision ID: a08ee25575d6
Revises: 
Create Date: 2025-07-13 21:32:44.667189

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a08ee25575d6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('invites', schema=None) as batch_op:
        batch_op.add_column(sa.Column('manuell_gesetzt', sa.Boolean(), nullable=True))

    with op.batch_alter_table('responses', schema=None) as batch_op:
        batch_op.drop_column('drinks')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('responses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('drinks', sa.VARCHAR(length=150), nullable=True))

    with op.batch_alter_table('invites', schema=None) as batch_op:
        batch_op.drop_column('manuell_gesetzt')

    # ### end Alembic commands ###

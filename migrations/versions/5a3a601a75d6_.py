"""empty message

Revision ID: 5a3a601a75d6
Revises: a34422d45fdc
Create Date: 2023-11-09 23:07:30.576283

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a3a601a75d6'
down_revision = 'a34422d45fdc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.add_column(sa.Column('google_id', sa.String(length=120), nullable=True))
        batch_op.create_unique_constraint(None, ['google_id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('google_id')

    # ### end Alembic commands ###

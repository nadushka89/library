"""empty message

Revision ID: 8396b6d3376e
Revises: 9ef55faaf5ff
Create Date: 2024-02-24 23:40:52.748453

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8396b6d3376e'
down_revision = '9ef55faaf5ff'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('avatar_path', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('avatar_path')

    # ### end Alembic commands ###

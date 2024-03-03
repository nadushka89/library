"""empty message

Revision ID: a23bd4eab976
Revises: bbb098ff62aa
Create Date: 2023-11-06 21:19:54.752958

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a23bd4eab976'
down_revision = 'bbb098ff62aa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.add_column(sa.Column('isbn', sa.String(length=20), nullable=True))
        batch_op.create_unique_constraint(None, ['isbn'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('isbn')

    # ### end Alembic commands ###

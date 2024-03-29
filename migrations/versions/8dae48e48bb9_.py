"""empty message

Revision ID: 8dae48e48bb9
Revises: f766d734537f
Create Date: 2023-11-29 00:33:34.115871

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '8dae48e48bb9'
down_revision = 'f766d734537f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.drop_column('is_ebook')
        batch_op.drop_column('web_reader_link')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.add_column(sa.Column('web_reader_link', mysql.VARCHAR(length=500), nullable=True))
        batch_op.add_column(sa.Column('is_ebook', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))

    # ### end Alembic commands ###

"""empty message

Revision ID: a165cef0dc95
Revises: ce2f56637491
Create Date: 2023-12-05 22:32:20.988244

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a165cef0dc95'
down_revision = 'ce2f56637491'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.alter_column('title',
               existing_type=mysql.VARCHAR(length=270),
               type_=sa.String(length=350),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.alter_column('title',
               existing_type=sa.String(length=350),
               type_=mysql.VARCHAR(length=270),
               existing_nullable=False)

    # ### end Alembic commands ###

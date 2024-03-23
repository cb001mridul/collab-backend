"""Revised2

Revision ID: a7f4de5f8d50
Revises: d09274af4f9c
Create Date: 2024-03-20 23:29:33.061761

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7f4de5f8d50'
down_revision = 'd09274af4f9c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('applied',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('contributor_id', sa.String(), nullable=False),
    sa.Column('project_id', sa.String(), nullable=False),
    sa.Column('admin_id', sa.String(), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('projects', sa.Column('subtitle', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('projects', 'subtitle')
    op.drop_table('applied')
    # ### end Alembic commands ###
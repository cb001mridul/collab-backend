"""revision

Revision ID: b4ee7512f532
Revises: ffb7edee8a7e
Create Date: 2024-03-24 22:03:52.248364

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4ee7512f532'
down_revision = 'ffb7edee8a7e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('experience', sa.Column('description', sa.String(), nullable=True))
    op.add_column('experience', sa.Column('location', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('experience', 'location')
    op.drop_column('experience', 'description')
    # ### end Alembic commands ###
"""add translation column to words

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('words', sa.Column('translation', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('words', 'translation')

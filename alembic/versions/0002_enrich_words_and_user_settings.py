"""enrich words with examples/synonyms/part_of_speech and add user display toggles

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("words", sa.Column("examples", sa.ARRAY(sa.Text), nullable=True))
    op.add_column("words", sa.Column("synonyms", sa.ARRAY(sa.Text), nullable=True))
    op.add_column("words", sa.Column("part_of_speech", sa.Text, nullable=True))

    op.add_column(
        "users",
        sa.Column("show_synonyms", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "users",
        sa.Column("show_examples", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("users", "show_examples")
    op.drop_column("users", "show_synonyms")
    op.drop_column("words", "part_of_speech")
    op.drop_column("words", "synonyms")
    op.drop_column("words", "examples")

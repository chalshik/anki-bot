"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )

    op.create_table(
        "words",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("word", sa.Text, nullable=False),
        sa.Column("definition", sa.Text),
        sa.Column("example", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.UniqueConstraint("user_id", "word", name="uq_words_user_word"),
    )

    op.create_table(
        "cards",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("word_id", sa.UUID, sa.ForeignKey("words.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_id", sa.BigInteger, nullable=False),
        sa.Column("state", sa.SmallInteger, nullable=False, server_default=sa.text("1")),
        sa.Column("step", sa.Integer),
        sa.Column("stability", sa.Float),
        sa.Column("difficulty", sa.Float),
        sa.Column(
            "due",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_review", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("cards")
    op.drop_table("words")
    op.drop_table("users")

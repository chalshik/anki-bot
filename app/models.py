import sqlalchemy as sa

metadata = sa.MetaData()

users = sa.Table(
    "users",
    metadata,
    sa.Column("id", sa.BigInteger, primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    sa.Column("show_synonyms", sa.Boolean, nullable=False, server_default=sa.text("true")),
    sa.Column("show_examples", sa.Boolean, nullable=False, server_default=sa.text("true")),
)

words = sa.Table(
    "words",
    metadata,
    sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sa.Column("word", sa.Text, nullable=False),
    sa.Column("definition", sa.Text),
    sa.Column("example", sa.Text),
    sa.Column("examples", sa.ARRAY(sa.Text)),
    sa.Column("synonyms", sa.ARRAY(sa.Text)),
    sa.Column("part_of_speech", sa.Text),
    sa.Column("translation", sa.Text),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    sa.UniqueConstraint("user_id", "word", name="uq_words_user_word"),
)

cards = sa.Table(
    "cards",
    metadata,
    sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("word_id", sa.UUID, sa.ForeignKey("words.id", ondelete="CASCADE"), nullable=False),
    sa.Column("card_id", sa.BigInteger, nullable=False),
    sa.Column("state", sa.SmallInteger, nullable=False, server_default=sa.text("1")),
    sa.Column("step", sa.Integer),
    sa.Column("stability", sa.Float),
    sa.Column("difficulty", sa.Float),
    sa.Column("due", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    sa.Column("last_review", sa.DateTime(timezone=True)),
)

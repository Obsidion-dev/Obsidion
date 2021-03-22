"""Create base tables

Revision ID: 851d11b8a33e
Revises:
Create Date: 2021-01-18 13:02:51.910663

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "851d11b8a33e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "guild",
        sa.Column("id", sa.BIGINT, primary_key=True),
        sa.Column("prefix", sa.Unicode(200)),
        sa.Column("regional", sa.Unicode(5)),
        sa.Column("locale", sa.Unicode(5)),
        sa.Column("server", sa.Unicode(200)),
        sa.Column("news", sa.JSON),
    )

    op.create_table(
        "account",
        sa.Column("id", sa.BIGINT, primary_key=True),
        sa.Column("uuid", sa.dialects.postgresql.UUID),
    )

    op.create_table(
        "rcon",
        sa.Column("id", sa.BIGINT, primary_key=True),
        sa.Column("server", sa.Unicode(200)),
        sa.Column("password", sa.Unicode(200)),
        sa.Column("port", sa.BIGINT),
        sa.Column("users", sa.ARRAY(sa.BIGINT)),
        sa.Column("channel", sa.BIGINT),
    )


def downgrade():
    op.drop_table("guild")
    op.drop_table("account")
    op.drop_table("rcon")

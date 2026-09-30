"""add message content and direction

Revision ID: c7cc9f618d7d
Revises: 0f6eaccaf2e2
Create Date: 2026-09-29 18:24:10.854792

"""
from collections.abc import Sequence
from typing import Union

import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7cc9f618d7d'
down_revision: Union[str, Sequence[str], None] = '0f6eaccaf2e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

message_direction_enum = sa.Enum(
    "INBOUND",
    "OUTBOUND",
    name="messagedirection",
)

message_direction_enum = sa.Enum(
    "INBOUND",
    "OUTBOUND",
    name="messagedirection",
)


def upgrade() -> None:
    message_direction_enum.create(op.get_bind())

    op.add_column(
        "message",
        sa.Column(
            "content",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
        ),
    )

    op.add_column(
        "message",
        sa.Column(
            "direction",
            message_direction_enum,
            nullable=False,
        ),
    )

    op.alter_column(
        "message",
        "campaign_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "message",
        "campaign_id",
        existing_type=sa.UUID(),
        nullable=False,
    )

    op.drop_column("message", "direction")
    op.drop_column("message", "content")

    message_direction_enum.drop(op.get_bind())
"""add unique constraint to teacher phone

Revision ID: f6b3d436916d
Revises: 6f038f5234c9
Create Date: 2026-10-01 18:13:26.435839

"""
from collections.abc import Sequence
from typing import Union

import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6b3d436916d'
down_revision: Union[str, Sequence[str], None] = '6f038f5234c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Fails if two existing teachers already share a phone number. That
    # needs a decision about which row is correct, so it is not resolved
    # automatically here.
    op.create_unique_constraint(
        "uq_teacher_phone",
        "teacher",
        ["phone"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_teacher_phone",
        "teacher",
        type_="unique",
    )

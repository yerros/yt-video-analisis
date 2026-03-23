"""change_disable_transcript_default_to_true

Revision ID: 1f28b66a192f
Revises: 354695bffb8b
Create Date: 2026-03-24 03:00:57.968757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f28b66a192f'
down_revision: Union[str, None] = '354695bffb8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change the default value for disable_transcript from false to true
    op.alter_column('jobs', 'disable_transcript',
                    server_default='true',
                    existing_type=sa.Boolean(),
                    existing_nullable=False)


def downgrade() -> None:
    # Revert the default value back to false
    op.alter_column('jobs', 'disable_transcript',
                    server_default='false',
                    existing_type=sa.Boolean(),
                    existing_nullable=False)

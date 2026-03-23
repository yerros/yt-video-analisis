"""add_index_youtube_url

Revision ID: f7e863f50d5d
Revises: 1f28b66a192f
Create Date: 2026-03-24 03:14:41.099351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7e863f50d5d'
down_revision: Union[str, None] = '1f28b66a192f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create index on youtube_url for faster duplicate detection
    op.create_index('ix_jobs_youtube_url', 'jobs', ['youtube_url'], unique=False)


def downgrade() -> None:
    # Drop the index
    op.drop_index('ix_jobs_youtube_url', table_name='jobs')

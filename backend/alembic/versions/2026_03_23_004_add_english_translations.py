"""Add English translation fields to jobs table

Revision ID: 004_english_translations
Revises: 003_youtube_metadata
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_english_translations'
down_revision: Union[str, None] = '003_youtube_metadata'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add English translation columns for video title and description
    op.add_column('jobs', sa.Column('title_en', sa.Text(), nullable=True))
    op.add_column('jobs', sa.Column('description_en', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove English translation columns
    op.drop_column('jobs', 'description_en')
    op.drop_column('jobs', 'title_en')

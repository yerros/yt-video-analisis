"""Add disable_transcript option to jobs table

Revision ID: 005_disable_transcript
Revises: 004_english_translations
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005_disable_transcript'
down_revision: Union[str, None] = '004_english_translations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add disable_transcript column with default False
    op.add_column('jobs', sa.Column('disable_transcript', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove disable_transcript column
    op.drop_column('jobs', 'disable_transcript')

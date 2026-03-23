"""Add YouTube metadata fields to jobs table

Revision ID: 003_youtube_metadata
Revises: 002_add_embeddings
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_youtube_metadata'
down_revision: Union[str, None] = '002_add_embeddings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add YouTube metadata columns
    op.add_column('jobs', sa.Column('youtube_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('channel_title', sa.Text(), nullable=True))
    op.add_column('jobs', sa.Column('channel_id', sa.Text(), nullable=True))
    op.add_column('jobs', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('jobs', sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('category_id', sa.String(length=50), nullable=True))
    op.add_column('jobs', sa.Column('published_at', sa.DateTime(), nullable=True))
    op.add_column('jobs', sa.Column('view_count', sa.Integer(), nullable=True))
    op.add_column('jobs', sa.Column('like_count', sa.Integer(), nullable=True))
    op.add_column('jobs', sa.Column('comment_count', sa.Integer(), nullable=True))
    op.add_column('jobs', sa.Column('thumbnail_url', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove YouTube metadata columns
    op.drop_column('jobs', 'thumbnail_url')
    op.drop_column('jobs', 'comment_count')
    op.drop_column('jobs', 'like_count')
    op.drop_column('jobs', 'view_count')
    op.drop_column('jobs', 'published_at')
    op.drop_column('jobs', 'category_id')
    op.drop_column('jobs', 'tags')
    op.drop_column('jobs', 'description')
    op.drop_column('jobs', 'channel_id')
    op.drop_column('jobs', 'channel_title')
    op.drop_column('jobs', 'youtube_metadata')

"""change_views_likes_comments_to_bigint

Revision ID: 354695bffb8b
Revises: 005_disable_transcript
Create Date: 2026-03-24 02:44:14.351470

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '354695bffb8b'
down_revision: Union[str, None] = '005_disable_transcript'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change view_count, like_count, comment_count from INTEGER to BIGINT
    # to support videos with billions of views (like Uptown Funk: 5.7B views)
    op.alter_column('jobs', 'view_count',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=True)
    op.alter_column('jobs', 'like_count',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=True)
    op.alter_column('jobs', 'comment_count',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=True)


def downgrade() -> None:
    # Revert back to INTEGER (may lose data if values > 2.1B)
    op.alter_column('jobs', 'comment_count',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column('jobs', 'like_count',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column('jobs', 'view_count',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=True)

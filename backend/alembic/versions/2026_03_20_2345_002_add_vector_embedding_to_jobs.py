"""Add vector embedding to jobs table

Revision ID: 002_add_embeddings
Revises: 001_add_chat_tables
Create Date: 2026-03-20 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '002_add_embeddings'
down_revision = '001_add_chat_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add vector embedding column to jobs table."""
    # Enable pgvector extension if not already enabled
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Add embedding column (1536 dimensions for text-embedding-3-small)
    op.add_column('jobs', sa.Column('embedding', Vector(1536), nullable=True))
    
    # Create HNSW index for fast similarity search
    # HNSW (Hierarchical Navigable Small World) is faster than IVFFlat for most use cases
    op.execute(
        "CREATE INDEX ON jobs USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Remove vector embedding column from jobs table."""
    op.drop_column('jobs', 'embedding')

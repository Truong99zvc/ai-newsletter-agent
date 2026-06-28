"""initial migration setup

Revision ID: 001_initial
Revises: 
Create Date: 2026-06-28 21:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. youtube_videos
    op.create_table(
        'youtube_videos',
        sa.Column('video_id', sa.String(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('channel_id', sa.String(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # 2. openai_articles
    op.create_table(
        'openai_articles',
        sa.Column('guid', sa.String(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # 3. anthropic_articles
    op.create_table(
        'anthropic_articles',
        sa.Column('guid', sa.String(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('markdown', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # 4. scraped_content
    op.create_table(
        'scraped_content',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    op.create_index('idx_scraped_source_type', 'scraped_content', ['source_type'])
    op.create_index('idx_scraped_published_at', 'scraped_content', ['published_at'])

    # 5. digests
    op.create_table(
        'digests',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('article_type', sa.String(), nullable=False),
        sa.Column('article_id', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    op.create_index('idx_digest_article_type', 'digests', ['article_type'])

    # 6. pipeline_runs
    op.create_table(
        'pipeline_runs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('hours_lookback', sa.Integer(), nullable=True),
        sa.Column('top_n', sa.Integer(), nullable=True),
        sa.Column('steps_completed', sa.JSON(), nullable=True),
        sa.Column('current_step', sa.String(), nullable=True),
        sa.Column('articles_scraped', sa.Integer(), nullable=True),
        sa.Column('articles_enriched', sa.Integer(), nullable=True),
        sa.Column('digests_created', sa.Integer(), nullable=True),
        sa.Column('email_sent', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_step', sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_table('pipeline_runs')
    op.drop_index('idx_digest_article_type', table_name='digests')
    op.drop_table('digests')
    op.drop_index('idx_scraped_published_at', table_name='scraped_content')
    op.drop_index('idx_scraped_source_type', table_name='scraped_content')
    op.drop_table('scraped_content')
    op.drop_table('anthropic_articles')
    op.drop_table('openai_articles')
    op.drop_table('youtube_videos')

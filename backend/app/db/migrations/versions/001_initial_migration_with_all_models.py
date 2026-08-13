"""Initial migration with all models

Revision ID: 001
Revises: 
Create Date: 2026-08-13 07:15:32.246736

"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create all tables from models
    op.create_table(
        'app_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('folder_path', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('folder_path'),
        sa.UniqueConstraint('title')
    )
    op.create_table(
        'video_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('audio_path', sa.String(), nullable=True),
        sa.Column('resolution', sa.String(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('fps', sa.Float(), nullable=True),
        sa.Column('quality_check_passed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id')
    )
    op.create_table(
        'processing_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('is_recurring', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('webhook_url', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'transcripts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('full_text', sa.Text(), nullable=False),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('whisper_model', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id')
    )
    op.create_table(
        'transcript_segments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transcript_id', sa.Integer(), nullable=False),
        sa.Column('segment_index', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['transcript_id'], ['transcripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transcript_id', 'segment_index')
    )
    op.create_table(
        'transcript_words',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('segment_id', sa.Integer(), nullable=False),
        sa.Column('word_index', sa.Integer(), nullable=False),
        sa.Column('word', sa.String(), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['segment_id'], ['transcript_segments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'analysis_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('llm_model', sa.String(), nullable=False),
        sa.Column('raw_json_output', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'highlight_moments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('start_segment_id', sa.Integer(), nullable=False),
        sa.Column('end_segment_id', sa.Integer(), nullable=False),
        sa.Column('start_word_id', sa.Integer(), nullable=True),
        sa.Column('end_word_id', sa.Integer(), nullable=True),
        sa.Column('suggested_duration_seconds', sa.Float(), nullable=True),
        sa.Column('engagement_reason', sa.Text(), nullable=True),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analysis_results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['end_segment_id'], ['transcript_segments.id'], ),
        sa.ForeignKeyConstraint(['end_word_id'], ['transcript_words.id'], ),
        sa.ForeignKeyConstraint(['start_segment_id'], ['transcript_segments.id'], ),
        sa.ForeignKeyConstraint(['start_word_id'], ['transcript_words.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'clips',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('highlight_moment_id', sa.Integer(), nullable=False),
        sa.Column('aspect_ratio', sa.String(), nullable=False),
        sa.Column('crop_mode', sa.String(), nullable=False),
        sa.Column('output_path', sa.String(), nullable=True),
        sa.Column('resolution', sa.String(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('render_status', sa.String(), nullable=False),
        sa.Column('render_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['highlight_moment_id'], ['highlight_moments.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'subtitle_styles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('clip_id', sa.Integer(), nullable=False),
        sa.Column('display_mode', sa.String(), nullable=False),
        sa.Column('font_family', sa.String(), nullable=False),
        sa.Column('font_size', sa.Integer(), nullable=False),
        sa.Column('font_weight', sa.String(), nullable=False),
        sa.Column('is_uppercase', sa.Boolean(), nullable=False),
        sa.Column('text_color', sa.String(), nullable=False),
        sa.Column('highlight_color', sa.String(), nullable=False),
        sa.Column('background_color', sa.String(), nullable=True),
        sa.Column('background_opacity', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['clip_id'], ['clips.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('clip_id')
    )
    op.create_table(
        'broll_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('clip_id', sa.Integer(), nullable=False),
        sa.Column('source_segment_id', sa.Integer(), nullable=True),
        sa.Column('pexels_query', sa.String(), nullable=True),
        sa.Column('pexels_video_id', sa.String(), nullable=True),
        sa.Column('pexels_video_url', sa.String(), nullable=True),
        sa.Column('local_cache_path', sa.String(), nullable=True),
        sa.Column('overlay_start_time', sa.Float(), nullable=True),
        sa.Column('overlay_end_time', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['clip_id'], ['clips.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_segment_id'], ['transcript_segments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'garbage_collection_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=True),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_name', sa.String(), nullable=False),
        sa.Column('api_key_value', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('service_name')
    )


def downgrade() -> None:
    op.drop_table('api_keys')
    op.drop_table('garbage_collection_logs')
    op.drop_table('broll_assets')
    op.drop_table('subtitle_styles')
    op.drop_table('clips')
    op.drop_table('highlight_moments')
    op.drop_table('analysis_results')
    op.drop_table('transcript_words')
    op.drop_table('transcript_segments')
    op.drop_table('transcripts')
    op.drop_table('processing_jobs')
    op.drop_table('video_sources')
    op.drop_table('projects')
    op.drop_table('app_settings')

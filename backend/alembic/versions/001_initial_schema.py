"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-12-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'surveys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now())
    )
    op.create_index('idx_surveys_active', 'surveys', ['is_active'])
    
    op.create_table(
        'survey_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('survey_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('is_current', sa.Boolean(), default=False),
        sa.Column('is_locked', sa.Boolean(), default=False),
        sa.Column('json_definition', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], ondelete='CASCADE')
    )
    op.create_index('idx_survey_versions_current', 'survey_versions', ['survey_id', 'is_current'])
    
    op.create_table(
        'questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('survey_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_type', sa.String(50), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), default=True),
        sa.Column('allow_prefer_not_to_answer', sa.Boolean(), default=True),
        sa.Column('skip_logic', postgresql.JSONB()),
        sa.Column('metadata_json', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.CheckConstraint("question_type IN ('single_choice', 'free_text', 'multiple_choice')"),
        sa.ForeignKeyConstraint(['survey_version_id'], ['survey_versions.id'], ondelete='CASCADE')
    )
    op.create_index('idx_questions_version_position', 'questions', ['survey_version_id', 'position'])
    
    op.create_table(
        'question_options',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('option_text', sa.String(500), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE')
    )
    op.create_index('idx_question_options_question', 'question_options', ['question_id', 'position'])
    
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('survey_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('anonymous_id', sa.String(255)),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('current_question_id', postgresql.UUID(as_uuid=True)),
        sa.Column('current_question_position', sa.Integer(), default=0),
        sa.Column('current_probe_count', sa.Integer(), default=0),
        sa.Column('is_follow_up_pending', sa.Boolean(), default=False),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('last_activity_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('user_agent', sa.Text()),
        sa.Column('ip_address', postgresql.INET()),
        sa.CheckConstraint("status IN ('active', 'completed', 'abandoned')"),
        sa.ForeignKeyConstraint(['survey_version_id'], ['survey_versions.id']),
        sa.ForeignKeyConstraint(['current_question_id'], ['questions.id'])
    )
    op.create_index('idx_sessions_status', 'sessions', ['status'])
    op.create_index('idx_sessions_survey_version', 'sessions', ['survey_version_id'])
    
    op.create_table(
        'session_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_type', sa.String(50), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True)),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('selected_option_id', postgresql.UUID(as_uuid=True)),
        sa.Column('is_follow_up', sa.Boolean(), default=False),
        sa.Column('parent_message_id', postgresql.UUID(as_uuid=True)),
        sa.Column('followup_reason', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "message_type IN ('survey_question', 'user_answer', 'follow_up_question', "
            "'follow_up_answer', 'system_message', 'prefer_not_to_answer')"
        ),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.ForeignKeyConstraint(['selected_option_id'], ['question_options.id']),
        sa.ForeignKeyConstraint(['parent_message_id'], ['session_messages.id'])
    )
    op.create_index('idx_session_messages_session', 'session_messages', ['session_id', 'sequence_number'])
    
    op.create_table(
        'session_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('key_themes', postgresql.ARRAY(sa.String())),
        sa.Column('last_updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE')
    )
    
    op.create_table(
        'model_calls',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True)),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('provider', sa.String(50), default="anthropic"),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('system_prompt', sa.Text()),
        sa.Column('temperature', sa.Float()),
        sa.Column('max_tokens', sa.Integer()),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('finish_reason', sa.String(50)),
        sa.Column('input_tokens', sa.Integer()),
        sa.Column('output_tokens', sa.Integer()),
        sa.Column('latency_ms', sa.Integer()),
        sa.Column('cost_usd', sa.Float()),
        sa.Column('reasoning_trace', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.CheckConstraint("agent_type IN ('follow_up', 'summary', 'exit_detector')"),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='SET NULL')
    )
    op.create_index('idx_model_calls_session', 'model_calls', ['session_id', 'created_at'])
    op.create_index('idx_model_calls_agent', 'model_calls', ['agent_type', 'created_at'])


def downgrade() -> None:
    op.drop_table('model_calls')
    op.drop_table('session_summaries')
    op.drop_table('session_messages')
    op.drop_table('sessions')
    op.drop_table('question_options')
    op.drop_table('questions')
    op.drop_table('survey_versions')
    op.drop_table('surveys')
"""Initial schema with versioning and respondent_id

Revision ID: 001
Revises: 
Create Date: 2026-01-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create surveys table
    op.create_table(
        'surveys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_surveys_name'), 'surveys', ['name'], unique=True)

    # Create survey_versions table
    op.create_table(
        'survey_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('survey_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=True),
        sa.Column('json_definition', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create questions table
    op.create_table(
        'questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('survey_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_type', sa.String(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.Column('allow_prefer_not_to_answer', sa.Boolean(), nullable=True),
        sa.Column('skip_logic', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['survey_version_id'], ['survey_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create question_options table
    op.create_table(
        'question_options',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('option_text', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create sessions table WITH respondent_id
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('survey_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('respondent_id', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_question_index', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),  # ADD THIS LINE
        sa.ForeignKeyConstraint(['survey_version_id'], ['survey_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # Create responses table WITH respondent_id
    op.create_table(
        'responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('respondent_id', sa.String(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_responses_id'), 'responses', ['id'], unique=False)
    op.create_index(op.f('ix_responses_respondent_id'), 'responses', ['respondent_id'], unique=False)

    # Create conversation_turns table WITH respondent_id
    op.create_table(
        'conversation_turns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('parent_message_id', postgresql.UUID(as_uuid=True), nullable=True),  # ADD THIS LINE
        sa.Column('respondent_id', sa.String(), nullable=False),
        sa.Column('speaker', sa.String(), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),  # RENAME from 'message'
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_turns_id'), 'conversation_turns', ['id'], unique=False)
    op.create_index(op.f('ix_conversation_turns_respondent_id'), 'conversation_turns', ['respondent_id'], unique=False)

    # Create session_messages table
    op.create_table(
        'session_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('is_follow_up', sa.Boolean(), nullable=True),
        sa.Column('followup_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create session_summaries table
    op.create_table(
        'session_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('key_themes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )

    # Create model_calls table
    op.create_table(
        'model_calls',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_id'), 'sessions', ['id'], unique=False)
    op.create_index(op.f('ix_sessions_respondent_id'), 'sessions', ['respondent_id'], unique=False)


def downgrade():
    op.drop_table('model_calls')
    op.drop_table('session_summaries')
    op.drop_table('session_messages')
    
    op.drop_index(op.f('ix_conversation_turns_respondent_id'), table_name='conversation_turns')
    op.drop_index(op.f('ix_conversation_turns_id'), table_name='conversation_turns')
    op.drop_table('conversation_turns')
    
    op.drop_index(op.f('ix_responses_respondent_id'), table_name='responses')
    op.drop_index(op.f('ix_responses_id'), table_name='responses')
    op.drop_table('responses')
    
    op.drop_index(op.f('ix_sessions_respondent_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_id'), table_name='sessions')
    op.drop_table('sessions')
    
    op.drop_table('question_options')
    op.drop_table('questions')
    op.drop_table('survey_versions')
    
    op.drop_index(op.f('ix_surveys_name'), table_name='surveys')
    op.drop_table('surveys')
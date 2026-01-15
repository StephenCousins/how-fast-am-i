"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2026-01-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create parkrun_athletes table
    op.create_table('parkrun_athletes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('athlete_id', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('total_runs', sa.Integer(), nullable=True),
        sa.Column('best_time_seconds', sa.Integer(), nullable=True),
        sa.Column('average_time_seconds', sa.Integer(), nullable=True),
        sa.Column('typical_avg_seconds', sa.Integer(), nullable=True),
        sa.Column('recent_avg_seconds', sa.Integer(), nullable=True),
        sa.Column('best_time', sa.String(length=20), nullable=True),
        sa.Column('average_time', sa.String(length=20), nullable=True),
        sa.Column('typical_avg_time', sa.String(length=20), nullable=True),
        sa.Column('recent_avg_time', sa.String(length=20), nullable=True),
        sa.Column('avg_age_grade', sa.Float(), nullable=True),
        sa.Column('recent_avg_age_grade', sa.Float(), nullable=True),
        sa.Column('pb_date', sa.String(length=50), nullable=True),
        sa.Column('pb_event', sa.String(length=100), nullable=True),
        sa.Column('pb_age', sa.String(length=50), nullable=True),
        sa.Column('trend', sa.String(length=20), nullable=True),
        sa.Column('trend_message', sa.String(length=200), nullable=True),
        sa.Column('outlier_count', sa.Integer(), nullable=True),
        sa.Column('normal_run_count', sa.Integer(), nullable=True),
        sa.Column('recent_results_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('lookup_count', sa.Integer(), nullable=True),
        sa.Column('last_lookup_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_parkrun_athletes_athlete_id', 'parkrun_athletes', ['athlete_id'], unique=True)

    # Create po10_athletes table
    op.create_table('po10_athletes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('athlete_id', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('club', sa.String(length=200), nullable=True),
        sa.Column('gender', sa.String(length=10), nullable=True),
        sa.Column('age_group', sa.String(length=20), nullable=True),
        sa.Column('pbs_json', sa.Text(), nullable=True),
        sa.Column('overall_percentile', sa.Float(), nullable=True),
        sa.Column('overall_age_grade', sa.Float(), nullable=True),
        sa.Column('overall_ability_level', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('lookup_count', sa.Integer(), nullable=True),
        sa.Column('last_lookup_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_po10_athletes_athlete_id', 'po10_athletes', ['athlete_id'], unique=True)

    # Create athlinks_athletes table
    op.create_table('athlinks_athletes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('athlete_id', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('total_races', sa.Integer(), nullable=True),
        sa.Column('total_distance_km', sa.Float(), nullable=True),
        sa.Column('total_distance_miles', sa.Float(), nullable=True),
        sa.Column('pbs_json', sa.Text(), nullable=True),
        sa.Column('results_json', sa.Text(), nullable=True),
        sa.Column('overall_percentile', sa.Float(), nullable=True),
        sa.Column('overall_ability_level', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('lookup_count', sa.Integer(), nullable=True),
        sa.Column('last_lookup_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_athlinks_athletes_athlete_id', 'athlinks_athletes', ['athlete_id'], unique=True)

    # Create lookups table
    op.create_table('lookups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('athlete_id', sa.String(length=20), nullable=False),
        sa.Column('athlete_name', sa.String(length=200), nullable=True),
        sa.Column('lookup_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lookups_athlete_id', 'lookups', ['athlete_id'], unique=False)


def downgrade():
    op.drop_index('ix_lookups_athlete_id', table_name='lookups')
    op.drop_table('lookups')
    op.drop_index('ix_athlinks_athletes_athlete_id', table_name='athlinks_athletes')
    op.drop_table('athlinks_athletes')
    op.drop_index('ix_po10_athletes_athlete_id', table_name='po10_athletes')
    op.drop_table('po10_athletes')
    op.drop_index('ix_parkrun_athletes_athlete_id', table_name='parkrun_athletes')
    op.drop_table('parkrun_athletes')

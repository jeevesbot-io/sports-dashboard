"""Phase 4: player stats, advanced stats, schema expansions

Revision ID: 51cfe9ae7943
Revises: 205b0d2d3e91
Create Date: 2026-02-14 18:31:49.778379

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '51cfe9ae7943'
down_revision = '205b0d2d3e91'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create advanced tables if they don't already exist (may have been created by create_all)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'sport_football_advanced_player' not in existing_tables:
        op.create_table('sport_football_advanced_player',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_name', sa.String(length=150), nullable=False),
        sa.Column('team_name', sa.String(length=100), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('position', sa.String(length=30), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('minutes_90s', sa.Float(), nullable=True),
        sa.Column('possession_pct', sa.Float(), nullable=True),
        sa.Column('progressive_passes', sa.Integer(), nullable=True),
        sa.Column('progressive_carries', sa.Integer(), nullable=True),
        sa.Column('progressive_passes_received', sa.Integer(), nullable=True),
        sa.Column('pressures', sa.Integer(), nullable=True),
        sa.Column('pressure_success_pct', sa.Float(), nullable=True),
        sa.Column('tackles', sa.Integer(), nullable=True),
        sa.Column('interceptions', sa.Integer(), nullable=True),
        sa.Column('blocks', sa.Integer(), nullable=True),
        sa.Column('sca', sa.Integer(), nullable=True),
        sa.Column('gca', sa.Integer(), nullable=True),
        sa.Column('passes_completed', sa.Integer(), nullable=True),
        sa.Column('pass_completion_pct', sa.Float(), nullable=True),
        sa.Column('key_passes', sa.Integer(), nullable=True),
        sa.Column('crosses', sa.Integer(), nullable=True),
        sa.Column('through_balls', sa.Integer(), nullable=True),
        sa.Column('carries', sa.Integer(), nullable=True),
        sa.Column('take_ons', sa.Integer(), nullable=True),
        sa.Column('take_on_pct', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
        )

    if 'sport_football_advanced_team' not in existing_tables:
        op.create_table('sport_football_advanced_team',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_name', sa.String(length=100), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('possession_pct', sa.Float(), nullable=True),
        sa.Column('progressive_passes', sa.Integer(), nullable=True),
        sa.Column('progressive_carries', sa.Integer(), nullable=True),
        sa.Column('pressures', sa.Integer(), nullable=True),
        sa.Column('pressure_success_pct', sa.Float(), nullable=True),
        sa.Column('tackles', sa.Integer(), nullable=True),
        sa.Column('interceptions', sa.Integer(), nullable=True),
        sa.Column('blocks', sa.Integer(), nullable=True),
        sa.Column('sca', sa.Integer(), nullable=True),
        sa.Column('gca', sa.Integer(), nullable=True),
        sa.Column('passes_completed', sa.Integer(), nullable=True),
        sa.Column('pass_completion_pct', sa.Float(), nullable=True),
        sa.Column('key_passes', sa.Integer(), nullable=True),
        sa.Column('crosses', sa.Integer(), nullable=True),
        sa.Column('through_balls', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
        )

    # Add new columns to sport_football_player_stats (table exists but only has id/created_at/updated_at)
    existing_cols = {c['name'] for c in inspector.get_columns('sport_football_player_stats')}
    new_cols = [
        ('understat_player_id', sa.String(length=50), True),
        ('name', sa.String(length=150), True),
        ('team_name', sa.String(length=100), True),
        ('season', sa.Integer(), True),
        ('games', sa.Integer(), True),
        ('minutes', sa.Integer(), True),
        ('goals', sa.Integer(), True),
        ('assists', sa.Integer(), True),
        ('shots', sa.Integer(), True),
        ('key_passes', sa.Integer(), True),
        ('xg', sa.Float(), True),
        ('xa', sa.Float(), True),
        ('npg', sa.Integer(), True),
        ('npxg', sa.Float(), True),
        ('xg_per_90', sa.Float(), True),
        ('goals_minus_xg', sa.Float(), True),
    ]
    for col_name, col_type, nullable in new_cols:
        if col_name not in existing_cols:
            op.add_column('sport_football_player_stats', sa.Column(col_name, col_type, nullable=nullable))


def downgrade() -> None:
    for col in ['goals_minus_xg', 'xg_per_90', 'npxg', 'npg', 'xa', 'xg',
                'key_passes', 'shots', 'assists', 'goals', 'minutes', 'games',
                'season', 'team_name', 'name', 'understat_player_id']:
        op.drop_column('sport_football_player_stats', col)
    op.drop_table('sport_football_advanced_team')
    op.drop_table('sport_football_advanced_player')
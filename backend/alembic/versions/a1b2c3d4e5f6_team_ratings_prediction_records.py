"""Add team ratings and prediction records tables

Revision ID: a1b2c3d4e5f6
Revises: 51cfe9ae7943
Create Date: 2026-02-14 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '51cfe9ae7943'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'sport_football_team_ratings' not in existing_tables:
        op.create_table('sport_football_team_ratings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('team_id', sa.Integer(), nullable=False),
            sa.Column('season', sa.Integer(), nullable=False),
            sa.Column('rating', sa.Float(), nullable=True, server_default='0.5'),
            sa.Column('seasons_analyzed', sa.Integer(), nullable=True, server_default='1'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['team_id'], ['sport_football_teams.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if 'sport_football_prediction_records' not in existing_tables:
        op.create_table('sport_football_prediction_records',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('fixture_id', sa.Integer(), nullable=False),
            sa.Column('season', sa.Integer(), nullable=False),
            sa.Column('predicted_home_score', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('predicted_away_score', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('home_win_prob', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('draw_prob', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('away_win_prob', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('model_name', sa.String(length=50), nullable=True, server_default='poisson'),
            sa.Column('actual_home_score', sa.Integer(), nullable=True),
            sa.Column('actual_away_score', sa.Integer(), nullable=True),
            sa.Column('outcome_correct', sa.Boolean(), nullable=True),
            sa.Column('score_correct', sa.Boolean(), nullable=True),
            sa.Column('score_error', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['fixture_id'], ['sport_football_fixtures.id']),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    op.drop_table('sport_football_prediction_records')
    op.drop_table('sport_football_team_ratings')

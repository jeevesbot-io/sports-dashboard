"""
Football business logic service.
Adapted from footballdash data_processor.py with async support.
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
from sqlalchemy.orm import selectinload

from .models import (
    FootballTeam, FootballFixture, FootballStanding, FootballXG,
    FootballTeamRating, FootballPredictionRecord
)
from .schemas import (
    FootballTeamResponse, FootballTeamDetail, FootballFixtureResponse,
    FootballStandingResponse, FootballFormAnalysis
)
from .client import FootballAPIClient
from ...config import settings
from sqlalchemy import func, update, delete

logger = logging.getLogger(__name__)


class FootballService:
    """Service class for football-related business logic."""
    
    def __init__(self):
        self.api_client = FootballAPIClient()
    
    async def get_teams(self, db: AsyncSession) -> List[FootballTeamResponse]:
        """
        Get all football teams.
        
        Args:
            db: Database session
            
        Returns:
            List of football teams
        """
        result = await db.execute(
            select(FootballTeam).order_by(FootballTeam.name)
        )
        teams = result.scalars().all()
        return [FootballTeamResponse.model_validate(team) for team in teams]
    
    async def get_team_by_id(
        self,
        team_id: int,
        db: AsyncSession
    ) -> Optional[FootballTeamDetail]:
        """
        Get team by ID with detailed statistics.
        
        Args:
            team_id: Team ID
            db: Database session
            
        Returns:
            Team details with statistics or None if not found
        """
        # Get team with relationships
        result = await db.execute(
            select(FootballTeam)
            .options(
                selectinload(FootballTeam.home_fixtures),
                selectinload(FootballTeam.away_fixtures),
                selectinload(FootballTeam.standings)
            )
            .where(FootballTeam.id == team_id)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            return None
        
        # Calculate statistics
        stats = await self._calculate_team_stats(team, db)
        
        team_detail = FootballTeamDetail.model_validate(team)
        team_detail.total_matches = stats["total_matches"]
        team_detail.wins = stats["wins"]
        team_detail.draws = stats["draws"]
        team_detail.losses = stats["losses"]
        team_detail.goals_for = stats["goals_for"]
        team_detail.goals_against = stats["goals_against"]
        team_detail.goal_difference = stats["goal_difference"]
        team_detail.points = stats["points"]
        team_detail.win_percentage = stats["win_percentage"]
        team_detail.current_position = stats["current_position"]
        
        return team_detail
    
    async def get_fixtures(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        status: Optional[str] = None,
        team_name: Optional[str] = None,
        matchday: Optional[int] = None,
        limit: int = 50
    ) -> List[FootballFixtureResponse]:
        """
        Get fixtures with optional filters.
        
        Args:
            db: Database session
            season: Optional season filter
            status: Optional status filter
            team_name: Optional team name filter
            matchday: Optional matchday filter
            limit: Maximum results
            
        Returns:
            List of fixtures
        """
        query = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        )
        
        # Apply filters
        filters = []
        if season:
            filters.append(FootballFixture.season == season)
        if status:
            filters.append(FootballFixture.status == status)
        if matchday:
            filters.append(FootballFixture.matchday == matchday)
        if team_name:
            # Join with teams for name filtering
            query = query.join(
                FootballTeam,
                or_(
                    FootballFixture.home_team_id == FootballTeam.id,
                    FootballFixture.away_team_id == FootballTeam.id
                )
            )
            filters.append(
                or_(
                    FootballTeam.name.ilike(f"%{team_name}%"),
                    FootballTeam.short_name.ilike(f"%{team_name}%")
                )
            )
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(desc(FootballFixture.utc_date)).limit(limit)
        
        result = await db.execute(query)
        fixtures = result.scalars().all()
        
        return [FootballFixtureResponse.model_validate(fixture) for fixture in fixtures]
    
    async def get_standings(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        matchday: Optional[str] = "latest"
    ) -> List[FootballStandingResponse]:
        """
        Get league standings.
        
        Args:
            db: Database session
            season: Season year
            matchday: Matchday number or 'latest'
            
        Returns:
            League standings
        """
        if season is None:
            season = settings.current_season
        query = select(FootballStanding).options(
            selectinload(FootballStanding.team)
        ).where(FootballStanding.season == season)

        if matchday and matchday != "latest":
            try:
                matchday_int = int(matchday)
                query = query.where(FootballStanding.matchday == matchday_int)
            except ValueError:
                pass  # Use latest if invalid matchday
        else:
            # Get latest matchday for the season
            latest_matchday_query = select(FootballStanding.matchday).where(
                FootballStanding.season == season
            ).order_by(desc(FootballStanding.matchday)).limit(1)
            latest_result = await db.execute(latest_matchday_query)
            latest_matchday = latest_result.scalar()
            
            if latest_matchday:
                query = query.where(FootballStanding.matchday == latest_matchday)
        
        query = query.order_by(FootballStanding.position)
        
        result = await db.execute(query)
        standings = result.scalars().all()
        
        # Convert to response objects and calculate computed fields
        response_standings = []
        for standing in standings:
            standing_response = FootballStandingResponse.model_validate(standing)
            
            # Calculate computed fields
            if standing.played > 0:
                standing_response.win_percentage = round((standing.won / standing.played) * 100, 1)
                standing_response.points_per_game = round(standing.points / standing.played, 2)
            else:
                standing_response.win_percentage = 0.0
                standing_response.points_per_game = 0.0
            
            response_standings.append(standing_response)
        
        return response_standings
    
    async def get_team_form(
        self,
        team_id: int,
        db: AsyncSession,
        games: int = 5
    ) -> Optional[FootballFormAnalysis]:
        """
        Get team form analysis for recent games.
        
        Args:
            team_id: Team ID
            db: Database session
            games: Number of recent games to analyze
            
        Returns:
            Form analysis or None if team not found
        """
        # Get team
        team_result = await db.execute(
            select(FootballTeam).where(FootballTeam.id == team_id)
        )
        team = team_result.scalar_one_or_none()
        
        if not team:
            return None
        
        # Get recent fixtures for this team
        fixtures_query = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        ).where(
            and_(
                or_(
                    FootballFixture.home_team_id == team_id,
                    FootballFixture.away_team_id == team_id
                ),
                FootballFixture.status == "FINISHED"
            )
        ).order_by(desc(FootballFixture.utc_date)).limit(games)
        
        fixtures_result = await db.execute(fixtures_query)
        recent_fixtures = list(fixtures_result.scalars().all())
        
        # Calculate form statistics
        wins = draws = losses = 0
        goals_for = goals_against = 0
        form_string = ""
        
        for fixture in reversed(recent_fixtures):  # Process in chronological order
            is_home = fixture.home_team_id == team_id
            
            if fixture.home_score is not None and fixture.away_score is not None:
                team_score = fixture.home_score if is_home else fixture.away_score
                opponent_score = fixture.away_score if is_home else fixture.home_score
                
                goals_for += team_score
                goals_against += opponent_score
                
                if team_score > opponent_score:
                    wins += 1
                    form_string += "W"
                elif team_score < opponent_score:
                    losses += 1
                    form_string += "L"
                else:
                    draws += 1
                    form_string += "D"
        
        points = wins * 3 + draws
        games_analyzed = len(recent_fixtures)
        win_percentage = (wins / games_analyzed * 100) if games_analyzed > 0 else 0.0
        
        return FootballFormAnalysis(
            team=FootballTeamResponse.model_validate(team),
            games_analyzed=games_analyzed,
            form_string=form_string,
            wins=wins,
            draws=draws,
            losses=losses,
            goals_for=goals_for,
            goals_against=goals_against,
            points=points,
            win_percentage=round(win_percentage, 1),
            recent_fixtures=[
                FootballFixtureResponse.model_validate(f) for f in recent_fixtures
            ]
        )
    
    async def _calculate_team_stats(
        self,
        team: FootballTeam,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Calculate team statistics from fixtures and standings."""
        # Get all finished fixtures for this team in current season
        current_season = settings.current_season
        
        fixtures_query = select(FootballFixture).where(
            and_(
                or_(
                    FootballFixture.home_team_id == team.id,
                    FootballFixture.away_team_id == team.id
                ),
                FootballFixture.season == current_season,
                FootballFixture.status == "FINISHED"
            )
        )
        
        fixtures_result = await db.execute(fixtures_query)
        fixtures = list(fixtures_result.scalars().all())
        
        # Calculate statistics
        wins = draws = losses = 0
        goals_for = goals_against = 0
        
        for fixture in fixtures:
            is_home = fixture.home_team_id == team.id
            
            if fixture.home_score is not None and fixture.away_score is not None:
                team_score = fixture.home_score if is_home else fixture.away_score
                opponent_score = fixture.away_score if is_home else fixture.home_score
                
                goals_for += team_score
                goals_against += opponent_score
                
                if team_score > opponent_score:
                    wins += 1
                elif team_score < opponent_score:
                    losses += 1
                else:
                    draws += 1
        
        total_matches = len(fixtures)
        points = wins * 3 + draws
        win_percentage = (wins / total_matches * 100) if total_matches > 0 else 0.0
        goal_difference = goals_for - goals_against
        
        # Get current position from standings
        position_query = select(FootballStanding.position).where(
            and_(
                FootballStanding.team_id == team.id,
                FootballStanding.season == current_season
            )
        ).order_by(desc(FootballStanding.matchday)).limit(1)
        
        position_result = await db.execute(position_query)
        current_position = position_result.scalar()
        
        return {
            "total_matches": total_matches,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": goal_difference,
            "points": points,
            "win_percentage": round(win_percentage, 1),
            "current_position": current_position
        }
    
    async def get_head_to_head(
        self,
        team1_name: str,
        team2_name: str,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get head-to-head record between two teams.
        
        Args:
            team1_name: First team name
            team2_name: Second team name
            db: Database session
            season: Optional season filter
            
        Returns:
            Head-to-head analysis
        """
        # Get teams
        team1_query = select(FootballTeam).where(
            or_(
                FootballTeam.name.ilike(f"%{team1_name}%"),
                FootballTeam.short_name.ilike(f"%{team1_name}%")
            )
        )
        team2_query = select(FootballTeam).where(
            or_(
                FootballTeam.name.ilike(f"%{team2_name}%"),
                FootballTeam.short_name.ilike(f"%{team2_name}%")
            )
        )
        
        team1_result = await db.execute(team1_query)
        team2_result = await db.execute(team2_query)
        
        team1 = team1_result.scalar_one_or_none()
        team2 = team2_result.scalar_one_or_none()
        
        if not team1 or not team2:
            return {
                "error": f"Team not found: {team1_name if not team1 else team2_name}",
                "team1": team1_name,
                "team2": team2_name,
                "matches": [],
                "team1_wins": 0,
                "team2_wins": 0,
                "draws": 0
            }
        
        # Get matches between these teams
        matches_query = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        ).where(
            and_(
                or_(
                    and_(FootballFixture.home_team_id == team1.id, FootballFixture.away_team_id == team2.id),
                    and_(FootballFixture.home_team_id == team2.id, FootballFixture.away_team_id == team1.id)
                ),
                FootballFixture.status == "FINISHED"
            )
        )
        
        if season:
            matches_query = matches_query.where(FootballFixture.season == season)
        
        matches_query = matches_query.order_by(desc(FootballFixture.utc_date))
        
        matches_result = await db.execute(matches_query)
        matches = list(matches_result.scalars().all())
        
        # Calculate head-to-head record
        team1_wins = team2_wins = draws = 0
        team1_goals = team2_goals = 0
        
        for match in matches:
            if match.home_score is not None and match.away_score is not None:
                # Determine which team scored how many
                if match.home_team_id == team1.id:
                    # Team1 is home
                    t1_score, t2_score = match.home_score, match.away_score
                else:
                    # Team1 is away
                    t1_score, t2_score = match.away_score, match.home_score
                
                team1_goals += t1_score
                team2_goals += t2_score
                
                if t1_score > t2_score:
                    team1_wins += 1
                elif t2_score > t1_score:
                    team2_wins += 1
                else:
                    draws += 1
        
        return {
            "team1": FootballTeamResponse.model_validate(team1),
            "team2": FootballTeamResponse.model_validate(team2),
            "matches": [FootballFixtureResponse.model_validate(m) for m in matches],
            "team1_wins": team1_wins,
            "team2_wins": team2_wins,
            "draws": draws,
            "team1_goals": team1_goals,
            "team2_goals": team2_goals,
            "total_matches": len(matches)
        }
    
    async def get_xg_standings(
        self,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get xG-based league table.
        
        Args:
            db: Database session
            season: Season year
            
        Returns:
            League table with xG data
        """
        if season is None:
            season = settings.current_season
        from .models import FootballXG
        from sqlalchemy import func
        
        # Query xG data grouped by team
        xg_query = select(
            FootballXG.home_team.label('team_name'),
            func.sum(FootballXG.home_xg).label('xg_for'),
            func.sum(FootballXG.away_xg).label('xg_against'),
            func.sum(FootballXG.home_goals).label('goals_for'),
            func.sum(FootballXG.away_goals).label('goals_against'),
            func.count().label('matches')
        ).where(FootballXG.season == season).group_by(FootballXG.home_team)
        
        # Add away games
        xg_away_query = select(
            FootballXG.away_team.label('team_name'),
            func.sum(FootballXG.away_xg).label('xg_for'),
            func.sum(FootballXG.home_xg).label('xg_against'),
            func.sum(FootballXG.away_goals).label('goals_for'),
            func.sum(FootballXG.home_goals).label('goals_against'),
            func.count().label('matches')
        ).where(FootballXG.season == season).group_by(FootballXG.away_team)
        
        # Execute queries
        home_result = await db.execute(xg_query)
        away_result = await db.execute(xg_away_query)
        
        # Combine results
        xg_stats = {}
        
        for row in home_result:
            xg_stats[row.team_name] = {
                'team_name': row.team_name,
                'xg_for': float(row.xg_for or 0),
                'xg_against': float(row.xg_against or 0),
                'goals_for': int(row.goals_for or 0),
                'goals_against': int(row.goals_against or 0),
                'matches': int(row.matches or 0)
            }
        
        for row in away_result:
            if row.team_name in xg_stats:
                xg_stats[row.team_name]['xg_for'] += float(row.xg_for or 0)
                xg_stats[row.team_name]['xg_against'] += float(row.xg_against or 0)
                xg_stats[row.team_name]['goals_for'] += int(row.goals_for or 0)
                xg_stats[row.team_name]['goals_against'] += int(row.goals_against or 0)
                xg_stats[row.team_name]['matches'] += int(row.matches or 0)
            else:
                xg_stats[row.team_name] = {
                    'team_name': row.team_name,
                    'xg_for': float(row.xg_for or 0),
                    'xg_against': float(row.xg_against or 0),
                    'goals_for': int(row.goals_for or 0),
                    'goals_against': int(row.goals_against or 0),
                    'matches': int(row.matches or 0)
                }
        
        # Calculate derived metrics
        standings = []
        for team_name, stats in xg_stats.items():
            xg_diff = stats['xg_for'] - stats['xg_against']
            actual_diff = stats['goals_for'] - stats['goals_against']
            overperformance = actual_diff - xg_diff
            
            standings.append({
                'team': team_name,
                'matches': stats['matches'],
                'xg_for': round(stats['xg_for'], 2),
                'xg_against': round(stats['xg_against'], 2),
                'xg_diff': round(xg_diff, 2),
                'goals_for': stats['goals_for'],
                'goals_against': stats['goals_against'],
                'goal_diff': actual_diff,
                'overperformance': round(overperformance, 2)
            })
        
        # Sort by xG difference
        standings.sort(key=lambda x: x['xg_diff'], reverse=True)
        
        return standings
    
    async def get_xg_overperformers(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        min_threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Get teams significantly over/under-performing their xG.
        
        Args:
            db: Database session
            season: Season year
            min_threshold: Minimum overperformance threshold
            
        Returns:
            List of over/under-performing teams
        """
        xg_standings = await self.get_xg_standings(db, season)
        
        # Filter for significant over/under-performers
        significant_performers = [
            team for team in xg_standings 
            if abs(team['overperformance']) >= min_threshold
        ]
        
        # Sort by overperformance (highest first)
        significant_performers.sort(key=lambda x: x['overperformance'], reverse=True)
        
        return significant_performers
    
    async def get_team_xg_analysis(
        self,
        team_id: int,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get xG analysis for a specific team.
        
        Args:
            team_id: Team ID
            db: Database session
            season: Season year
            
        Returns:
            Team xG analysis
        """
        if season is None:
            season = settings.current_season
        # Get team
        team_result = await db.execute(
            select(FootballTeam).where(FootballTeam.id == team_id)
        )
        team = team_result.scalar_one_or_none()

        if not team:
            return None

        from .models import FootballXG
        from sqlalchemy import func

        # Build name variants to match xG data (which uses Understat naming)
        name_variants = {team.name, team.short_name}
        for suffix in [' FC', ' AFC']:
            if team.name.endswith(suffix):
                name_variants.add(team.name[:-len(suffix)])

        # Get team's xG data
        home_query = select(
            func.sum(FootballXG.home_xg).label('xg_for'),
            func.sum(FootballXG.away_xg).label('xg_against'),
            func.sum(FootballXG.home_goals).label('goals_for'),
            func.sum(FootballXG.away_goals).label('goals_against'),
            func.count().label('home_matches')
        ).where(
            and_(
                FootballXG.home_team.in_(name_variants),
                FootballXG.season == season
            )
        )

        away_query = select(
            func.sum(FootballXG.away_xg).label('xg_for'),
            func.sum(FootballXG.home_xg).label('xg_against'),
            func.sum(FootballXG.away_goals).label('goals_for'),
            func.sum(FootballXG.home_goals).label('goals_against'),
            func.count().label('away_matches')
        ).where(
            and_(
                FootballXG.away_team.in_(name_variants),
                FootballXG.season == season
            )
        )
        
        home_result = await db.execute(home_query)
        away_result = await db.execute(away_query)
        
        home_stats = home_result.first()
        away_stats = away_result.first()
        
        # Combine stats
        total_xg_for = (float(home_stats.xg_for or 0) + 
                       float(away_stats.xg_for or 0))
        total_xg_against = (float(home_stats.xg_against or 0) + 
                           float(away_stats.xg_against or 0))
        total_goals_for = (int(home_stats.goals_for or 0) + 
                          int(away_stats.goals_for or 0))
        total_goals_against = (int(home_stats.goals_against or 0) + 
                              int(away_stats.goals_against or 0))
        total_matches = (int(home_stats.home_matches or 0) + 
                        int(away_stats.away_matches or 0))
        
        xg_diff = total_xg_for - total_xg_against
        actual_diff = total_goals_for - total_goals_against
        overperformance = actual_diff - xg_diff
        
        return {
            'team': FootballTeamResponse.model_validate(team),
            'season': season,
            'matches': total_matches,
            'xg_for': round(total_xg_for, 2),
            'xg_against': round(total_xg_against, 2),
            'xg_diff': round(xg_diff, 2),
            'goals_for': total_goals_for,
            'goals_against': total_goals_against,
            'goal_diff': actual_diff,
            'overperformance': round(overperformance, 2),
            'xg_per_game': round(total_xg_for / total_matches, 2) if total_matches > 0 else 0,
            'xa_per_game': round(total_xg_against / total_matches, 2) if total_matches > 0 else 0
        }
    
    async def get_points_progression(
        self,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get cumulative points progression for all teams by matchday.
        
        Args:
            db: Database session
            season: Season year
            
        Returns:
            Points progression data
        """
        if season is None:
            season = settings.current_season
        # Get all standings data ordered by matchday
        standings_query = select(FootballStanding).options(
            selectinload(FootballStanding.team)
        ).where(
            FootballStanding.season == season
        ).order_by(FootballStanding.matchday, FootballStanding.position)
        
        standings_result = await db.execute(standings_query)
        all_standings = list(standings_result.scalars().all())
        
        # Group by team and build progression
        team_progressions = {}
        matchdays = set()
        
        for standing in all_standings:
            team_name = standing.team.name
            matchday = standing.matchday
            
            matchdays.add(matchday)
            
            if team_name not in team_progressions:
                team_progressions[team_name] = {}
            
            team_progressions[team_name][matchday] = standing.points
        
        # Convert to chart format
        matchdays = sorted(list(matchdays))
        series_data = []
        
        for team_name, progression in team_progressions.items():
            points_data = []
            for matchday in matchdays:
                points_data.append({
                    'matchday': matchday,
                    'points': progression.get(matchday, 0)
                })
            
            series_data.append({
                'name': team_name,
                'data': points_data
            })
        
        return {
            'matchdays': matchdays,
            'series': series_data,
            'season': season
        }
    
    async def get_form_heatmap(
        self,
        db: AsyncSession,
        games: int = 10,
        season: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get form heatmap data for all teams.
        Batch-loads all finished fixtures in one query (O(1) instead of O(N)).

        Args:
            db: Database session
            games: Number of recent games
            season: Season year

        Returns:
            Form heatmap data
        """
        if season is None:
            season = settings.current_season

        # Single query: load all finished fixtures for the season with teams
        fixtures_query = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        ).where(
            and_(
                FootballFixture.season == season,
                FootballFixture.status == "FINISHED"
            )
        ).order_by(desc(FootballFixture.utc_date))

        fixtures_result = await db.execute(fixtures_query)
        all_fixtures = list(fixtures_result.scalars().all())

        # Group fixtures by team and compute form in-memory
        team_fixtures: Dict[str, List] = {}  # team_name -> list of (result_char,) sorted newest first
        team_names: Dict[str, str] = {}  # team_id -> team_name

        for fixture in all_fixtures:
            if fixture.home_score is None or fixture.away_score is None:
                continue

            home_name = fixture.home_team.name
            away_name = fixture.away_team.name

            # Home team result
            if home_name not in team_fixtures:
                team_fixtures[home_name] = []
            if fixture.home_score > fixture.away_score:
                team_fixtures[home_name].append('W')
            elif fixture.home_score < fixture.away_score:
                team_fixtures[home_name].append('L')
            else:
                team_fixtures[home_name].append('D')

            # Away team result
            if away_name not in team_fixtures:
                team_fixtures[away_name] = []
            if fixture.away_score > fixture.home_score:
                team_fixtures[away_name].append('W')
            elif fixture.away_score < fixture.home_score:
                team_fixtures[away_name].append('L')
            else:
                team_fixtures[away_name].append('D')

        heatmap_data = []
        for team_name, results in team_fixtures.items():
            # results are already sorted newest-first (from query ORDER BY)
            recent = results[:games]
            # Reverse for chronological order (oldest first)
            form_string = ''.join(reversed(recent))

            form_values = []
            for char in form_string:
                if char == 'W':
                    form_values.append(3)
                elif char == 'D':
                    form_values.append(1)
                else:
                    form_values.append(0)

            # Pad with zeros if needed
            while len(form_values) < games:
                form_values.insert(0, 0)

            wins = form_string.count('W')
            draws = form_string.count('D')
            losses = form_string.count('L')
            points = wins * 3 + draws
            games_analyzed = len(form_string)
            win_pct = round((wins / games_analyzed * 100), 1) if games_analyzed > 0 else 0.0

            heatmap_data.append({
                'team': team_name,
                'form_values': form_values,
                'form_string': form_string,
                'points': points,
                'win_percentage': win_pct
            })

        # Sort by recent form (points in last N games)
        heatmap_data.sort(key=lambda x: x['points'], reverse=True)

        return {
            'teams': heatmap_data,
            'games': games,
            'season': season
        }

    async def get_home_advantage_index(
        self,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Compute home/away splits and advantage index for each team.

        Returns:
            Dict with 'teams' list and 'season'.
        """
        if season is None:
            season = settings.current_season

        fixtures_query = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        ).where(
            and_(
                FootballFixture.season == season,
                FootballFixture.status == "FINISHED"
            )
        )
        result = await db.execute(fixtures_query)
        fixtures = list(result.scalars().all())

        teams: Dict[str, Dict[str, Any]] = {}

        for f in fixtures:
            if f.home_score is None or f.away_score is None:
                continue

            h_name = f.home_team.name
            a_name = f.away_team.name

            for name in (h_name, a_name):
                if name not in teams:
                    teams[name] = {
                        'home_played': 0, 'home_won': 0, 'home_drawn': 0, 'home_lost': 0,
                        'home_gf': 0, 'home_ga': 0,
                        'away_played': 0, 'away_won': 0, 'away_drawn': 0, 'away_lost': 0,
                        'away_gf': 0, 'away_ga': 0
                    }

            # Home team stats
            teams[h_name]['home_played'] += 1
            teams[h_name]['home_gf'] += f.home_score
            teams[h_name]['home_ga'] += f.away_score
            if f.home_score > f.away_score:
                teams[h_name]['home_won'] += 1
            elif f.home_score < f.away_score:
                teams[h_name]['home_lost'] += 1
            else:
                teams[h_name]['home_drawn'] += 1

            # Away team stats
            teams[a_name]['away_played'] += 1
            teams[a_name]['away_gf'] += f.away_score
            teams[a_name]['away_ga'] += f.home_score
            if f.away_score > f.home_score:
                teams[a_name]['away_won'] += 1
            elif f.away_score < f.home_score:
                teams[a_name]['away_lost'] += 1
            else:
                teams[a_name]['away_drawn'] += 1

        result_list = []
        for name, s in teams.items():
            home_ppg = round((s['home_won'] * 3 + s['home_drawn']) / s['home_played'], 2) if s['home_played'] > 0 else 0.0
            away_ppg = round((s['away_won'] * 3 + s['away_drawn']) / s['away_played'], 2) if s['away_played'] > 0 else 0.0
            result_list.append({
                'team': name,
                **s,
                'home_ppg': home_ppg,
                'away_ppg': away_ppg,
                'advantage_index': round(home_ppg - away_ppg, 2)
            })

        result_list.sort(key=lambda x: x['advantage_index'], reverse=True)
        return {'teams': result_list, 'season': season}

    async def get_team_xg_timeline(
        self,
        team_id: int,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cumulative xG timeline for a team."""
        if season is None:
            season = settings.current_season

        team_result = await db.execute(
            select(FootballTeam).where(FootballTeam.id == team_id)
        )
        team = team_result.scalar_one_or_none()
        if not team:
            return None

        # Build set of possible name variants (teams table uses "Newcastle United FC",
        # xG table uses Understat names like "Newcastle United" or mapped names)
        name_variants = {team.name, team.short_name}
        # Strip common suffixes to match xG data
        for suffix in [' FC', ' AFC']:
            if team.name.endswith(suffix):
                name_variants.add(team.name[:-len(suffix)])

        # Get xG data for this team ordered by date
        xg_query = select(FootballXG).where(
            and_(
                or_(
                    FootballXG.home_team.in_(name_variants),
                    FootballXG.away_team.in_(name_variants)
                ),
                FootballXG.season == season
            )
        ).order_by(FootballXG.date)

        xg_result = await db.execute(xg_query)
        xg_records = list(xg_result.scalars().all())

        timeline = []
        cum_goals = 0
        cum_xg = 0.0
        cum_goals_against = 0
        cum_xg_against = 0.0

        for i, xg in enumerate(xg_records):
            is_home = xg.home_team in name_variants
            gf = xg.home_goals if is_home else xg.away_goals
            ga = xg.away_goals if is_home else xg.home_goals
            xgf = xg.home_xg if is_home else xg.away_xg
            xga = xg.away_xg if is_home else xg.home_xg
            opponent = xg.away_team if is_home else xg.home_team

            cum_goals += gf
            cum_xg += xgf
            cum_goals_against += ga
            cum_xg_against += xga

            timeline.append({
                'matchday': i + 1,
                'date': xg.date,
                'opponent': opponent,
                'is_home': is_home,
                'goals_for': gf,
                'goals_against': ga,
                'xg_for': round(xgf, 2),
                'xg_against': round(xga, 2),
                'cumulative_goals': cum_goals,
                'cumulative_xg': round(cum_xg, 2),
                'cumulative_goals_against': cum_goals_against,
                'cumulative_xg_against': round(cum_xg_against, 2)
            })

        return {
            'team': FootballTeamResponse.model_validate(team),
            'season': season,
            'timeline': timeline
        }

    async def get_team_vs_league(
        self,
        team_id: int,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Compare a team against league averages."""
        if season is None:
            season = settings.current_season

        team_result = await db.execute(
            select(FootballTeam).where(FootballTeam.id == team_id)
        )
        team = team_result.scalar_one_or_none()
        if not team:
            return None

        # Get all finished fixtures for the season
        fixtures_query = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        ).where(
            and_(
                FootballFixture.season == season,
                FootballFixture.status == "FINISHED"
            )
        )
        fix_result = await db.execute(fixtures_query)
        all_fixtures = list(fix_result.scalars().all())

        # Compute per-team stats
        team_stats: Dict[str, Dict[str, Any]] = {}
        for f in all_fixtures:
            if f.home_score is None or f.away_score is None:
                continue
            for is_home in [True, False]:
                t_name = f.home_team.name if is_home else f.away_team.name
                if t_name not in team_stats:
                    team_stats[t_name] = {'played': 0, 'won': 0, 'gf': 0, 'ga': 0}
                ts = team_stats[t_name]
                ts['played'] += 1
                gf = f.home_score if is_home else f.away_score
                ga = f.away_score if is_home else f.home_score
                ts['gf'] += gf
                ts['ga'] += ga
                if gf > ga:
                    ts['won'] += 1

        if not team_stats:
            return None

        # League averages
        total_teams = len(team_stats)
        league_avg = {
            'ppg': 0.0, 'gf_per_game': 0.0, 'ga_per_game': 0.0, 'win_pct': 0.0
        }
        for ts in team_stats.values():
            if ts['played'] > 0:
                league_avg['ppg'] += ts['gf']  # temp accumulator
                league_avg['gf_per_game'] += ts['gf'] / ts['played']
                league_avg['ga_per_game'] += ts['ga'] / ts['played']
                league_avg['win_pct'] += (ts['won'] / ts['played']) * 100

        for key in league_avg:
            league_avg[key] = round(league_avg[key] / total_teams, 2) if total_teams > 0 else 0.0

        # Recalculate league PPG properly
        total_points = sum(ts['won'] * 3 for ts in team_stats.values())  # simplified
        total_games = sum(ts['played'] for ts in team_stats.values())
        # Each game produces total points for both teams; approximate PPG from wins
        # Better: compute from standings
        standings = await self.get_standings(db, season)
        if standings:
            avg_ppg = round(sum(s.points_per_game for s in standings) / len(standings), 2)
        else:
            avg_ppg = round(1.5, 2)  # ~league average
        league_avg['ppg'] = avg_ppg

        # Team-specific stats
        my_stats = team_stats.get(team.name, {'played': 0, 'won': 0, 'gf': 0, 'ga': 0})
        p = my_stats['played'] or 1
        my_standing = next((s for s in standings if s.team.name == team.name), None)
        my_ppg = my_standing.points_per_game if my_standing else 0.0

        # xG data if available
        xg_analysis = await self.get_team_xg_analysis(team_id, db, season)
        my_xgf_pg = xg_analysis.get('xg_per_game', 0.0) if xg_analysis else 0.0
        my_xga_pg = xg_analysis.get('xa_per_game', 0.0) if xg_analysis else 0.0

        # League xG averages
        xg_standings = await self.get_xg_standings(db, season)
        if xg_standings:
            total_xg_matches = sum(t['matches'] for t in xg_standings)
            total_xg_for = sum(t['xg_for'] for t in xg_standings)
            total_xg_against = sum(t['xg_against'] for t in xg_standings)
            n_xg_teams = len(xg_standings)
            league_xgf_pg = round(total_xg_for / total_xg_matches, 2) if total_xg_matches > 0 else 0.0
            league_xga_pg = round(total_xg_against / total_xg_matches, 2) if total_xg_matches > 0 else 0.0
        else:
            league_xgf_pg = 0.0
            league_xga_pg = 0.0

        metrics = [
            {'metric': 'Points Per Game', 'team_value': my_ppg, 'league_value': league_avg['ppg'],
             'difference': round(my_ppg - league_avg['ppg'], 2)},
            {'metric': 'Goals For / Game', 'team_value': round(my_stats['gf'] / p, 2),
             'league_value': league_avg['gf_per_game'],
             'difference': round(my_stats['gf'] / p - league_avg['gf_per_game'], 2)},
            {'metric': 'Goals Against / Game', 'team_value': round(my_stats['ga'] / p, 2),
             'league_value': league_avg['ga_per_game'],
             'difference': round(my_stats['ga'] / p - league_avg['ga_per_game'], 2)},
            {'metric': 'Win %', 'team_value': round((my_stats['won'] / p) * 100, 1),
             'league_value': league_avg['win_pct'],
             'difference': round((my_stats['won'] / p) * 100 - league_avg['win_pct'], 1)},
            {'metric': 'xG For / Game', 'team_value': my_xgf_pg, 'league_value': league_xgf_pg,
             'difference': round(my_xgf_pg - league_xgf_pg, 2)},
            {'metric': 'xG Against / Game', 'team_value': my_xga_pg, 'league_value': league_xga_pg,
             'difference': round(my_xga_pg - league_xga_pg, 2)},
        ]

        return {
            'team': FootballTeamResponse.model_validate(team),
            'season': season,
            'metrics': metrics
        }

    async def get_player_stats(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        sort_by: str = 'goals',
        order: str = 'desc',
        limit: int = 50,
        team_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get player statistics with sorting, filtering, and search."""
        if season is None:
            season = settings.current_season

        from .models import FootballPlayerStats

        query = select(FootballPlayerStats).where(
            FootballPlayerStats.season == season
        )

        if team_filter:
            query = query.where(FootballPlayerStats.team_name.ilike(f"%{team_filter}%"))
        if search:
            query = query.where(FootballPlayerStats.name.ilike(f"%{search}%"))

        # Dynamic sort
        valid_sort_fields = {
            'name': FootballPlayerStats.name,
            'team_name': FootballPlayerStats.team_name,
            'games': FootballPlayerStats.games,
            'minutes': FootballPlayerStats.minutes,
            'goals': FootballPlayerStats.goals,
            'assists': FootballPlayerStats.assists,
            'shots': FootballPlayerStats.shots,
            'key_passes': FootballPlayerStats.key_passes,
            'xg': FootballPlayerStats.xg,
            'xa': FootballPlayerStats.xa,
            'npg': FootballPlayerStats.npg,
            'npxg': FootballPlayerStats.npxg,
            'xg_per_90': FootballPlayerStats.xg_per_90,
            'goals_minus_xg': FootballPlayerStats.goals_minus_xg,
        }
        sort_col = valid_sort_fields.get(sort_by, FootballPlayerStats.goals)
        if order == 'asc':
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        query = query.limit(limit)

        result = await db.execute(query)
        players = list(result.scalars().all())

        return players

    async def get_player_detail(
        self,
        player_id: int,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> Optional[Any]:
        """Get a single player's detail."""
        from .models import FootballPlayerStats

        query = select(FootballPlayerStats).where(
            FootballPlayerStats.id == player_id
        )
        if season:
            query = query.where(FootballPlayerStats.season == season)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_advanced_team_stats(
        self,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> List[Any]:
        """Get advanced team stats from FBref data."""
        if season is None:
            season = settings.current_season

        from .models import FootballAdvancedTeamStats

        query = select(FootballAdvancedTeamStats).where(
            FootballAdvancedTeamStats.season == season
        ).order_by(FootballAdvancedTeamStats.team_name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_advanced_player_stats(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        sort_by: str = 'progressive_passes',
        team_filter: Optional[str] = None,
        search: Optional[str] = None,
        position_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[Any]:
        """Get advanced player stats from FBref data."""
        if season is None:
            season = settings.current_season

        from .models import FootballAdvancedPlayerStats

        query = select(FootballAdvancedPlayerStats).where(
            FootballAdvancedPlayerStats.season == season
        )

        if team_filter:
            query = query.where(FootballAdvancedPlayerStats.team_name.ilike(f"%{team_filter}%"))
        if search:
            query = query.where(FootballAdvancedPlayerStats.player_name.ilike(f"%{search}%"))
        if position_filter:
            query = query.where(FootballAdvancedPlayerStats.position.ilike(f"%{position_filter}%"))

        valid_sort_fields = {
            'progressive_passes': FootballAdvancedPlayerStats.progressive_passes,
            'progressive_carries': FootballAdvancedPlayerStats.progressive_carries,
            'pressures': FootballAdvancedPlayerStats.pressures,
            'tackles': FootballAdvancedPlayerStats.tackles,
            'interceptions': FootballAdvancedPlayerStats.interceptions,
            'sca': FootballAdvancedPlayerStats.sca,
            'gca': FootballAdvancedPlayerStats.gca,
            'pass_completion_pct': FootballAdvancedPlayerStats.pass_completion_pct,
            'player_name': FootballAdvancedPlayerStats.player_name,
        }
        sort_col = valid_sort_fields.get(sort_by, FootballAdvancedPlayerStats.progressive_passes)
        query = query.order_by(sort_col.desc()).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    # ========== Phase 1: Team Ratings ==========

    async def calculate_team_ratings(
        self,
        db: AsyncSession,
        current_season: Optional[int] = None,
        seasons_back: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Calculate multi-season team ratings using exponential recency weighting.
        Rating = normalized(weighted sum of points + GD/10 across seasons).
        """
        if current_season is None:
            current_season = settings.current_season

        seasons = list(range(current_season - seasons_back, current_season + 1))

        # Get latest standings per team per season
        team_season_data: Dict[int, List[Dict[str, Any]]] = {}
        teams_info: Dict[int, Dict[str, str]] = {}

        for season in seasons:
            # Get latest matchday standings for this season
            latest_md_q = select(func.max(FootballStanding.matchday)).where(
                FootballStanding.season == season
            )
            latest_md_result = await db.execute(latest_md_q)
            latest_md = latest_md_result.scalar()
            if not latest_md:
                continue

            standings_q = select(FootballStanding).options(
                selectinload(FootballStanding.team)
            ).where(
                and_(
                    FootballStanding.season == season,
                    FootballStanding.matchday == latest_md
                )
            )
            standings_result = await db.execute(standings_q)
            standings = list(standings_result.scalars().all())

            age = current_season - season  # 0 for current season
            weight = 2.5 ** (seasons_back - age)

            for s in standings:
                # Skip current season if too few games
                if season == current_season and s.played < 4:
                    continue

                if s.team_id not in team_season_data:
                    team_season_data[s.team_id] = []
                if s.team_id not in teams_info:
                    teams_info[s.team_id] = {
                        'name': s.team.name,
                        'tla': s.team.tla
                    }

                score = s.points + s.goal_difference / 10.0
                team_season_data[s.team_id].append({
                    'score': score,
                    'weight': weight,
                    'season': season
                })

        # Calculate weighted scores
        raw_ratings: Dict[int, float] = {}
        seasons_counted: Dict[int, int] = {}
        for team_id, season_entries in team_season_data.items():
            total_weight = sum(e['weight'] for e in season_entries)
            if total_weight == 0:
                continue
            weighted_score = sum(e['score'] * e['weight'] for e in season_entries) / total_weight
            raw_ratings[team_id] = weighted_score
            seasons_counted[team_id] = len(season_entries)

        if not raw_ratings:
            return []

        # Min/max normalize to 0-1
        min_rating = min(raw_ratings.values())
        max_rating = max(raw_ratings.values())
        rating_range = max_rating - min_rating

        ratings = []
        for team_id, raw in raw_ratings.items():
            normalized = (raw - min_rating) / rating_range if rating_range > 0 else 0.5
            ratings.append({
                'team_id': team_id,
                'team_name': teams_info[team_id]['name'],
                'tla': teams_info[team_id]['tla'],
                'rating': round(normalized, 4),
                'seasons_analyzed': seasons_counted[team_id]
            })

        # Upsert into DB
        for r in ratings:
            existing_q = select(FootballTeamRating).where(
                and_(
                    FootballTeamRating.team_id == r['team_id'],
                    FootballTeamRating.season == current_season
                )
            )
            existing_result = await db.execute(existing_q)
            existing = existing_result.scalar_one_or_none()

            if existing:
                existing.rating = r['rating']
                existing.seasons_analyzed = r['seasons_analyzed']
            else:
                db.add(FootballTeamRating(
                    team_id=r['team_id'],
                    season=current_season,
                    rating=r['rating'],
                    seasons_analyzed=r['seasons_analyzed']
                ))

        await db.commit()

        ratings.sort(key=lambda x: x['rating'], reverse=True)
        return ratings

    async def get_team_ratings(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        recalculate: bool = False
    ) -> List[Dict[str, Any]]:
        """Get team ratings, optionally recalculating."""
        if season is None:
            season = settings.current_season

        if recalculate:
            return await self.calculate_team_ratings(db, season)

        # Try to load from DB
        query = select(FootballTeamRating).options(
            selectinload(FootballTeamRating.team)
        ).where(FootballTeamRating.season == season)

        result = await db.execute(query)
        existing = list(result.scalars().all())

        if not existing:
            return await self.calculate_team_ratings(db, season)

        ratings = []
        for r in existing:
            ratings.append({
                'team_id': r.team_id,
                'team_name': r.team.name,
                'tla': r.team.tla,
                'rating': r.rating,
                'seasons_analyzed': r.seasons_analyzed
            })

        ratings.sort(key=lambda x: x['rating'], reverse=True)
        return ratings

    # ========== Phase 2: Opponent-Adjusted Form ==========

    async def get_opponent_adjusted_form(
        self,
        team_id: int,
        db: AsyncSession,
        games: int = 10,
        season: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate opponent-adjusted form rating.
        Accounts for opponent strength in form calculation.
        """
        if season is None:
            season = settings.current_season

        team_result = await db.execute(
            select(FootballTeam).where(FootballTeam.id == team_id)
        )
        team = team_result.scalar_one_or_none()
        if not team:
            return None

        # Get recent finished fixtures
        fixtures_q = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        ).where(
            and_(
                or_(
                    FootballFixture.home_team_id == team_id,
                    FootballFixture.away_team_id == team_id
                ),
                FootballFixture.status == "FINISHED",
                FootballFixture.season == season
            )
        ).order_by(desc(FootballFixture.utc_date)).limit(games)

        fix_result = await db.execute(fixtures_q)
        recent_fixtures = list(fix_result.scalars().all())

        # Get team ratings for opponents
        ratings_map = {}
        all_ratings = await self.get_team_ratings(db, season)
        for r in all_ratings:
            ratings_map[r['team_id']] = r['rating']

        breakdown = []
        form_string = ""

        for i, fixture in enumerate(reversed(recent_fixtures)):
            is_home = fixture.home_team_id == team_id
            opponent_id = fixture.away_team_id if is_home else fixture.home_team_id
            opponent_name = fixture.away_team.name if is_home else fixture.home_team.name
            opp_rating = ratings_map.get(opponent_id, 0.5)

            team_score = fixture.home_score if is_home else fixture.away_score
            opp_score = fixture.away_score if is_home else fixture.home_score

            if team_score is None or opp_score is None:
                continue

            recency_weight = 1.2 ** (len(recent_fixtures) - 1 - i)

            if team_score > opp_score:
                result_char = "W"
                contribution = opp_rating * 0.5 * recency_weight
            elif team_score == opp_score:
                result_char = "D"
                contribution = opp_rating * 0.15 * recency_weight
            else:
                result_char = "L"
                contribution = -opp_rating * 0.35 * recency_weight

            form_string += result_char
            breakdown.append({
                'opponent': opponent_name,
                'result': result_char,
                'opponent_rating': round(opp_rating, 4),
                'contribution': round(contribution, 4),
                'is_home': is_home
            })

        # Calculate form ratings
        def calc_form_rating(entries):
            if not entries:
                return 0.5
            base = 0.5
            total_weight = sum(abs(e['contribution']) for e in entries)
            adjustment = sum(e['contribution'] for e in entries)
            max_possible = len(entries) * 0.5  # max contribution per match
            if max_possible > 0:
                rating = base + (adjustment / max_possible) * 0.5
            else:
                rating = base
            return max(0.0, min(1.0, round(rating, 4)))

        form_rating_5 = calc_form_rating(breakdown[-5:] if len(breakdown) >= 5 else breakdown)
        form_rating_10 = calc_form_rating(breakdown)

        return {
            'team': FootballTeamResponse.model_validate(team),
            'form_rating_5': form_rating_5,
            'form_rating_10': form_rating_10,
            'form_string': form_string,
            'breakdown': breakdown
        }

    # ========== Phase 3a: Fixture Difficulty ==========

    async def get_fixture_difficulty(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        rating_mode: str = "team_rating"
    ) -> Dict[str, Any]:
        """Get fixture difficulty heatmap data for all teams."""
        if season is None:
            season = settings.current_season

        # Get team ratings
        ratings_map = {}
        all_ratings = await self.get_team_ratings(db, season)
        for r in all_ratings:
            ratings_map[r['team_id']] = r['rating']

        # Get all teams
        teams_q = select(FootballTeam).order_by(FootballTeam.name)
        teams_result = await db.execute(teams_q)
        all_teams = list(teams_result.scalars().all())
        team_info = {t.id: {'name': t.name, 'tla': t.tla} for t in all_teams}

        # Get all fixtures for the season
        fix_q = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        ).where(
            FootballFixture.season == season
        ).order_by(FootballFixture.matchday)

        fix_result = await db.execute(fix_q)
        all_fixtures = list(fix_result.scalars().all())

        # Build per-team fixture difficulty
        team_difficulties: Dict[int, List[Dict[str, Any]]] = {t.id: [] for t in all_teams}

        for fixture in all_fixtures:
            # Home team entry
            opp_id_for_home = fixture.away_team_id
            opp_rating_home = ratings_map.get(opp_id_for_home, 0.5)

            result_home = None
            if fixture.status == "FINISHED" and fixture.home_score is not None:
                if fixture.home_score > fixture.away_score:
                    result_home = "W"
                elif fixture.home_score < fixture.away_score:
                    result_home = "L"
                else:
                    result_home = "D"

            if fixture.home_team_id in team_difficulties:
                team_difficulties[fixture.home_team_id].append({
                    'matchday': fixture.matchday,
                    'opponent_short': team_info.get(opp_id_for_home, {}).get('tla', '???'),
                    'is_home': True,
                    'difficulty': round(opp_rating_home, 4),
                    'status': fixture.status,
                    'result': result_home
                })

            # Away team entry
            opp_id_for_away = fixture.home_team_id
            opp_rating_away = ratings_map.get(opp_id_for_away, 0.5)

            result_away = None
            if fixture.status == "FINISHED" and fixture.home_score is not None:
                if fixture.away_score > fixture.home_score:
                    result_away = "W"
                elif fixture.away_score < fixture.home_score:
                    result_away = "L"
                else:
                    result_away = "D"

            if fixture.away_team_id in team_difficulties:
                team_difficulties[fixture.away_team_id].append({
                    'matchday': fixture.matchday,
                    'opponent_short': team_info.get(opp_id_for_away, {}).get('tla', '???'),
                    'is_home': False,
                    'difficulty': round(opp_rating_away, 4),
                    'status': fixture.status,
                    'result': result_away
                })

        teams_data = []
        for team_id, fixtures in team_difficulties.items():
            if not fixtures:
                continue
            info = team_info.get(team_id, {'name': 'Unknown', 'tla': '???'})
            fixtures.sort(key=lambda x: x['matchday'])
            teams_data.append({
                'team_name': info['name'],
                'tla': info['tla'],
                'team_id': team_id,
                'fixtures': fixtures
            })

        teams_data.sort(key=lambda x: x['team_name'])

        return {
            'teams': teams_data,
            'season': season,
            'rating_mode': rating_mode
        }

    # ========== Phase 3b: Position Progression ==========

    async def get_position_progression(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        team_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Get league position evolution by matchday."""
        if season is None:
            season = settings.current_season

        query = select(FootballStanding).options(
            selectinload(FootballStanding.team)
        ).where(
            FootballStanding.season == season
        ).order_by(FootballStanding.matchday, FootballStanding.position)

        result = await db.execute(query)
        all_standings = list(result.scalars().all())

        matchdays_set: set = set()
        team_positions: Dict[int, Dict[int, int]] = {}
        team_names: Dict[int, str] = {}

        for s in all_standings:
            if team_ids and s.team_id not in team_ids:
                continue
            matchdays_set.add(s.matchday)
            if s.team_id not in team_positions:
                team_positions[s.team_id] = {}
                team_names[s.team_id] = s.team.name
            team_positions[s.team_id][s.matchday] = s.position

        matchdays = sorted(matchdays_set)

        teams = []
        for team_id, positions_dict in team_positions.items():
            positions = [positions_dict.get(md) for md in matchdays]
            teams.append({
                'team_name': team_names[team_id],
                'team_id': team_id,
                'positions': positions
            })

        return {
            'matchdays': matchdays,
            'teams': teams,
            'season': season
        }

    # ========== Phase 4a: Scoreline Frequency ==========

    async def get_scoreline_frequency(
        self,
        team_id: int,
        db: AsyncSession,
        seasons_back: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Get most common scorelines for a team across seasons."""
        team_result = await db.execute(
            select(FootballTeam).where(FootballTeam.id == team_id)
        )
        team = team_result.scalar_one_or_none()
        if not team:
            return None

        current_season = settings.current_season
        min_season = current_season - seasons_back

        fix_q = select(FootballFixture).where(
            and_(
                or_(
                    FootballFixture.home_team_id == team_id,
                    FootballFixture.away_team_id == team_id
                ),
                FootballFixture.status == "FINISHED",
                FootballFixture.season >= min_season
            )
        )

        fix_result = await db.execute(fix_q)
        fixtures = list(fix_result.scalars().all())

        scoreline_counts: Dict[str, Dict[str, int]] = {}

        for f in fixtures:
            if f.home_score is None or f.away_score is None:
                continue

            is_home = f.home_team_id == team_id
            team_goals = f.home_score if is_home else f.away_score
            opp_goals = f.away_score if is_home else f.home_score
            scoreline = f"{team_goals}-{opp_goals}"

            if scoreline not in scoreline_counts:
                scoreline_counts[scoreline] = {'count': 0, 'wins': 0, 'draws': 0, 'losses': 0}

            scoreline_counts[scoreline]['count'] += 1
            if team_goals > opp_goals:
                scoreline_counts[scoreline]['wins'] += 1
            elif team_goals < opp_goals:
                scoreline_counts[scoreline]['losses'] += 1
            else:
                scoreline_counts[scoreline]['draws'] += 1

        scorelines = sorted(
            [{'scoreline': k, **v} for k, v in scoreline_counts.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:15]

        return {
            'team_name': team.name,
            'team_id': team.id,
            'scorelines': scorelines,
            'seasons_analyzed': min(seasons_back + 1, len(set(f.season for f in fixtures)))
        }

    # ========== Phase 4b: Multi-Season Home Advantage ==========

    async def get_home_advantage_multi_season(
        self,
        db: AsyncSession,
        current_season: Optional[int] = None,
        seasons_back: int = 3
    ) -> Dict[str, Any]:
        """Get per-team home advantage averaged across multiple seasons."""
        if current_season is None:
            current_season = settings.current_season

        min_season = current_season - seasons_back
        excluded_seasons = {2020}  # Pandemic season

        fix_q = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        ).where(
            and_(
                FootballFixture.status == "FINISHED",
                FootballFixture.season >= min_season,
                FootballFixture.season <= current_season
            )
        )

        fix_result = await db.execute(fix_q)
        all_fixtures = list(fix_result.scalars().all())

        # Per team per season stats
        team_season_stats: Dict[str, Dict[int, Dict[str, Any]]] = {}

        for f in all_fixtures:
            if f.home_score is None or f.away_score is None:
                continue
            if f.season in excluded_seasons:
                continue

            h_name = f.home_team.name
            a_name = f.away_team.name

            for name in (h_name, a_name):
                if name not in team_season_stats:
                    team_season_stats[name] = {}
                if f.season not in team_season_stats[name]:
                    team_season_stats[name][f.season] = {
                        'home_played': 0, 'home_pts': 0,
                        'away_played': 0, 'away_pts': 0
                    }

            s = team_season_stats[h_name][f.season]
            s['home_played'] += 1
            if f.home_score > f.away_score:
                s['home_pts'] += 3
            elif f.home_score == f.away_score:
                s['home_pts'] += 1

            s = team_season_stats[a_name][f.season]
            s['away_played'] += 1
            if f.away_score > f.home_score:
                s['away_pts'] += 3
            elif f.away_score == f.home_score:
                s['away_pts'] += 1

        result_list = []
        for team_name, seasons_data in team_season_stats.items():
            valid_seasons = []
            for season_yr, stats in seasons_data.items():
                if season_yr == current_season and stats['home_played'] < 6:
                    continue
                if stats['home_played'] > 0 and stats['away_played'] > 0:
                    home_ppg = stats['home_pts'] / stats['home_played']
                    away_ppg = stats['away_pts'] / stats['away_played']
                    valid_seasons.append({
                        'home_ppg': home_ppg,
                        'away_ppg': away_ppg
                    })

            if not valid_seasons:
                continue

            avg_home_ppg = sum(s['home_ppg'] for s in valid_seasons) / len(valid_seasons)
            avg_away_ppg = sum(s['away_ppg'] for s in valid_seasons) / len(valid_seasons)

            result_list.append({
                'team': team_name,
                'home_advantage': round(avg_home_ppg - avg_away_ppg, 4),
                'avg_home_ppg': round(avg_home_ppg, 4),
                'avg_away_ppg': round(avg_away_ppg, 4),
                'seasons_analyzed': len(valid_seasons)
            })

        result_list.sort(key=lambda x: x['home_advantage'], reverse=True)

        return {
            'teams': result_list,
            'current_season': current_season,
            'seasons_back': seasons_back
        }

    # ========== Phase 5a: Prediction Tracking ==========

    async def store_prediction(
        self,
        db: AsyncSession,
        fixture_id: int,
        predicted_home_score: float,
        predicted_away_score: float,
        home_win_prob: float,
        draw_prob: float,
        away_win_prob: float,
        model_name: str = "poisson"
    ) -> Dict[str, Any]:
        """Store a match prediction for later accuracy tracking."""
        fix_result = await db.execute(
            select(FootballFixture).where(FootballFixture.id == fixture_id)
        )
        fixture = fix_result.scalar_one_or_none()
        if not fixture:
            return {'error': f'Fixture {fixture_id} not found'}

        existing_q = select(FootballPredictionRecord).where(
            and_(
                FootballPredictionRecord.fixture_id == fixture_id,
                FootballPredictionRecord.model_name == model_name
            )
        )
        existing_result = await db.execute(existing_q)
        existing = existing_result.scalar_one_or_none()

        if existing:
            existing.predicted_home_score = predicted_home_score
            existing.predicted_away_score = predicted_away_score
            existing.home_win_prob = home_win_prob
            existing.draw_prob = draw_prob
            existing.away_win_prob = away_win_prob
        else:
            record = FootballPredictionRecord(
                fixture_id=fixture_id,
                season=fixture.season,
                predicted_home_score=predicted_home_score,
                predicted_away_score=predicted_away_score,
                home_win_prob=home_win_prob,
                draw_prob=draw_prob,
                away_win_prob=away_win_prob,
                model_name=model_name
            )
            db.add(record)

        await db.commit()
        return {'stored': True, 'fixture_id': fixture_id}

    async def update_prediction_results(
        self,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> Dict[str, Any]:
        """Batch-update prediction records with actual results."""
        if season is None:
            season = settings.current_season

        query = select(FootballPredictionRecord).options(
            selectinload(FootballPredictionRecord.fixture)
        ).where(
            and_(
                FootballPredictionRecord.season == season,
                FootballPredictionRecord.outcome_correct.is_(None)
            )
        )

        result = await db.execute(query)
        records = list(result.scalars().all())

        updated = 0
        for record in records:
            fixture = record.fixture
            if fixture.status != "FINISHED" or fixture.home_score is None:
                continue

            record.actual_home_score = fixture.home_score
            record.actual_away_score = fixture.away_score

            if record.home_win_prob > record.draw_prob and record.home_win_prob > record.away_win_prob:
                pred_outcome = "HOME"
            elif record.away_win_prob > record.draw_prob:
                pred_outcome = "AWAY"
            else:
                pred_outcome = "DRAW"

            if fixture.home_score > fixture.away_score:
                actual_outcome = "HOME"
            elif fixture.away_score > fixture.home_score:
                actual_outcome = "AWAY"
            else:
                actual_outcome = "DRAW"

            record.outcome_correct = pred_outcome == actual_outcome

            pred_h = round(record.predicted_home_score)
            pred_a = round(record.predicted_away_score)
            record.score_correct = (pred_h == fixture.home_score and pred_a == fixture.away_score)
            record.score_error = abs(fixture.home_score - record.predicted_home_score) + \
                                 abs(fixture.away_score - record.predicted_away_score)
            updated += 1

        await db.commit()
        return {'updated': updated}

    async def get_prediction_accuracy(
        self,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get prediction accuracy statistics."""
        if season is None:
            season = settings.current_season

        query = select(FootballPredictionRecord).where(
            FootballPredictionRecord.season == season
        )
        result = await db.execute(query)
        records = list(result.scalars().all())

        total = len(records)
        evaluated = [r for r in records if r.outcome_correct is not None]
        n_eval = len(evaluated)

        if n_eval == 0:
            return {
                'total': total, 'evaluated': 0,
                'outcome_accuracy': 0.0, 'score_accuracy': 0.0,
                'avg_error': 0.0, 'by_month': []
            }

        outcome_correct = sum(1 for r in evaluated if r.outcome_correct)
        score_correct = sum(1 for r in evaluated if r.score_correct)
        avg_error = sum(r.score_error for r in evaluated if r.score_error is not None) / n_eval

        return {
            'total': total,
            'evaluated': n_eval,
            'outcome_accuracy': round(outcome_correct / n_eval * 100, 1),
            'score_accuracy': round(score_correct / n_eval * 100, 1),
            'avg_error': round(avg_error, 2),
            'by_month': []
        }

    async def get_prediction_history(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        limit: int = 20
    ) -> List[Any]:
        """Get recent prediction records."""
        if season is None:
            season = settings.current_season

        query = select(FootballPredictionRecord).where(
            FootballPredictionRecord.season == season
        ).order_by(desc(FootballPredictionRecord.id)).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    # ========== Phase 5c: Upcoming Fixtures ==========

    async def get_upcoming_fixtures(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        include_predictions: bool = False
    ) -> Dict[str, Any]:
        """Get next matchday fixtures with optional predictions."""
        if season is None:
            season = settings.current_season

        fix_q = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        ).where(
            and_(
                FootballFixture.season == season,
                FootballFixture.status == "SCHEDULED"
            )
        ).order_by(FootballFixture.utc_date).limit(20)

        fix_result = await db.execute(fix_q)
        scheduled = list(fix_result.scalars().all())

        if not scheduled:
            return {
                'next_matchday': None,
                'fixtures': [],
                'season': season
            }

        next_matchday = scheduled[0].matchday
        matchday_fixtures = [f for f in scheduled if f.matchday == next_matchday]

        fixtures_data = []
        for fixture in matchday_fixtures:
            fixture_resp = FootballFixtureResponse.model_validate(fixture)
            prediction = None

            if include_predictions:
                try:
                    from .predictions import predict_match_outcome
                    pred = await predict_match_outcome(
                        fixture.home_team.name, fixture.away_team.name, db, season
                    )
                    if 'error' not in pred:
                        prediction = pred.get('predictions')
                except Exception:
                    pass

            fixtures_data.append({
                'fixture': fixture_resp,
                'prediction': prediction
            })

        return {
            'next_matchday': next_matchday,
            'fixtures': fixtures_data,
            'season': season
        }
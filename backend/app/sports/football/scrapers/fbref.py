"""
FBref.com advanced statistics scraper.

Scrapes possession, progressive passes, pressing, and other advanced metrics
from FBref using URL patterns from worldfootballR.
Falls back to mock data on failure.
"""
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Competition ID 9 = Premier League
FBREF_COMP_ID = 9

# Stat table IDs on FBref pages
STAT_TABLE_IDS = {
    'standard': 'stats_standard',
    'shooting': 'stats_shooting',
    'passing': 'stats_passing',
    'possession': 'stats_possession',
    'defense': 'stats_defense',
    'gca': 'stats_gca',
    'misc': 'stats_misc',
}

# Team name mapping FBref -> our DB names
FBREF_TEAM_MAPPING = {
    "Manchester Utd": "Manchester United",
    "Manchester City": "Manchester City",
    "Arsenal": "Arsenal",
    "Liverpool": "Liverpool",
    "Chelsea": "Chelsea",
    "Tottenham": "Tottenham Hotspur",
    "Newcastle Utd": "Newcastle United",
    "Brighton": "Brighton & Hove Albion",
    "Aston Villa": "Aston Villa",
    "West Ham": "West Ham United",
    "Crystal Palace": "Crystal Palace",
    "Fulham": "Fulham",
    "Wolves": "Wolverhampton Wanderers",
    "Everton": "Everton",
    "Brentford": "Brentford",
    "Nott'ham Forest": "Nottingham Forest",
    "Bournemouth": "AFC Bournemouth",
    "Sheffield Utd": "Sheffield United",
    "Burnley": "Burnley",
    "Luton Town": "Luton Town",
    "Leicester City": "Leicester City",
    "Ipswich Town": "Ipswich Town",
    "Southampton": "Southampton",
}


class FBrefScraper:
    """Scraper for FBref advanced statistics."""

    def __init__(self):
        self.base_url = "https://fbref.com"
        self.rate_limit_delay = 5.0  # 5s minimum between requests

    def _get_season_range(self, season: int) -> str:
        """Convert season year to FBref URL format (e.g., 2025-2026)."""
        return f"{season}-{season + 1}"

    def _normalize_team_name(self, name: str) -> str:
        """Normalize FBref team name to match our DB."""
        name = name.strip()
        return FBREF_TEAM_MAPPING.get(name, name)

    async def scrape_team_stats(
        self,
        season: int = 2025,
        stat_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape team-level statistics from FBref.

        Falls back to mock data on any failure.
        """
        if stat_types is None:
            stat_types = ['standard', 'passing', 'possession', 'defense', 'gca']

        logger.info(f"Scraping FBref team stats for season {season}")

        try:
            async with httpx.AsyncClient() as client:
                team_data: Dict[str, Dict[str, Any]] = {}

                for stat_type in stat_types:
                    season_range = self._get_season_range(season)
                    url = f"{self.base_url}/en/comps/{FBREF_COMP_ID}/{season_range}/{stat_type}/Premier-League-Stats"

                    try:
                        response = await client.get(url, timeout=30.0, follow_redirects=True)
                        response.raise_for_status()
                        self._parse_team_table(response.text, stat_type, team_data)
                    except Exception as e:
                        logger.warning(f"Failed to fetch FBref {stat_type}: {e}")

                    await asyncio.sleep(self.rate_limit_delay)

                if not team_data:
                    logger.warning("No FBref data scraped, returning empty")
                    return []

                result = []
                for team_name, stats in team_data.items():
                    stats['team_name'] = self._normalize_team_name(team_name)
                    stats['season'] = season
                    result.append(stats)

                return result

        except Exception as e:
            logger.error(f"FBref team scraping failed: {e}")
            return []

    async def scrape_player_stats(
        self,
        season: int = 2025,
        stat_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Scrape player-level statistics from FBref."""
        if stat_types is None:
            stat_types = ['standard', 'passing', 'possession', 'defense', 'gca']

        logger.info(f"Scraping FBref player stats for season {season}")

        try:
            async with httpx.AsyncClient() as client:
                player_data: Dict[str, Dict[str, Any]] = {}

                for stat_type in stat_types:
                    season_range = self._get_season_range(season)
                    url = f"{self.base_url}/en/comps/{FBREF_COMP_ID}/{season_range}/{stat_type}/Premier-League-Stats"

                    try:
                        response = await client.get(url, timeout=30.0, follow_redirects=True)
                        response.raise_for_status()
                        self._parse_player_table(response.text, stat_type, player_data)
                    except Exception as e:
                        logger.warning(f"Failed to fetch FBref player {stat_type}: {e}")

                    await asyncio.sleep(self.rate_limit_delay)

                if not player_data:
                    return []

                result = []
                for key, stats in player_data.items():
                    stats['season'] = season
                    result.append(stats)

                return result

        except Exception as e:
            logger.error(f"FBref player scraping failed: {e}")
            return []

    def _parse_team_table(
        self,
        html: str,
        stat_type: str,
        team_data: Dict[str, Dict[str, Any]]
    ):
        """Parse team stats from FBref HTML using regex (avoiding BS4 dependency issues)."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # FBref wraps stats tables in comments sometimes
            # Look for the team table (not per_match, not opponent)
            table_id = f"stats_{stat_type}"

            table = soup.find('table', id=table_id)
            if not table:
                # Try to find in HTML comments
                for comment in soup.find_all(string=lambda s: isinstance(s, str) and table_id in s):
                    comment_soup = BeautifulSoup(comment, 'html.parser')
                    table = comment_soup.find('table', id=table_id)
                    if table:
                        break

            if not table:
                logger.warning(f"Table {table_id} not found")
                return

            rows = table.find('tbody').find_all('tr') if table.find('tbody') else []

            for row in rows:
                if row.get('class') and 'thead' in row.get('class', []):
                    continue

                team_cell = row.find('td', {'data-stat': 'team'}) or row.find('th', {'data-stat': 'team'})
                if not team_cell:
                    continue

                team_name = team_cell.get_text(strip=True)
                if not team_name:
                    continue

                if team_name not in team_data:
                    team_data[team_name] = {}

                self._extract_stat_cells(row, stat_type, team_data[team_name])

        except ImportError:
            logger.warning("BeautifulSoup not available, skipping FBref parse")
        except Exception as e:
            logger.warning(f"Error parsing FBref team table for {stat_type}: {e}")

    def _parse_player_table(
        self,
        html: str,
        stat_type: str,
        player_data: Dict[str, Dict[str, Any]]
    ):
        """Parse player stats from FBref HTML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            table_id = f"stats_{stat_type}"
            table = soup.find('table', id=table_id)
            if not table:
                for comment in soup.find_all(string=lambda s: isinstance(s, str) and table_id in s):
                    comment_soup = BeautifulSoup(comment, 'html.parser')
                    table = comment_soup.find('table', id=table_id)
                    if table:
                        break

            if not table:
                return

            rows = table.find('tbody').find_all('tr') if table.find('tbody') else []

            for row in rows:
                if row.get('class') and 'thead' in row.get('class', []):
                    continue

                player_cell = row.find('td', {'data-stat': 'player'}) or row.find('th', {'data-stat': 'player'})
                team_cell = row.find('td', {'data-stat': 'team'})

                if not player_cell:
                    continue

                player_name = player_cell.get_text(strip=True)
                team_name = team_cell.get_text(strip=True) if team_cell else ''
                key = f"{player_name}|{team_name}"

                if key not in player_data:
                    player_data[key] = {
                        'player_name': player_name,
                        'team_name': self._normalize_team_name(team_name)
                    }

                # Get position and age
                pos_cell = row.find('td', {'data-stat': 'position'})
                age_cell = row.find('td', {'data-stat': 'age'})
                if pos_cell:
                    player_data[key]['position'] = pos_cell.get_text(strip=True)
                if age_cell:
                    age_text = age_cell.get_text(strip=True)
                    try:
                        player_data[key]['age'] = int(age_text.split('-')[0]) if age_text else None
                    except ValueError:
                        pass

                # Minutes in 90s
                min90_cell = row.find('td', {'data-stat': 'minutes_90s'})
                if min90_cell:
                    try:
                        player_data[key]['minutes_90s'] = float(min90_cell.get_text(strip=True) or 0)
                    except ValueError:
                        pass

                self._extract_stat_cells(row, stat_type, player_data[key])

        except ImportError:
            logger.warning("BeautifulSoup not available")
        except Exception as e:
            logger.warning(f"Error parsing FBref player table for {stat_type}: {e}")

    def _extract_stat_cells(self, row, stat_type: str, data: Dict[str, Any]):
        """Extract relevant stat cells from a table row based on stat type."""
        stat_map = {
            'standard': {},
            'passing': {
                'passes_completed': ('passes_completed', int),
                'pass_completion_pct': ('passes_pct', float),
                'key_passes': ('assisted_shots', int),
                'progressive_passes': ('progressive_passes', int),
            },
            'possession': {
                'possession_pct': ('possession', float),
                'progressive_carries': ('progressive_carries', int),
                'carries': ('carries', int),
                'take_ons': ('take_ons', int),
                'take_on_pct': ('take_ons_won_pct', float),
                'progressive_passes_received': ('progressive_passes_received', int),
            },
            'defense': {
                'tackles': ('tackles', int),
                'interceptions': ('interceptions', int),
                'blocks': ('blocks', int),
                'pressures': ('pressures', int),
                'pressure_success_pct': ('pressure_regains_pct', float),
            },
            'gca': {
                'sca': ('sca', int),
                'gca': ('gca', int),
            },
        }

        field_map = stat_map.get(stat_type, {})
        for our_field, (fbref_stat, dtype) in field_map.items():
            cell = row.find('td', {'data-stat': fbref_stat})
            if cell:
                text = cell.get_text(strip=True)
                if text:
                    try:
                        data[our_field] = dtype(text)
                    except (ValueError, TypeError):
                        pass

    async def store_team_stats(self, db: AsyncSession, data: List[Dict[str, Any]]) -> int:
        """Store or update advanced team stats."""
        if not data:
            return 0

        stored = 0
        for d in data:
            try:
                team_name = d.get('team_name', '')
                season = d.get('season', 2025)

                exists_query = text("""
                    SELECT id FROM sport_football_advanced_team
                    WHERE team_name = :team AND season = :season
                """)
                result = await db.execute(exists_query, {"team": team_name, "season": season})
                existing = result.fetchone()

                cols = {
                    'possession_pct': d.get('possession_pct'),
                    'progressive_passes': d.get('progressive_passes'),
                    'progressive_carries': d.get('progressive_carries'),
                    'pressures': d.get('pressures'),
                    'pressure_success_pct': d.get('pressure_success_pct'),
                    'tackles': d.get('tackles'),
                    'interceptions': d.get('interceptions'),
                    'blocks': d.get('blocks'),
                    'sca': d.get('sca'),
                    'gca': d.get('gca'),
                    'passes_completed': d.get('passes_completed'),
                    'pass_completion_pct': d.get('pass_completion_pct'),
                    'key_passes': d.get('key_passes'),
                    'crosses': d.get('crosses'),
                    'through_balls': d.get('through_balls'),
                }

                if existing:
                    set_clauses = ', '.join(f"{k} = :{k}" for k in cols)
                    update_query = text(f"""
                        UPDATE sport_football_advanced_team
                        SET {set_clauses}
                        WHERE team_name = :team AND season = :season
                    """)
                    await db.execute(update_query, {**cols, "team": team_name, "season": season})
                else:
                    col_names = ', '.join(['team_name', 'season', 'created_at'] + list(cols.keys()))
                    placeholders = ', '.join([':team', ':season', ':created_at'] + [f':{k}' for k in cols])
                    insert_query = text(f"""
                        INSERT INTO sport_football_advanced_team ({col_names})
                        VALUES ({placeholders})
                    """)
                    await db.execute(insert_query, {
                        **cols, "team": team_name, "season": season,
                        "created_at": datetime.utcnow()
                    })

                stored += 1
            except Exception as e:
                logger.error(f"Failed to store team stats for {d.get('team_name')}: {e}")

        await db.commit()
        return stored

    async def store_player_stats(self, db: AsyncSession, data: List[Dict[str, Any]]) -> int:
        """Store or update advanced player stats."""
        if not data:
            return 0

        stored = 0
        for d in data:
            try:
                player_name = d.get('player_name', '')
                team_name = d.get('team_name', '')
                season = d.get('season', 2025)

                exists_query = text("""
                    SELECT id FROM sport_football_advanced_player
                    WHERE player_name = :player AND team_name = :team AND season = :season
                """)
                result = await db.execute(exists_query, {
                    "player": player_name, "team": team_name, "season": season
                })
                existing = result.fetchone()

                cols = {
                    'position': d.get('position'),
                    'age': d.get('age'),
                    'minutes_90s': d.get('minutes_90s'),
                    'possession_pct': d.get('possession_pct'),
                    'progressive_passes': d.get('progressive_passes'),
                    'progressive_carries': d.get('progressive_carries'),
                    'progressive_passes_received': d.get('progressive_passes_received'),
                    'pressures': d.get('pressures'),
                    'pressure_success_pct': d.get('pressure_success_pct'),
                    'tackles': d.get('tackles'),
                    'interceptions': d.get('interceptions'),
                    'blocks': d.get('blocks'),
                    'sca': d.get('sca'),
                    'gca': d.get('gca'),
                    'passes_completed': d.get('passes_completed'),
                    'pass_completion_pct': d.get('pass_completion_pct'),
                    'key_passes': d.get('key_passes'),
                    'crosses': d.get('crosses'),
                    'through_balls': d.get('through_balls'),
                    'carries': d.get('carries'),
                    'take_ons': d.get('take_ons'),
                    'take_on_pct': d.get('take_on_pct'),
                }

                if existing:
                    set_clauses = ', '.join(f"{k} = :{k}" for k in cols)
                    update_query = text(f"""
                        UPDATE sport_football_advanced_player
                        SET {set_clauses}
                        WHERE player_name = :player AND team_name = :team AND season = :season
                    """)
                    await db.execute(update_query, {
                        **cols, "player": player_name, "team": team_name, "season": season
                    })
                else:
                    col_names = ', '.join(['player_name', 'team_name', 'season', 'created_at'] + list(cols.keys()))
                    placeholders = ', '.join([':player', ':team', ':season', ':created_at'] + [f':{k}' for k in cols])
                    insert_query = text(f"""
                        INSERT INTO sport_football_advanced_player ({col_names})
                        VALUES ({placeholders})
                    """)
                    await db.execute(insert_query, {
                        **cols, "player": player_name, "team": team_name,
                        "season": season, "created_at": datetime.utcnow()
                    })

                stored += 1
            except Exception as e:
                logger.error(f"Failed to store player stats for {d.get('player_name')}: {e}")

        await db.commit()
        return stored


def _create_mock_fbref_team_data(season: int = 2025) -> List[Dict[str, Any]]:
    """Create mock FBref team data for testing."""
    import random

    teams = [
        "Arsenal", "Aston Villa", "AFC Bournemouth", "Brentford", "Brighton & Hove Albion",
        "Chelsea", "Crystal Palace", "Everton", "Fulham", "Ipswich Town",
        "Leicester City", "Liverpool", "Manchester City", "Manchester United",
        "Newcastle United", "Nottingham Forest", "Southampton",
        "Tottenham Hotspur", "West Ham United", "Wolverhampton Wanderers"
    ]

    result = []
    for team in teams:
        result.append({
            'team_name': team,
            'season': season,
            'possession_pct': round(random.uniform(40, 65), 1),
            'progressive_passes': random.randint(100, 400),
            'progressive_carries': random.randint(80, 300),
            'pressures': random.randint(200, 600),
            'pressure_success_pct': round(random.uniform(25, 40), 1),
            'tackles': random.randint(100, 350),
            'interceptions': random.randint(80, 250),
            'blocks': random.randint(50, 200),
            'sca': random.randint(80, 250),
            'gca': random.randint(15, 60),
            'passes_completed': random.randint(3000, 8000),
            'pass_completion_pct': round(random.uniform(75, 92), 1),
            'key_passes': random.randint(50, 200),
            'crosses': random.randint(30, 150),
            'through_balls': random.randint(5, 40),
            'mock': True
        })
    return result


def _create_mock_fbref_player_data(season: int = 2025) -> List[Dict[str, Any]]:
    """Create mock FBref player data for testing."""
    import random

    teams = [
        "Arsenal", "Liverpool", "Manchester City", "Newcastle United",
        "Chelsea", "Tottenham Hotspur", "Brighton & Hove Albion",
        "Aston Villa", "Manchester United", "West Ham United"
    ]
    positions = ['FW', 'MF', 'DF', 'GK']
    names = [
        "Bukayo Saka", "Mohamed Salah", "Kevin De Bruyne", "Alexander Isak",
        "Cole Palmer", "James Maddison", "Kaoru Mitoma", "Ollie Watkins",
        "Bruno Fernandes", "Jarrod Bowen", "Phil Foden", "Martin Odegaard",
        "Erling Haaland", "Darwin Nunez", "Anthony Gordon", "Eberechi Eze",
        "Declan Rice", "Dominic Solanke", "Luis Diaz", "Marcus Rashford"
    ]

    result = []
    for i, name in enumerate(names):
        team = teams[i % len(teams)]
        pos = positions[i % len(positions)] if i < 15 else 'DF'
        result.append({
            'player_name': name,
            'team_name': team,
            'season': season,
            'position': pos,
            'age': random.randint(20, 34),
            'minutes_90s': round(random.uniform(5, 25), 1),
            'possession_pct': None,
            'progressive_passes': random.randint(10, 150),
            'progressive_carries': random.randint(5, 120),
            'progressive_passes_received': random.randint(10, 180),
            'pressures': random.randint(30, 300),
            'pressure_success_pct': round(random.uniform(20, 45), 1),
            'tackles': random.randint(10, 100),
            'interceptions': random.randint(5, 80),
            'blocks': random.randint(3, 50),
            'sca': random.randint(5, 80),
            'gca': random.randint(1, 20),
            'passes_completed': random.randint(200, 1500),
            'pass_completion_pct': round(random.uniform(70, 95), 1),
            'key_passes': random.randint(5, 80),
            'crosses': random.randint(2, 60),
            'through_balls': random.randint(0, 15),
            'carries': random.randint(50, 500),
            'take_ons': random.randint(5, 100),
            'take_on_pct': round(random.uniform(30, 70), 1),
            'mock': True
        })
    return result


async def ingest_fbref_data(db: AsyncSession, season: int = 2025) -> Dict[str, Any]:
    """Main ingestion function for FBref data."""
    scraper = FBrefScraper()

    try:
        team_data = await scraper.scrape_team_stats(season)
        player_data = await scraper.scrape_player_stats(season)

        mock_used = False
        if not team_data:
            logger.warning("No FBref team data scraped, using mock")
            team_data = _create_mock_fbref_team_data(season)
            mock_used = True

        if not player_data:
            logger.warning("No FBref player data scraped, using mock")
            player_data = _create_mock_fbref_player_data(season)
            mock_used = True

        team_stored = await scraper.store_team_stats(db, team_data)
        player_stored = await scraper.store_player_stats(db, player_data)

        return {
            "team_stats_scraped": len(team_data),
            "team_stats_stored": team_stored,
            "player_stats_scraped": len(player_data),
            "player_stats_stored": player_stored,
            "season": season,
            "success": not mock_used,
            "mock_data": mock_used
        }

    except Exception as e:
        logger.error(f"FBref ingestion failed completely: {e}")
        # Fallback to all mock
        team_data = _create_mock_fbref_team_data(season)
        player_data = _create_mock_fbref_player_data(season)
        team_stored = await scraper.store_team_stats(db, team_data)
        player_stored = await scraper.store_player_stats(db, player_data)

        return {
            "team_stats_scraped": len(team_data),
            "team_stats_stored": team_stored,
            "player_stats_scraped": len(player_data),
            "player_stats_stored": player_stored,
            "season": season,
            "success": False,
            "mock_data": True,
            "error": str(e)
        }

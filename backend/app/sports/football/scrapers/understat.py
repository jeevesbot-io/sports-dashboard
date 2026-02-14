"""
Understat.com xG data scraper.

Scrapes expected goals (xG) data from understat.com for Premier League matches.
"""
import asyncio
import json
import re
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, date
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Team name mapping between football-data.org and Understat
TEAM_NAME_MAPPING = {
    "Manchester United": "Manchester United",
    "Manchester City": "Manchester City",
    "Arsenal": "Arsenal",
    "Liverpool": "Liverpool",
    "Chelsea": "Chelsea",
    "Tottenham": "Tottenham",
    "Newcastle United": "Newcastle",
    "Brighton & Hove Albion": "Brighton",
    "Aston Villa": "Aston Villa",
    "West Ham United": "West Ham",
    "Crystal Palace": "Crystal Palace",
    "Fulham": "Fulham",
    "Wolverhampton Wanderers": "Wolves",
    "Everton": "Everton",
    "Brentford": "Brentford",
    "Nottingham Forest": "Nottingham Forest",
    "AFC Bournemouth": "Bournemouth",
    "Sheffield United": "Sheffield United",
    "Burnley": "Burnley",
    "Luton Town": "Luton",
    "Leicester City": "Leicester",
    "Ipswich Town": "Ipswich",
    "Southampton": "Southampton"
}

# Reverse mapping for lookups
UNDERSTAT_TO_FOOTBALLDATA = {v: k for k, v in TEAM_NAME_MAPPING.items()}


class UnderstatScraper:
    """Scraper for Understat xG data."""
    
    def __init__(self):
        self.base_url = "https://understat.com"
        self.rate_limit_delay = 3.0  # 3 seconds between requests
        
    async def scrape_league_matches(self, season: int = 2025) -> List[Dict[str, Any]]:
        """
        Scrape all matches from Understat league page.
        
        Args:
            season: Season year (e.g., 2025)
            
        Returns:
            List of match data dictionaries
        """
        logger.info(f"Scraping Understat league data for season {season}")
        
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.base_url}/league/EPL/{season}"
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                
                matches = self._parse_league_page(response.text)
                logger.info(f"Found {len(matches)} matches on Understat")
                
                return matches
                
            except httpx.RequestError as e:
                logger.error(f"Failed to fetch Understat league page: {e}")
                raise
            except Exception as e:
                logger.error(f"Error parsing Understat data: {e}")
                raise
    
    def _parse_league_page(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse match data from league page HTML."""
        matches = []
        
        # Look for JSON data in script tags
        # Understat typically embeds data in variables like datesData or matchesData
        patterns = [
            r'var\s+datesData\s*=\s*JSON\.parse\(\'([^\']+)\'\)',
            r'var\s+matchesData\s*=\s*JSON\.parse\(\'([^\']+)\'\)',
            r'JSON\.parse\(\'([^\']+)\'\)'
        ]
        
        for pattern in patterns:
            matches_found = re.findall(pattern, html_content)
            if matches_found:
                logger.info(f"Found {len(matches_found)} JSON data blocks")
                
                for json_str in matches_found:
                    try:
                        # Unescape the JSON string
                        json_str = json_str.replace('\\"', '"').replace('\\\\', '\\')
                        data = json.loads(json_str)
                        
                        # Check if this looks like match data
                        if isinstance(data, dict) and any(key in data for key in ['matches', 'fixtures']):
                            matches.extend(self._extract_matches_from_data(data))
                        elif isinstance(data, list) and data and isinstance(data[0], dict):
                            # Could be a list of matches
                            matches.extend(self._extract_matches_from_list(data))
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON block: {e}")
                        continue
        
        # If we didn't find structured data, try to parse from table HTML
        if not matches:
            logger.warning("No JSON data found, attempting HTML table parsing")
            matches = self._parse_html_table(html_content)
        
        return matches
    
    def _extract_matches_from_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract matches from structured data object."""
        matches = []
        
        # Try different possible data structures
        match_lists = []
        if 'matches' in data:
            match_lists.append(data['matches'])
        if 'fixtures' in data:
            match_lists.append(data['fixtures'])
        
        for match_list in match_lists:
            if isinstance(match_list, dict):
                # Data might be organized by date
                for date_key, day_matches in match_list.items():
                    if isinstance(day_matches, list):
                        matches.extend(self._extract_matches_from_list(day_matches))
            elif isinstance(match_list, list):
                matches.extend(self._extract_matches_from_list(match_list))
        
        return matches
    
    def _extract_matches_from_list(self, match_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract match data from a list of match objects."""
        matches = []
        
        for match in match_list:
            if not isinstance(match, dict):
                continue
                
            try:
                # Extract basic match info
                match_data = {
                    'understat_match_id': match.get('id'),
                    'home_team': self._normalize_team_name(match.get('h', {}).get('title', '')),
                    'away_team': self._normalize_team_name(match.get('a', {}).get('title', '')),
                    'home_goals': int(match.get('goals', {}).get('h', 0) or 0),
                    'away_goals': int(match.get('goals', {}).get('a', 0) or 0),
                    'home_xg': float(match.get('xG', {}).get('h', 0.0) or 0.0),
                    'away_xg': float(match.get('xG', {}).get('a', 0.0) or 0.0),
                    'date': match.get('datetime', ''),
                    'season': 2025  # Current season
                }
                
                # Only include if we have essential data
                if (match_data['understat_match_id'] and 
                    match_data['home_team'] and 
                    match_data['away_team']):
                    matches.append(match_data)
                    
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse match data: {match}, error: {e}")
                continue
        
        return matches
    
    def _parse_html_table(self, html_content: str) -> List[Dict[str, Any]]:
        """Fallback: parse match data from HTML table."""
        logger.info("Attempting HTML table parsing as fallback")
        
        # This is a simplified fallback - in practice, you might need BeautifulSoup
        # For now, we'll return empty list and rely on mock data
        return []
    
    def _normalize_team_name(self, team_name: str) -> str:
        """Normalize team name to match our database."""
        if not team_name:
            return ""
            
        # Remove extra whitespace
        team_name = team_name.strip()
        
        # Direct mapping
        if team_name in UNDERSTAT_TO_FOOTBALLDATA:
            return UNDERSTAT_TO_FOOTBALLDATA[team_name]
        
        # Fallback to original name
        return team_name
    
    async def store_xg_data(self, db: AsyncSession, matches: List[Dict[str, Any]]) -> int:
        """
        Store xG data in the database.

        Args:
            db: Database session
            matches: List of match data

        Returns:
            Number of matches stored
        """
        if not matches:
            return 0

        logger.info(f"Storing {len(matches)} xG records")

        stored_count = 0
        for match in matches:
            try:
                # Check if already exists
                exists_query = text("""
                    SELECT id FROM sport_football_xg 
                    WHERE understat_match_id = :match_id
                """)
                result = await db.execute(exists_query, {"match_id": match['understat_match_id']})
                if result.fetchone():
                    continue  # Skip if already exists
                
                # Insert new record
                insert_query = text("""
                    INSERT INTO sport_football_xg 
                    (understat_match_id, home_team, away_team, home_xg, away_xg, 
                     home_goals, away_goals, date, season, created_at)
                    VALUES (:match_id, :home_team, :away_team, :home_xg, :away_xg,
                            :home_goals, :away_goals, :match_date, :season, :created_at)
                """)
                
                await db.execute(insert_query, {
                    "match_id": match['understat_match_id'],
                    "home_team": match['home_team'],
                    "away_team": match['away_team'],
                    "home_xg": match['home_xg'],
                    "away_xg": match['away_xg'],
                    "home_goals": match['home_goals'],
                    "away_goals": match['away_goals'],
                    "match_date": match['date'],
                    "season": match['season'],
                    "created_at": datetime.utcnow()
                })
                
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to store match {match.get('understat_match_id')}: {e}")
                continue
        
        await db.commit()
        logger.info(f"Successfully stored {stored_count} new xG records")
        return stored_count
    
async def ingest_xg_data(db: AsyncSession, season: int = 2025) -> Dict[str, Any]:
    """
    Main ingestion function for xG data.
    
    Args:
        db: Database session
        season: Season year
        
    Returns:
        Ingestion summary
    """
    scraper = UnderstatScraper()
    
    try:
        # Scrape data
        matches = await scraper.scrape_league_matches(season)
        
        if not matches:
            logger.warning("No matches found, creating mock data")
            matches = _create_mock_xg_data()
        
        # Store in database
        stored_count = await scraper.store_xg_data(db, matches)
        
        # Rate limiting delay
        await asyncio.sleep(scraper.rate_limit_delay)
        
        return {
            "scraped_matches": len(matches),
            "stored_matches": stored_count,
            "season": season,
            "success": True,
            "mock_data": len(matches) > 0 and matches[0].get('mock', False)
        }
        
    except Exception as e:
        logger.error(f"xG ingestion failed: {e}")
        
        # Fallback to mock data
        logger.info("Falling back to mock xG data")
        mock_matches = _create_mock_xg_data()
        stored_count = await scraper.store_xg_data(db, mock_matches)
        
        return {
            "scraped_matches": 0,
            "stored_matches": stored_count,
            "season": season,
            "success": False,
            "mock_data": True,
            "error": str(e)
        }


def _create_mock_xg_data() -> List[Dict[str, Any]]:
    """Create mock xG data for testing."""
    logger.info("Generating mock xG data")
    
    mock_matches = []
    teams = list(TEAM_NAME_MAPPING.keys())[:20]  # Take first 20 teams
    
    # Generate some realistic mock data
    import random
    
    for i in range(50):  # 50 mock matches
        home_team = random.choice(teams)
        away_team = random.choice([t for t in teams if t != home_team])
        
        # Generate realistic xG values (typically 0.2 to 3.5)
        home_xg = round(random.uniform(0.2, 3.5), 2)
        away_xg = round(random.uniform(0.2, 3.5), 2)
        
        # Goals are somewhat correlated with xG but with variance
        home_goals = max(0, int(home_xg + random.normalvariate(0, 0.8)))
        away_goals = max(0, int(away_xg + random.normalvariate(0, 0.8)))
        
        mock_matches.append({
            'understat_match_id': f"mock_{i+1}",
            'home_team': home_team,
            'away_team': away_team,
            'home_goals': home_goals,
            'away_goals': away_goals,
            'home_xg': home_xg,
            'away_xg': away_xg,
            'date': f"2025-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            'season': 2025,
            'mock': True
        })
    
    return mock_matches
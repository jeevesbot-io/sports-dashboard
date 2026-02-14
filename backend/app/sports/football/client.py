"""
Football Data API client with retry logic and timeout handling.
Ported and enhanced from the original footballdash api_client.py.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
import httpx
from httpx import AsyncClient, Response

from ...config import settings

logger = logging.getLogger(__name__)


class FootballAPIException(Exception):
    """Custom exception for Football API errors."""
    pass


class FootballAPIClient:
    """
    Async API client for Football Data API with enhanced error handling.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            api_key: API authentication key (defaults to settings)
        """
        self.api_key = api_key or settings.football_data_api_key
        if not self.api_key:
            raise FootballAPIException("Football Data API key is required")
        
        self.base_url = settings.football_data_base_url.rstrip('/')
        self.timeout = settings.football_data_timeout
        self.retry_count = settings.football_data_retry_count
        self.retry_delay = settings.football_data_retry_delay
        
        self.headers = {
            'X-Auth-Token': self.api_key,
            'Accept': 'application/json',
        }
        
        # Simple in-memory cache
        self._cache: Dict[str, Any] = {}
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            use_cache: Whether to use cached responses
            
        Returns:
            API response data
            
        Raises:
            FootballAPIException: If request fails after retries
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        cache_key = f"{endpoint}_{str(params or {})}"
        
        # Check cache
        if use_cache and cache_key in self._cache:
            logger.debug(f"Using cached data for {endpoint}")
            return self._cache[cache_key]
        
        async with AsyncClient(
            headers=self.headers,
            timeout=self.timeout
        ) as client:
            for attempt in range(self.retry_count + 1):
                try:
                    logger.debug(f"Making request to {url} (attempt {attempt + 1})")
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Cache successful response
                    if use_cache:
                        self._cache[cache_key] = data
                    
                    return data
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:  # Rate limit
                        if attempt < self.retry_count:
                            wait_time = self.retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limited, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                    elif e.response.status_code >= 500:  # Server error
                        if attempt < self.retry_count:
                            wait_time = self.retry_delay * (2 ** attempt)
                            logger.warning(f"Server error {e.response.status_code}, retrying in {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                    raise FootballAPIException(f"HTTP {e.response.status_code}: {e.response.text}")
                    
                except httpx.RequestError as e:
                    if attempt < self.retry_count:
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Request error, retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    logger.error(f"Request failed after {self.retry_count} retries: {e}")
                    raise FootballAPIException(f"Request failed: {e}")
        
        raise FootballAPIException(f"Request failed after {self.retry_count + 1} attempts")
    
    async def get_competition_teams(
        self,
        competition: str = "PL",
        season: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get teams for a competition.
        
        Args:
            competition: Competition code (default: PL for Premier League)
            season: Optional season year
            
        Returns:
            List of team data
        """
        endpoint = f"competitions/{competition}/teams"
        params = {}
        if season:
            params["season"] = season
        
        try:
            data = await self._make_request(endpoint, params)
            return data.get("teams", [])
        except Exception as e:
            logger.error(f"Failed to fetch teams: {e}")
            raise FootballAPIException(f"Failed to fetch teams: {e}")
    
    async def get_competition_matches(
        self,
        competition: str = "PL",
        season: Optional[int] = None,
        matchday: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get matches for a competition.
        
        Args:
            competition: Competition code (default: PL for Premier League)
            season: Optional season year
            matchday: Optional matchday number
            status: Optional status filter (FINISHED, SCHEDULED, etc.)
            
        Returns:
            List of match data
        """
        endpoint = f"competitions/{competition}/matches"
        params = {}
        
        if season:
            params["season"] = season
        if matchday:
            params["matchday"] = matchday
        if status:
            params["status"] = status
        
        try:
            data = await self._make_request(endpoint, params)
            return data.get("matches", [])
        except Exception as e:
            logger.error(f"Failed to fetch matches: {e}")
            raise FootballAPIException(f"Failed to fetch matches: {e}")
    
    async def get_competition_standings(
        self,
        competition: str = "PL",
        season: Optional[int] = None,
        matchday: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get standings for a competition.
        
        Args:
            competition: Competition code (default: PL for Premier League)
            season: Optional season year
            matchday: Optional matchday number
            
        Returns:
            List of standing data
        """
        endpoint = f"competitions/{competition}/standings"
        params = {}
        
        if season:
            params["season"] = season
        if matchday:
            params["matchday"] = matchday
        
        try:
            data = await self._make_request(endpoint, params)
            # Extract table data from the nested structure
            standings = data.get("standings", [])
            if standings:
                return standings[0].get("table", [])
            return []
        except Exception as e:
            logger.error(f"Failed to fetch standings: {e}")
            raise FootballAPIException(f"Failed to fetch standings: {e}")
    
    async def test_connection(self) -> bool:
        """
        Test API connection and authentication.
        
        Returns:
            True if connection successful
        """
        try:
            await self._make_request("competitions/PL", use_cache=False)
            logger.info("Football API connection test successful")
            return True
        except Exception as e:
            logger.error(f"Football API connection test failed: {e}")
            return False
    
    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._cache.clear()
        logger.info("Football API cache cleared")
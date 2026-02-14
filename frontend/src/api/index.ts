/**
 * API client for Sports Dashboard backend.
 */
import axios, { AxiosInstance, AxiosResponse } from 'axios'
import type {
  StandardResponse,
  FootballTeam,
  FootballTeamDetail,
  FootballFixture,
  FootballStanding,
  FootballFormAnalysis,
  FootballStandingsParams,
  FootballFixturesParams,
  FootballTeamFormParams,
  ComingSoonResponse,
  ApiClientConfig,
  XGStanding,
  HeadToHeadData,
  MatchPrediction,
  TeamXGAnalysis,
  ChartData,
  HomeAdvantageData,
  PlayerStats,
  PlayerStatsParams,
  TeamXGTimeline,
  TeamVsLeagueData,
  SeasonProjectionResponse,
  AdvancedTeamStats,
  AdvancedPlayerStats,
  TeamRatingsResponse,
  OpponentAdjustedForm,
  FixtureDifficultyResponse,
  PositionProgressionResponse,
  ScorelineAnalysisResponse,
  MultiSeasonHomeAdvantageResponse,
  StorePredictionRequest,
  PredictionRecord,
  PredictionAccuracy,
  UpcomingResponse
} from '@/types'

class ApiClient {
  private client: AxiosInstance

  constructor(config: ApiClientConfig) {
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message)
        return Promise.reject(error)
      }
    )
  }

  // Health check
  async health(): Promise<StandardResponse> {
    const response: AxiosResponse<StandardResponse> = await this.client.get('/api/health')
    return response.data
  }

  // Football API methods
  async getFootballTeams(): Promise<FootballTeam[]> {
    const response: AxiosResponse<StandardResponse<FootballTeam[]>> = 
      await this.client.get('/api/football/teams')
    return response.data.data || []
  }

  async getFootballTeamDetail(teamId: number): Promise<FootballTeamDetail | null> {
    try {
      const response: AxiosResponse<StandardResponse<FootballTeamDetail>> = 
        await this.client.get(`/api/football/teams/${teamId}`)
      return response.data.data || null
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null
      }
      throw error
    }
  }

  async getFootballTeamForm(
    teamId: number,
    params: FootballTeamFormParams = {}
  ): Promise<FootballFormAnalysis | null> {
    try {
      const response: AxiosResponse<StandardResponse<FootballFormAnalysis>> = 
        await this.client.get(`/api/football/teams/${teamId}/form`, { params })
      return response.data.data || null
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null
      }
      throw error
    }
  }

  async getFootballFixtures(
    params: FootballFixturesParams = {}
  ): Promise<FootballFixture[]> {
    const response: AxiosResponse<StandardResponse<FootballFixture[]>> = 
      await this.client.get('/api/football/fixtures', { params })
    return response.data.data || []
  }

  async getFootballStandings(
    params: FootballStandingsParams = {}
  ): Promise<FootballStanding[]> {
    const response: AxiosResponse<StandardResponse<FootballStanding[]>> = 
      await this.client.get('/api/football/standings', { params })
    return response.data.data || []
  }

  // Analytics API methods

  async getXGStandings(season: number = 2025): Promise<StandardResponse<XGStanding[]>> {
    const response: AxiosResponse<StandardResponse<XGStanding[]>> =
      await this.client.get('/api/football/xg/standings', { params: { season } })
    return response.data
  }

  async getXGOverperformers(season: number = 2025, threshold: number = 2.0): Promise<StandardResponse<XGStanding[]>> {
    const response: AxiosResponse<StandardResponse<XGStanding[]>> =
      await this.client.get('/api/football/xg/overperformers', { params: { season, threshold } })
    return response.data
  }

  async getHeadToHead(team1: string, team2: string, season?: number): Promise<StandardResponse<HeadToHeadData>> {
    const params: Record<string, any> = { team1, team2 }
    if (season) params.season = season
    const response: AxiosResponse<StandardResponse<HeadToHeadData>> =
      await this.client.get('/api/football/head-to-head', { params })
    return response.data
  }

  async predictMatch(home: string, away: string, season: number = 2025): Promise<StandardResponse<MatchPrediction>> {
    const response: AxiosResponse<StandardResponse<MatchPrediction>> =
      await this.client.get('/api/football/predict', { params: { home, away, season } })
    return response.data
  }

  async getTeamXGAnalysis(teamId: number, season: number = 2025): Promise<StandardResponse<TeamXGAnalysis>> {
    const response: AxiosResponse<StandardResponse<TeamXGAnalysis>> =
      await this.client.get(`/api/football/teams/${teamId}/xg`, { params: { season } })
    return response.data
  }

  async getPointsProgression(season: number = 2025): Promise<StandardResponse<ChartData>> {
    const response: AxiosResponse<StandardResponse<ChartData>> =
      await this.client.get('/api/football/charts/points-progression', { params: { season } })
    return response.data
  }

  async getFormHeatmap(games: number = 10, season: number = 2025): Promise<StandardResponse<ChartData>> {
    const response: AxiosResponse<StandardResponse<ChartData>> =
      await this.client.get('/api/football/charts/form-heatmap', { params: { games, season } })
    return response.data
  }

  async ingestData(season: number = 2025): Promise<StandardResponse> {
    const response: AxiosResponse<StandardResponse> =
      await this.client.post('/api/football/ingest', null, { params: { season } })
    return response.data
  }

  async ingestXGData(season: number = 2025): Promise<StandardResponse> {
    const response: AxiosResponse<StandardResponse> =
      await this.client.post('/api/football/ingest-xg', null, { params: { season } })
    return response.data
  }

  // Home Advantage
  async getHomeAdvantage(season: number = 2025): Promise<StandardResponse<HomeAdvantageData>> {
    const response: AxiosResponse<StandardResponse<HomeAdvantageData>> =
      await this.client.get('/api/football/home-advantage', { params: { season } })
    return response.data
  }

  // Player Stats
  async getPlayers(params: PlayerStatsParams = {}): Promise<StandardResponse<PlayerStats[]>> {
    const response: AxiosResponse<StandardResponse<PlayerStats[]>> =
      await this.client.get('/api/football/players', { params })
    return response.data
  }

  async getPlayerDetail(playerId: number, season: number = 2025): Promise<StandardResponse<PlayerStats>> {
    const response: AxiosResponse<StandardResponse<PlayerStats>> =
      await this.client.get(`/api/football/players/${playerId}`, { params: { season } })
    return response.data
  }

  async ingestPlayerData(season: number = 2025): Promise<StandardResponse> {
    const response: AxiosResponse<StandardResponse> =
      await this.client.post('/api/football/ingest-players', null, { params: { season } })
    return response.data
  }

  // xG Timeline
  async getTeamXGTimeline(teamId: number, season: number = 2025): Promise<StandardResponse<TeamXGTimeline>> {
    const response: AxiosResponse<StandardResponse<TeamXGTimeline>> =
      await this.client.get(`/api/football/teams/${teamId}/xg-timeline`, { params: { season } })
    return response.data
  }

  // Team vs League
  async getTeamVsLeague(teamId: number, season: number = 2025): Promise<StandardResponse<TeamVsLeagueData>> {
    const response: AxiosResponse<StandardResponse<TeamVsLeagueData>> =
      await this.client.get(`/api/football/teams/${teamId}/vs-league`, { params: { season } })
    return response.data
  }

  // Season Projections
  async getSeasonProjections(season: number = 2025, simulations: number = 1000): Promise<StandardResponse<SeasonProjectionResponse>> {
    const response: AxiosResponse<StandardResponse<SeasonProjectionResponse>> =
      await this.client.get('/api/football/projections', { params: { season, simulations } })
    return response.data
  }

  // Advanced Stats (FBref)
  async getAdvancedTeamStats(season: number = 2025): Promise<StandardResponse<AdvancedTeamStats[]>> {
    const response: AxiosResponse<StandardResponse<AdvancedTeamStats[]>> =
      await this.client.get('/api/football/advanced/teams', { params: { season } })
    return response.data
  }

  async getAdvancedPlayerStats(params: Record<string, any> = {}): Promise<StandardResponse<AdvancedPlayerStats[]>> {
    const response: AxiosResponse<StandardResponse<AdvancedPlayerStats[]>> =
      await this.client.get('/api/football/advanced/players', { params })
    return response.data
  }

  async ingestFBrefData(season: number = 2025): Promise<StandardResponse> {
    const response: AxiosResponse<StandardResponse> =
      await this.client.post('/api/football/ingest-fbref', null, { params: { season } })
    return response.data
  }

  // Team Ratings
  async getTeamRatings(season: number = 2025, recalculate: boolean = false): Promise<StandardResponse<TeamRatingsResponse>> {
    const response: AxiosResponse<StandardResponse<TeamRatingsResponse>> =
      await this.client.get('/api/football/team-ratings', { params: { season, recalculate } })
    return response.data
  }

  // Opponent-Adjusted Form
  async getOpponentAdjustedForm(teamId: number, games: number = 10, season: number = 2025): Promise<StandardResponse<OpponentAdjustedForm>> {
    const response: AxiosResponse<StandardResponse<OpponentAdjustedForm>> =
      await this.client.get(`/api/football/teams/${teamId}/form-adjusted`, { params: { games, season } })
    return response.data
  }

  // Fixture Difficulty
  async getFixtureDifficulty(season: number = 2025, ratingMode: string = 'team_rating'): Promise<StandardResponse<FixtureDifficultyResponse>> {
    const response: AxiosResponse<StandardResponse<FixtureDifficultyResponse>> =
      await this.client.get('/api/football/fixture-difficulty', { params: { season, rating_mode: ratingMode } })
    return response.data
  }

  // Position Progression
  async getPositionProgression(season: number = 2025, teamIds?: string): Promise<StandardResponse<PositionProgressionResponse>> {
    const params: Record<string, any> = { season }
    if (teamIds) params.team_ids = teamIds
    const response: AxiosResponse<StandardResponse<PositionProgressionResponse>> =
      await this.client.get('/api/football/charts/position-progression', { params })
    return response.data
  }

  // Scoreline Frequency
  async getScorelineFrequency(teamId: number, seasonsBack: number = 3): Promise<StandardResponse<ScorelineAnalysisResponse>> {
    const response: AxiosResponse<StandardResponse<ScorelineAnalysisResponse>> =
      await this.client.get(`/api/football/teams/${teamId}/scorelines`, { params: { seasons_back: seasonsBack } })
    return response.data
  }

  // Multi-Season Home Advantage
  async getHomeAdvantageMultiSeason(seasonsBack: number = 3): Promise<StandardResponse<MultiSeasonHomeAdvantageResponse>> {
    const response: AxiosResponse<StandardResponse<MultiSeasonHomeAdvantageResponse>> =
      await this.client.get('/api/football/home-advantage-multi-season', { params: { seasons_back: seasonsBack } })
    return response.data
  }

  // Prediction Tracking
  async storePrediction(request: StorePredictionRequest): Promise<StandardResponse> {
    const response: AxiosResponse<StandardResponse> =
      await this.client.post('/api/football/predictions/store', request)
    return response.data
  }

  async updatePredictionResults(season: number = 2025): Promise<StandardResponse> {
    const response: AxiosResponse<StandardResponse> =
      await this.client.post('/api/football/predictions/update-results', null, { params: { season } })
    return response.data
  }

  async getPredictionAccuracy(season: number = 2025): Promise<StandardResponse<PredictionAccuracy>> {
    const response: AxiosResponse<StandardResponse<PredictionAccuracy>> =
      await this.client.get('/api/football/predictions/accuracy', { params: { season } })
    return response.data
  }

  async getPredictionHistory(season: number = 2025, limit: number = 20): Promise<StandardResponse<PredictionRecord[]>> {
    const response: AxiosResponse<StandardResponse<PredictionRecord[]>> =
      await this.client.get('/api/football/predictions/history', { params: { season, limit } })
    return response.data
  }

  // Upcoming Fixtures
  async getUpcomingFixtures(season: number = 2025, includePredictions: boolean = false): Promise<StandardResponse<UpcomingResponse>> {
    const response: AxiosResponse<StandardResponse<UpcomingResponse>> =
      await this.client.get('/api/football/upcoming', { params: { season, include_predictions: includePredictions } })
    return response.data
  }

  // Multi-season Ingestion
  async ingestMultiSeason(startSeason: number = 2022, endSeason: number = 2025): Promise<StandardResponse> {
    const response: AxiosResponse<StandardResponse> =
      await this.client.post('/api/football/ingest-multi-season', null, { params: { start_season: startSeason, end_season: endSeason } })
    return response.data
  }

  // Cricket API methods
  async getCricketStatus(): Promise<ComingSoonResponse> {
    const response: AxiosResponse<StandardResponse<ComingSoonResponse>> = 
      await this.client.get('/api/cricket/')
    return response.data.data || {
      status: 'coming_soon',
      sport: 'cricket',
      scope: 'international',
      message: 'Cricket analytics coming soon!'
    }
  }

  // Rugby API methods
  async getRugbyStatus(): Promise<ComingSoonResponse> {
    const response: AxiosResponse<StandardResponse<ComingSoonResponse>> = 
      await this.client.get('/api/rugby/')
    return response.data.data || {
      status: 'coming_soon',
      sport: 'rugby',
      scope: 'international',
      message: 'Rugby analytics coming soon!'
    }
  }
}

// Create and export API client instance
const apiClient = new ApiClient({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5160',
  timeout: 30000,
})

export default apiClient
export { ApiClient }
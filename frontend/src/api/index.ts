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
  ChartData
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
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5060',
  timeout: 30000,
})

export default apiClient
export { ApiClient }
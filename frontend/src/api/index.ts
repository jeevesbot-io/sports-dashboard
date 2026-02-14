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
  ApiClientConfig
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
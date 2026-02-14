/**
 * API service for Sports Dashboard
 */

// Types
interface ApiResponse<T = any> {
  data: {
    data: T
    message: string
    success?: boolean
  }
}

interface Team {
  id: number
  name: string
  short_name: string
  tla: string
  crest_url?: string
}

interface Fixture {
  id: number
  api_id: number
  season: number
  matchday: number
  status: string
  utc_date: string
  home_team: Team
  away_team: Team
  home_score?: number
  away_score?: number
  winner?: string
}

interface Standing {
  id: number
  season: number
  matchday: number
  position: number
  played: number
  won: number
  drawn: number
  lost: number
  goals_for: number
  goals_against: number
  goal_difference: number
  points: number
  form?: string
  team: Team
  win_percentage: number
  points_per_game: number
}

interface TeamDetail extends Team {
  total_matches: number
  wins: number
  draws: number
  losses: number
  goals_for: number
  goals_against: number
  goal_difference: number
  points: number
  win_percentage: number
  current_position?: number
}

interface FormAnalysis {
  team: Team
  games_analyzed: number
  form_string: string
  wins: number
  draws: number
  losses: number
  goals_for: number
  goals_against: number
  points: number
  win_percentage: number
  recent_fixtures: Fixture[]
}

interface XGStanding {
  team: string
  matches: number
  xg_for: number
  xg_against: number
  xg_diff: number
  goals_for: number
  goals_against: number
  goal_diff: number
  overperformance: number
}

interface HeadToHeadData {
  team1: Team
  team2: Team
  matches: Fixture[]
  team1_wins: number
  team2_wins: number
  draws: number
  team1_goals: number
  team2_goals: number
  total_matches: number
}

interface MatchPrediction {
  home_team: {
    name: string
    id: number
    attack_strength: number
    defense_strength: number
  }
  away_team: {
    name: string
    id: number
    attack_strength: number
    defense_strength: number
  }
  predictions: {
    home_xg: number
    away_xg: number
    home_win_prob: number
    draw_prob: number
    away_win_prob: number
    most_likely_score: string
    confidence: number
  }
  model: string
  season: number
}

interface TeamXGAnalysis {
  team: Team
  season: number
  matches: number
  xg_for: number
  xg_against: number
  xg_diff: number
  goals_for: number
  goals_against: number
  goal_diff: number
  overperformance: number
  xg_per_game: number
  xa_per_game: number
}

interface ChartData {
  matchdays?: number[]
  series: any[]
  teams?: any[]
  games?: number
  season: number
}

// Base API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5060'

class ApiClient {
  private baseURL: string

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  private async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      return { data }
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error)
      throw error
    }
  }

  // Football API methods
  async getTeams(): Promise<ApiResponse<Team[]>> {
    return this.request('/api/football/teams')
  }

  async getTeamDetail(teamId: number): Promise<ApiResponse<TeamDetail>> {
    return this.request(`/api/football/teams/${teamId}`)
  }

  async getTeamForm(teamId: number, games: number = 5): Promise<ApiResponse<FormAnalysis>> {
    return this.request(`/api/football/teams/${teamId}/form?games=${games}`)
  }

  async getFixtures(params: {
    season?: number
    match_status?: string
    team?: string
    matchday?: number
    limit?: number
  } = {}): Promise<ApiResponse<Fixture[]>> {
    const searchParams = new URLSearchParams()
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString())
      }
    })
    
    const queryString = searchParams.toString()
    const endpoint = `/api/football/fixtures${queryString ? `?${queryString}` : ''}`
    
    return this.request(endpoint)
  }

  async getStandings(season: number = 2025, matchday: string = 'latest'): Promise<ApiResponse<Standing[]>> {
    return this.request(`/api/football/standings?season=${season}&matchday=${matchday}`)
  }

  async ingestData(season: number = 2025): Promise<ApiResponse<any>> {
    return this.request(`/api/football/ingest?season=${season}`, { method: 'POST' })
  }

  // Analytics API methods
  async getHeadToHead(team1: string, team2: string, season?: number): Promise<ApiResponse<HeadToHeadData>> {
    const params = new URLSearchParams({
      team1,
      team2
    })
    
    if (season) {
      params.append('season', season.toString())
    }
    
    return this.request(`/api/football/head-to-head?${params}`)
  }

  async getXGStandings(season: number = 2025): Promise<ApiResponse<XGStanding[]>> {
    return this.request(`/api/football/xg/standings?season=${season}`)
  }

  async getXGOverperformers(season: number = 2025, threshold: number = 2.0): Promise<ApiResponse<XGStanding[]>> {
    return this.request(`/api/football/xg/overperformers?season=${season}&threshold=${threshold}`)
  }

  async getTeamXGAnalysis(teamId: number, season: number = 2025): Promise<ApiResponse<TeamXGAnalysis>> {
    return this.request(`/api/football/teams/${teamId}/xg?season=${season}`)
  }

  async predictMatch(home: string, away: string, season: number = 2025): Promise<ApiResponse<MatchPrediction>> {
    const params = new URLSearchParams({
      home,
      away,
      season: season.toString()
    })
    
    return this.request(`/api/football/predict?${params}`)
  }

  async getPointsProgression(season: number = 2025): Promise<ApiResponse<ChartData>> {
    return this.request(`/api/football/charts/points-progression?season=${season}`)
  }

  async getFormHeatmap(games: number = 10, season: number = 2025): Promise<ApiResponse<ChartData>> {
    return this.request(`/api/football/charts/form-heatmap?games=${games}&season=${season}`)
  }

  async ingestXGData(season: number = 2025): Promise<ApiResponse<any>> {
    return this.request(`/api/football/ingest-xg?season=${season}`, { method: 'POST' })
  }
}

// Create API client instance
export const footballApi = new ApiClient()

// Export types for use in components
export type {
  Team,
  Fixture,
  Standing,
  TeamDetail,
  FormAnalysis,
  XGStanding,
  HeadToHeadData,
  MatchPrediction,
  TeamXGAnalysis,
  ChartData,
  ApiResponse
}
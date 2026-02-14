/**
 * TypeScript type definitions for the Sports Dashboard.
 */

// API Response Types
export interface StandardResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  errors?: Record<string, any>
  timestamp: string
}

// Football Types
export interface FootballTeam {
  id: number
  api_id: number
  name: string
  short_name: string
  tla: string
  crest_url?: string
  created_at: string
  updated_at: string
}

export interface FootballTeamDetail extends FootballTeam {
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

export interface FootballFixture {
  id: number
  api_id: number
  season: number
  matchday: number
  status: string
  utc_date: string
  home_team: FootballTeam
  away_team: FootballTeam
  home_score?: number
  away_score?: number
  winner?: string
  score_display?: string
  is_finished: boolean
  created_at: string
  updated_at: string
}

export interface FootballStanding {
  id: number
  season: number
  matchday: number
  team: FootballTeam
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
  win_percentage: number
  points_per_game: number
  created_at: string
}

export interface FootballFormAnalysis {
  team: FootballTeam
  games_analyzed: number
  form_string: string
  wins: number
  draws: number
  losses: number
  goals_for: number
  goals_against: number
  points: number
  win_percentage: number
  recent_fixtures: FootballFixture[]
}

// xG / Analytics Types
export interface XGStanding {
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

export interface HeadToHeadData {
  team1: FootballTeam
  team2: FootballTeam
  matches: FootballFixture[]
  team1_wins: number
  team2_wins: number
  draws: number
  team1_goals: number
  team2_goals: number
  total_matches: number
}

export interface MatchPrediction {
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

export interface TeamXGAnalysis {
  team: FootballTeam
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

export interface ChartData {
  matchdays?: number[]
  series?: any[]
  teams?: any[]
  games?: number
  season: number
}

// Cricket/Rugby Coming Soon Types
export interface ComingSoonResponse {
  status: string
  sport: string
  scope: string
  message: string
}

// Navigation Types
export interface SportTab {
  name: string
  label: string
  route: string
  active: boolean
  comingSoon?: boolean
}

// Chart Data Types
export interface ChartDataPoint {
  name: string
  value: number
  [key: string]: any
}

export interface TableColumn {
  field: string
  header: string
  sortable?: boolean
  width?: string
  class?: string
}

// API Client Types
export interface ApiClientConfig {
  baseURL: string
  timeout: number
}

export interface PaginationParams {
  page?: number
  limit?: number
}

export interface FootballStandingsParams {
  season?: number
  matchday?: string
}

export interface FootballFixturesParams {
  season?: number
  status?: string
  team?: string
  matchday?: number
  limit?: number
}

export interface FootballTeamFormParams {
  games?: number
}
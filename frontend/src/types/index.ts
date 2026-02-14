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

// Home Advantage Types
export interface HomeAdvantageTeam {
  team: string
  home_played: number
  home_won: number
  home_drawn: number
  home_lost: number
  home_gf: number
  home_ga: number
  home_ppg: number
  away_played: number
  away_won: number
  away_drawn: number
  away_lost: number
  away_gf: number
  away_ga: number
  away_ppg: number
  advantage_index: number
}

export interface HomeAdvantageData {
  teams: HomeAdvantageTeam[]
  season: number
}

// Player Stats Types
export interface PlayerStats {
  id: number
  understat_player_id?: string
  name: string
  team_name: string
  season: number
  games: number
  minutes: number
  goals: number
  assists: number
  shots: number
  key_passes: number
  xg: number
  xa: number
  npg: number
  npxg: number
  xg_per_90: number
  goals_minus_xg: number
}

export interface PlayerStatsParams {
  season?: number
  sort_by?: string
  order?: string
  limit?: number
  team?: string
  search?: string
}

// xG Timeline Types
export interface XGTimelinePoint {
  matchday: number
  date?: string
  opponent: string
  is_home: boolean
  goals_for: number
  goals_against: number
  xg_for: number
  xg_against: number
  cumulative_goals: number
  cumulative_xg: number
  cumulative_goals_against: number
  cumulative_xg_against: number
}

export interface TeamXGTimeline {
  team: FootballTeam
  season: number
  timeline: XGTimelinePoint[]
}

// Team vs League Types
export interface TeamVsLeagueMetric {
  metric: string
  team_value: number
  league_value: number
  difference: number
}

export interface TeamVsLeagueData {
  team: FootballTeam
  season: number
  metrics: TeamVsLeagueMetric[]
}

// Season Projection Types
export interface TeamProjection {
  team: string
  current_points: number
  current_position: number
  projected_points_mean: number
  projected_points_5th: number
  projected_points_95th: number
  title_probability: number
  top4_probability: number
  relegation_probability: number
  projected_position_mean: number
}

export interface SeasonProjectionResponse {
  teams: TeamProjection[]
  simulations: number
  season: number
}

// Advanced Stats Types (FBref)
export interface AdvancedTeamStats {
  id: number
  team_name: string
  season: number
  possession_pct?: number
  progressive_passes?: number
  progressive_carries?: number
  pressures?: number
  pressure_success_pct?: number
  tackles?: number
  interceptions?: number
  blocks?: number
  sca?: number
  gca?: number
  passes_completed?: number
  pass_completion_pct?: number
  key_passes?: number
  crosses?: number
  through_balls?: number
}

export interface AdvancedPlayerStats {
  id: number
  player_name: string
  team_name: string
  season: number
  position?: string
  age?: number
  minutes_90s?: number
  progressive_passes?: number
  progressive_carries?: number
  progressive_passes_received?: number
  pressures?: number
  pressure_success_pct?: number
  tackles?: number
  interceptions?: number
  blocks?: number
  sca?: number
  gca?: number
  passes_completed?: number
  pass_completion_pct?: number
  key_passes?: number
  crosses?: number
  through_balls?: number
  carries?: number
  take_ons?: number
  take_on_pct?: number
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

// Team Rating Types
export interface TeamRating {
  team_id: number
  team_name: string
  tla: string
  rating: number
  seasons_analyzed: number
}

export interface TeamRatingsResponse {
  ratings: TeamRating[]
  season: number
}

// Opponent-Adjusted Form Types
export interface FormMatchBreakdown {
  opponent: string
  result: string
  opponent_rating: number
  contribution: number
  is_home: boolean
}

export interface OpponentAdjustedForm {
  team: FootballTeam
  form_rating_5: number
  form_rating_10: number
  form_string: string
  breakdown: FormMatchBreakdown[]
}

// Fixture Difficulty Types
export interface FixtureDifficultyCell {
  matchday: number
  opponent_short: string
  is_home: boolean
  difficulty: number
  status: string
  result?: string
}

export interface TeamFixtureDifficulty {
  team_name: string
  tla: string
  team_id: number
  fixtures: FixtureDifficultyCell[]
}

export interface FixtureDifficultyResponse {
  teams: TeamFixtureDifficulty[]
  season: number
  rating_mode: string
}

// Position Progression Types
export interface TeamPositionProgression {
  team_name: string
  team_id: number
  positions: (number | null)[]
}

export interface PositionProgressionResponse {
  matchdays: number[]
  teams: TeamPositionProgression[]
  season: number
}

// Scoreline Frequency Types
export interface ScorelineFrequency {
  scoreline: string
  count: number
  wins: number
  draws: number
  losses: number
}

export interface ScorelineAnalysisResponse {
  team_name: string
  team_id: number
  scorelines: ScorelineFrequency[]
  seasons_analyzed: number
}

// Multi-Season Home Advantage Types
export interface MultiSeasonHomeAdvantage {
  team: string
  home_advantage: number
  avg_home_ppg: number
  avg_away_ppg: number
  seasons_analyzed: number
}

export interface MultiSeasonHomeAdvantageResponse {
  teams: MultiSeasonHomeAdvantage[]
  current_season: number
  seasons_back: number
}

// Prediction Tracking Types
export interface StorePredictionRequest {
  fixture_id: number
  predicted_home_score: number
  predicted_away_score: number
  home_win_prob: number
  draw_prob: number
  away_win_prob: number
  model_name?: string
}

export interface PredictionRecord {
  id: number
  fixture_id: number
  season: number
  predicted_home_score: number
  predicted_away_score: number
  home_win_prob: number
  draw_prob: number
  away_win_prob: number
  model_name: string
  actual_home_score?: number
  actual_away_score?: number
  outcome_correct?: boolean
  score_correct?: boolean
  score_error?: number
  created_at: string
}

export interface PredictionAccuracy {
  total: number
  evaluated: number
  outcome_accuracy: number
  score_accuracy: number
  avg_error: number
  by_month: any[]
}

// Upcoming Fixtures Types
export interface UpcomingFixture {
  fixture: FootballFixture
  prediction?: any
}

export interface UpcomingResponse {
  next_matchday?: number
  fixtures: UpcomingFixture[]
  season: number
}
/**
 * Pinia store for football data management.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api'
import type {
  FootballTeam,
  FootballTeamDetail,
  FootballFixture,
  FootballStanding,
  FootballFormAnalysis,
  FootballStandingsParams,
  FootballFixturesParams,
  FootballTeamFormParams
} from '@/types'

export const useFootballStore = defineStore('football', () => {
  // State
  const teams = ref<FootballTeam[]>([])
  const standings = ref<FootballStanding[]>([])
  const fixtures = ref<FootballFixture[]>([])
  const selectedTeam = ref<FootballTeamDetail | null>(null)
  const teamForm = ref<FootballFormAnalysis | null>(null)
  
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // Computed
  const newcastlePosition = computed(() => {
    const newcastle = standings.value.find(s => 
      s.team.name.toLowerCase().includes('newcastle')
    )
    return newcastle?.position || null
  })
  
  const newcastleTeam = computed(() => {
    return teams.value.find(t => 
      t.name.toLowerCase().includes('newcastle')
    )
  })
  
  const recentFixtures = computed(() => {
    return fixtures.value
      .filter(f => f.status === 'FINISHED')
      .sort((a, b) => new Date(b.utc_date).getTime() - new Date(a.utc_date).getTime())
      .slice(0, 10)
  })
  
  const upcomingFixtures = computed(() => {
    return fixtures.value
      .filter(f => f.status === 'SCHEDULED')
      .sort((a, b) => new Date(a.utc_date).getTime() - new Date(b.utc_date).getTime())
      .slice(0, 10)
  })
  
  // Actions
  const setLoading = (value: boolean) => {
    loading.value = value
  }
  
  const setError = (message: string | null) => {
    error.value = message
  }
  
  const clearError = () => {
    error.value = null
  }
  
  const fetchTeams = async () => {
    try {
      setLoading(true)
      clearError()
      
      teams.value = await apiClient.getFootballTeams()
    } catch (err: any) {
      setError(`Failed to fetch teams: ${err.message}`)
      console.error('Error fetching teams:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const fetchStandings = async (params: FootballStandingsParams = {}) => {
    try {
      setLoading(true)
      clearError()
      
      standings.value = await apiClient.getFootballStandings(params)
    } catch (err: any) {
      setError(`Failed to fetch standings: ${err.message}`)
      console.error('Error fetching standings:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const fetchFixtures = async (params: FootballFixturesParams = {}) => {
    try {
      setLoading(true)
      clearError()
      
      fixtures.value = await apiClient.getFootballFixtures(params)
    } catch (err: any) {
      setError(`Failed to fetch fixtures: ${err.message}`)
      console.error('Error fetching fixtures:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const fetchTeamDetail = async (teamId: number) => {
    try {
      setLoading(true)
      clearError()
      
      const team = await apiClient.getFootballTeamDetail(teamId)
      selectedTeam.value = team
      
      if (!team) {
        setError('Team not found')
      }
    } catch (err: any) {
      setError(`Failed to fetch team details: ${err.message}`)
      console.error('Error fetching team detail:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const fetchTeamForm = async (teamId: number, params: FootballTeamFormParams = {}) => {
    try {
      setLoading(true)
      clearError()
      
      const form = await apiClient.getFootballTeamForm(teamId, params)
      teamForm.value = form
      
      if (!form) {
        setError('Team form data not found')
      }
    } catch (err: any) {
      setError(`Failed to fetch team form: ${err.message}`)
      console.error('Error fetching team form:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const initializeDashboard = async () => {
    try {
      setLoading(true)
      clearError()
      
      // Fetch all essential data for the dashboard
      await Promise.all([
        fetchTeams(),
        fetchStandings({ season: 2025, matchday: 'latest' }),
        fetchFixtures({ status: 'FINISHED', limit: 20 })
      ])
    } catch (err: any) {
      setError(`Failed to initialize dashboard: ${err.message}`)
      console.error('Error initializing dashboard:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const clearSelectedTeam = () => {
    selectedTeam.value = null
  }
  
  const clearTeamForm = () => {
    teamForm.value = null
  }
  
  return {
    // State
    teams,
    standings,
    fixtures,
    selectedTeam,
    teamForm,
    loading,
    error,
    
    // Computed
    newcastlePosition,
    newcastleTeam,
    recentFixtures,
    upcomingFixtures,
    
    // Actions
    setLoading,
    setError,
    clearError,
    fetchTeams,
    fetchStandings,
    fetchFixtures,
    fetchTeamDetail,
    fetchTeamForm,
    initializeDashboard,
    clearSelectedTeam,
    clearTeamForm
  }
})
import { apiClient } from './apiClient'
import type {
  InvestmentGoal,
  InvestmentGoalCreate,
  InvestmentGoalUpdate,
  InvestmentGoalList,
  FinancialPlan,
  FinancialPlanCreate,
  FinancialPlanUpdate,
  FinancialPlanList,
  RetirementPlan,
  RetirementPlanCreate,
  RetirementPlanUpdate,
  RetirementPlanList,
  WealthHistory,
  WealthHistoryCreate,
  WealthHistoryUpdate,
  WealthHistoryList,
  PortfolioProjectionRequest,
  PortfolioProjectionResponse,
  ContributionSimulationRequest,
  ContributionSimulationResponse,
  WealthAnalysisResponse
} from './types'

export const financialPlanningApi = {
  // Investment Goals
  async getGoals(): Promise<InvestmentGoalList> {
    const response = await apiClient.get<InvestmentGoalList>('/financial-planning/goals')
    return response.data
  },

  async createGoal(data: InvestmentGoalCreate): Promise<InvestmentGoal> {
    const response = await apiClient.post<InvestmentGoal>('/financial-planning/goals', data)
    return response.data
  },

  async getGoal(goalId: number): Promise<InvestmentGoal> {
    const response = await apiClient.get<InvestmentGoal>(`/financial-planning/goals/${goalId}`)
    return response.data
  },

  async updateGoal(goalId: number, data: InvestmentGoalUpdate): Promise<InvestmentGoal> {
    const response = await apiClient.patch<InvestmentGoal>(`/financial-planning/goals/${goalId}`, data)
    return response.data
  },

  async deleteGoal(goalId: number): Promise<void> {
    await apiClient.delete(`/financial-planning/goals/${goalId}`)
  },

  // Financial Plans
  async getPlans(): Promise<FinancialPlanList> {
    const response = await apiClient.get<FinancialPlanList>('/financial-planning/plans')
    return response.data
  },

  async createPlan(data: FinancialPlanCreate): Promise<FinancialPlan> {
    const response = await apiClient.post<FinancialPlan>('/financial-planning/plans', data)
    return response.data
  },

  async getPlan(planId: number): Promise<FinancialPlan> {
    const response = await apiClient.get<FinancialPlan>(`/financial-planning/plans/${planId}`)
    return response.data
  },

  async updatePlan(planId: number, data: FinancialPlanUpdate): Promise<FinancialPlan> {
    const response = await apiClient.patch<FinancialPlan>(`/financial-planning/plans/${planId}`, data)
    return response.data
  },

  async deletePlan(planId: number): Promise<void> {
    await apiClient.delete(`/financial-planning/plans/${planId}`)
  },

  // Retirement Plans
  async getRetirementPlans(): Promise<RetirementPlanList> {
    const response = await apiClient.get<RetirementPlanList>('/financial-planning/retirement')
    return response.data
  },

  async createRetirementPlan(data: RetirementPlanCreate): Promise<RetirementPlan> {
    const response = await apiClient.post<RetirementPlan>('/financial-planning/retirement', data)
    return response.data
  },

  async getRetirementPlan(planId: number): Promise<RetirementPlan> {
    const response = await apiClient.get<RetirementPlan>(`/financial-planning/retirement/${planId}`)
    return response.data
  },

  async updateRetirementPlan(planId: number, data: RetirementPlanUpdate): Promise<RetirementPlan> {
    const response = await apiClient.patch<RetirementPlan>(`/financial-planning/retirement/${planId}`, data)
    return response.data
  },

  async deleteRetirementPlan(planId: number): Promise<void> {
    await apiClient.delete(`/financial-planning/retirement/${planId}`)
  },

  // Portfolio Projections
  async calculateProjection(data: PortfolioProjectionRequest): Promise<PortfolioProjectionResponse> {
    const response = await apiClient.post<PortfolioProjectionResponse>('/financial-planning/projections', data)
    return response.data
  },

  // Contribution Simulator
  async simulateContributions(data: ContributionSimulationRequest): Promise<ContributionSimulationResponse> {
    const response = await apiClient.post<ContributionSimulationResponse>('/financial-planning/simulate-contributions', data)
    return response.data
  },

  // Wealth History
  async getWealthHistory(): Promise<WealthHistoryList> {
    const response = await apiClient.get<WealthHistoryList>('/financial-planning/wealth-history')
    return response.data
  },

  async createWealthHistory(data: WealthHistoryCreate): Promise<WealthHistory> {
    const response = await apiClient.post<WealthHistory>('/financial-planning/wealth-history', data)
    return response.data
  },

  async getWealthHistoryItem(historyId: number): Promise<WealthHistory> {
    const response = await apiClient.get<WealthHistory>(`/financial-planning/wealth-history/${historyId}`)
    return response.data
  },

  async updateWealthHistory(historyId: number, data: WealthHistoryUpdate): Promise<WealthHistory> {
    const response = await apiClient.patch<WealthHistory>(`/financial-planning/wealth-history/${historyId}`, data)
    return response.data
  },

  async deleteWealthHistory(historyId: number): Promise<void> {
    await apiClient.delete(`/financial-planning/wealth-history/${historyId}`)
  },

  // Wealth Analysis
  async getWealthAnalysis(): Promise<WealthAnalysisResponse> {
    const response = await apiClient.get<WealthAnalysisResponse>('/financial-planning/wealth-analysis')
    return response.data
  },
}


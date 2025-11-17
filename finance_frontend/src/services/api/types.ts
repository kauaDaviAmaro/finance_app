// Auth Types
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: number
  email: string
  username: string
  role: 'ADMIN' | 'PRO' | 'USER'
  subscription_status?: string | null
  created_at?: string
  two_factor_enabled?: boolean
}

// Stock Types
export interface HistoricalPrice {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface TickerHistoricalData {
  ticker: string
  period: string
  data: HistoricalPrice[]
}

export interface TechnicalIndicator {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  macd?: number
  macd_signal?: number
  macd_histogram?: number
  stochastic_k?: number
  stochastic_d?: number
  atr?: number
  bb_lower?: number
  bb_middle?: number
  bb_upper?: number
  obv?: number
  rsi?: number
}

export interface TechnicalAnalysis {
  ticker: string
  period: string
  data: TechnicalIndicator[]
}

export interface Fundamentals {
  ticker: string
  pe_ratio?: number
  pb_ratio?: number
  dividend_yield?: number
  beta?: number
  sector?: string
  industry?: string
  market_cap?: number
  roe?: number
  roa?: number
  net_margin?: number
  debt_to_equity?: number
  ev_ebitda?: number
  pebit_ratio?: number
  quality_score?: number
}

export interface TickerRequest {
  ticker: string
  period?: string
}

export interface MostSearchedTicker {
  ticker: string
  search_count: number
}

export interface TickerComparisonRequest {
  ticker1: string
  ticker2: string
  period?: string
}

export interface TickerComparison {
  ticker1: string
  ticker2: string
  period: string
  ticker1_data: TechnicalAnalysis
  ticker2_data: TechnicalAnalysis
  ticker1_fundamentals: Fundamentals
  ticker2_fundamentals: Fundamentals
}

// Financial Statements Types
export interface FinancialStatementRow {
  account: string
  values: Record<string, number | null>
}

export interface IncomeStatement {
  ticker: string
  periods: string[]
  data: FinancialStatementRow[]
}

export interface BalanceSheet {
  ticker: string
  periods: string[]
  data: FinancialStatementRow[]
}

export interface CashFlow {
  ticker: string
  periods: string[]
  data: FinancialStatementRow[]
}

export interface FinancialStatements {
  ticker: string
  income_statement: IncomeStatement
  balance_sheet: BalanceSheet
  cash_flow: CashFlow
}

// Portfolio Types
export interface Portfolio {
  id: number
  name: string
  category?: string | null
  description?: string | null
  created_at: string
  updated_at?: string | null
  item_count?: number
}

export interface PortfolioList {
  portfolios: Portfolio[]
}

export interface PortfolioCreate {
  name: string
  category?: string | null
  description?: string | null
}

export interface PortfolioUpdate {
  name?: string
  category?: string | null
  description?: string | null
}

export interface PortfolioItem {
  id: number
  portfolio_id: number
  ticker: string
  quantity: number
  purchase_price: number
  purchase_date: string
  sold_price?: number
  sold_date?: string
  realized_pnl?: number
  unrealized_pnl?: number
  current_price?: number
  created_at: string
  updated_at?: string
}

export interface PortfolioSummary {
  total_invested: number
  total_realized_pnl: number
  total_unrealized_pnl: number
  positions: PortfolioItem[]
}

export interface PortfolioItemCreate {
  portfolio_id: number
  ticker: string
  quantity: number
  purchase_price: number
  purchase_date: string
}

export interface PortfolioItemUpdate {
  sold_price: number
  sold_date: string
}

// Watchlist Types
export interface WatchlistItem {
  id: number
  ticker: string
  created_at: string
}

export interface WatchlistResponse {
  items: WatchlistItem[]
}

// Alert Types
export interface Alert {
  id: number
  ticker: string
  indicator_type: string
  condition: string
  threshold_value?: number
  is_active: boolean
  triggered_at?: string
  created_at: string
}

export interface AlertListResponse {
  alerts: Alert[]
}

export interface AlertCreate {
  ticker: string
  indicator_type: string
  condition: string
  threshold_value?: number
}

// Subscription Types
export interface SubscriptionStatus {
  role: 'ADMIN' | 'PRO' | 'USER'
  subscription_status: string | null
  is_pro: boolean
}

export interface CheckoutSessionResponse {
  url: string
  session_id: string
}

export interface PortalSessionResponse {
  url: string
}


// Profile Types
export interface UserUpdate {
  email?: string
  username?: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}


// Scanner Types
export interface ScannerRow {
  ticker: string
  last_price: number | null
  rsi_14: number | null
  macd_h: number | null
  bb_upper: number | null
  bb_lower: number | null
  timestamp: string
  quality_score?: number | null
}

export type ScannerSort = 'rsi_asc' | 'rsi_desc' | 'macd_desc'

// Backtesting Types
export type StrategyType = 'GRAPHICAL' | 'JSON'
export type ConditionType = 'ENTRY' | 'EXIT'
export type ConditionLogic = 'AND' | 'OR'
export type PaperTradeStatus = 'ACTIVE' | 'PAUSED' | 'STOPPED'

export interface StrategyCondition {
  id?: number
  strategy_id?: number
  condition_type: ConditionType
  indicator: string
  operator: string
  value?: number | null
  logic: ConditionLogic
  order: number
}

export interface StrategyConditionCreate {
  condition_type: ConditionType
  indicator: string
  operator: string
  value?: number | null
  logic?: ConditionLogic
  order?: number
}

export interface Strategy {
  id: number
  user_id: number
  name: string
  description?: string | null
  strategy_type: StrategyType
  json_config?: Record<string, any> | null
  initial_capital: number
  position_size: number
  created_at: string
  updated_at?: string | null
  conditions: StrategyCondition[]
}

export interface StrategyCreate {
  name: string
  description?: string | null
  strategy_type?: StrategyType
  json_config?: Record<string, any> | null
  initial_capital?: number
  position_size?: number
  conditions: StrategyConditionCreate[]
}

export interface StrategyCreateJSON {
  name: string
  description?: string | null
  json_config: Record<string, any>
  initial_capital?: number
  position_size?: number
}

export interface StrategyUpdate {
  name?: string
  description?: string | null
  initial_capital?: number
  position_size?: number
  conditions?: StrategyConditionCreate[]
}

export interface BacktestRunRequest {
  strategy_id: number
  ticker: string
  period?: string
}

export interface BacktestTrade {
  id: number
  backtest_id: number
  trade_date: string
  trade_type: string
  price: number
  quantity: number
  pnl?: number | null
  capital_after?: number | null
}

export interface Backtest {
  id: number
  user_id: number
  strategy_id: number
  ticker: string
  period: string
  start_date?: string | null
  end_date?: string | null
  total_return?: number | null
  annualized_return?: number | null
  sharpe_ratio?: number | null
  max_drawdown?: number | null
  win_rate?: number | null
  profit_factor?: number | null
  total_trades: number
  winning_trades: number
  losing_trades: number
  avg_win?: number | null
  avg_loss?: number | null
  final_capital?: number | null
  created_at: string
  trades: BacktestTrade[]
}

export interface BacktestResultDetail {
  backtest: Backtest
  equity_curve: Array<{ date: string; equity: number }>
}

export interface BacktestCompareRequest {
  strategy_ids: number[]
  ticker: string
  period?: string
}

export interface BacktestCompareResult {
  ticker: string
  period: string
  strategies: Backtest[]
}

export interface PaperTradeStartRequest {
  strategy_id: number
  ticker: string
  initial_capital?: number
}

export interface PaperTradePosition {
  id: number
  paper_trade_id: number
  ticker: string
  quantity: number
  entry_price: number
  entry_date: string
  exit_price?: number | null
  exit_date?: string | null
  pnl?: number | null
}

export interface PaperTrade {
  id: number
  user_id: number
  strategy_id: number
  ticker: string
  initial_capital: number
  current_capital: number
  status: PaperTradeStatus
  started_at: string
  stopped_at?: string | null
  last_update: string
  positions: PaperTradePosition[]
}

export interface PaperTradeStatusOut {
  paper_trade: PaperTrade
  current_equity: number
  total_return: number
  open_positions_count: number
  positions_value: number
}

export interface PaperTradeSignal {
  entry_signal: boolean
  exit_signal: boolean
  current_price: number
  timestamp: string
}

// Risk Management Types
export interface VarResult {
  var_value: number | null
  var_percentage: number | null
  method: string
  confidence_level: number
  horizon_days: number
  error?: string | null
}

export interface DrawdownPoint {
  date: string
  value: number
  drawdown: number
}

export interface DrawdownAnalysis {
  max_drawdown: number | null
  current_drawdown: number | null
  max_drawdown_date: string | null
  recovery_days: number | null
  drawdown_history: DrawdownPoint[]
}

export interface PositionBeta {
  ticker: string
  beta: number | null
  error?: string | null
}

export interface BetaAnalysis {
  portfolio_beta: number | null
  position_betas: PositionBeta[]
  benchmark: string
  error?: string | null
}

export interface PositionVolatility {
  ticker: string
  volatility: number | null
  error?: string | null
}

export interface VolatilityAnalysis {
  portfolio_volatility: number | null
  position_volatilities: PositionVolatility[]
}

export interface TickerConcentration {
  ticker: string
  weight: number
}

export interface SectorDiversification {
  sector: string
  weight: number
  industries: string[]
  tickers: string[]
}

export interface DiversificationMetrics {
  herfindahl_index: number | null
  concentration_by_ticker: TickerConcentration[]
  sector_diversification: SectorDiversification[]
  effective_positions: number | null
  warnings: string[]
}

export interface RiskMetrics {
  var: VarResult
  drawdown: DrawdownAnalysis
  beta: BetaAnalysis
  volatility: VolatilityAnalysis
  diversification: DiversificationMetrics
}

export interface PositionCorrelation {
  ticker: string
  correlation: number
}

export interface PositionRiskAnalysis {
  ticker: string
  var: number | null
  var_percentage: number | null
  beta: number | null
  volatility: number | null
  portfolio_weight: number
  correlations: PositionCorrelation[]
  stop_loss: number | null
  take_profit: number | null
  stop_loss_percentage: number | null
  take_profit_percentage: number | null
  error?: string | null
}

export interface PortfolioRiskAnalysis {
  portfolio_id: number
  metrics: RiskMetrics
  position_analyses: PositionRiskAnalysis[]
}


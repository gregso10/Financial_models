const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// === SIMPLE MODE ===

export interface SimpleSimulationRequest {
  location: string;
  price: number;
  surface_sqm: number;
  monthly_rent: number;
  apport: number;
  loan_rate?: number;
}

// === EXPERT MODE ===

export type LeaseType = 'furnished_1yr' | 'unfurnished_3yr' | 'airbnb';

export interface ExpertSimulationRequest {
  // Property
  location: string;
  property_price: number;
  surface_sqm: number;
  agency_fees_pct?: number;
  notary_fees_pct?: number;
  initial_renovation?: number;
  furnishing_costs?: number;
  
  // Financing
  apport?: number;
  loan_rate?: number;
  loan_duration_years?: number;
  loan_insurance_rate?: number;
  
  // Rental
  lease_type?: LeaseType;
  monthly_rent?: number;
  daily_rate?: number;
  vacancy_rate?: number;
  occupancy_rate?: number;
  rent_growth_rate?: number;
  
  // Expenses
  property_tax_yearly?: number;
  condo_fees_monthly?: number;
  pno_insurance_yearly?: number;
  maintenance_pct?: number;
  management_fee_pct?: number;
  
  // Fiscal
  tmi?: number;
  
  // Exit
  holding_years?: number;
  property_growth_rate?: number;
  exit_fees_pct?: number;
  
  // Analysis
  discount_rate?: number;
}

// === SHARED RESPONSE TYPES ===

export interface SimulationMetrics {
  irr: number;
  npv: number;
  monthly_cashflow: number;
  cash_on_cash: number;
  equity_multiple: number;
  exit_property_value: number;
  net_exit_proceeds: number;
  capital_gains_tax: number;
  capital_gain: number;
  remaining_loan: number;
  selling_costs: number;
}

export interface FiscalScenario {
  regime: string;
  gross_revenue: number;
  taxable_income: number;
  total_tax: number;
  effective_rate: number;
}

export interface FiscalComparison {
  recommended: string;
  reason: string;
  annual_savings: number;
  micro: FiscalScenario;
  reel: FiscalScenario;
}

export interface YearlyCashFlow {
  year: number;
  net_change: number;
  cumulative: number;
}

export interface Alert {
  type: 'success' | 'warning' | 'error';
  icon: string;
  message_fr: string;
  message_en: string;
}

export interface LMPStatus {
  is_lmp: boolean;
  revenue_threshold_met: boolean;
  income_condition_met: boolean;
  annual_revenue: number;
  threshold: number;
  implications?: Record<string, string>;
  implications_fr?: Record<string, string>;
  implications_en?: Record<string, string>;
}

export interface SimulationResponse {
  success: boolean;
  metrics?: SimulationMetrics;
  fiscal?: FiscalComparison;
  yearly_cashflows?: YearlyCashFlow[];
  alerts?: Alert[];
  error?: string;
}

export interface ExpertSimulationResponse extends SimulationResponse {
  lmp_status?: LMPStatus;
}

// === FISCAL COMPARISON ===

export interface FiscalComparisonRequest {
  gross_revenue: number;
  deductible_expenses?: number;
  depreciation?: number;
  lease_type?: LeaseType;
  tmi?: number;
  holding_years?: number;
}

export interface FiscalComparisonResponse {
  recommended: string;
  reason_fr: string;
  reason_en: string;
  annual_savings: number;
  total_savings: number;
  micro: FiscalScenario;
  reel: FiscalScenario;
}

// === LMP CHECK ===

export interface LMPCheckRequest {
  annual_revenue: number;
  other_income?: number;
}

export interface LMPCheckResponse {
  is_lmp: boolean;
  revenue_threshold_met: boolean;
  income_condition_met: boolean;
  annual_revenue: number;
  threshold: number;
  implications_fr: Record<string, string>;
  implications_en: Record<string, string>;
}

// === SENSITIVITY ===

export interface SensitivityRequest {
  base_params: ExpertSimulationRequest;
  variable: 'loan_rate' | 'property_growth_rate';
  range_min?: number;
  range_max?: number;
  steps?: number;
}

export interface SensitivityPoint {
  value: number;
  irr: number;
  npv: number;
  monthly_cashflow: number;
}

export interface SensitivityResponse {
  success: boolean;
  variable: string;
  base_value: number;
  points?: SensitivityPoint[];
  error?: string;
}

// === API FUNCTIONS ===

export async function simulateSimple(data: SimpleSimulationRequest): Promise<SimulationResponse> {
  const res = await fetch(`${API_URL}/api/v1/simulate/simple`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function simulateExpert(data: ExpertSimulationRequest): Promise<ExpertSimulationResponse> {
  const res = await fetch(`${API_URL}/api/v1/expert/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function compareFiscalRegimes(data: FiscalComparisonRequest): Promise<FiscalComparisonResponse> {
  const res = await fetch(`${API_URL}/api/v1/expert/fiscal/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function checkLMPStatus(data: LMPCheckRequest): Promise<LMPCheckResponse> {
  const res = await fetch(`${API_URL}/api/v1/expert/fiscal/lmp-check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function runSensitivityAnalysis(data: SensitivityRequest): Promise<SensitivityResponse> {
  const res = await fetch(`${API_URL}/api/v1/expert/sensitivity`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getLocations(): Promise<string[]> {
  const res = await fetch(`${API_URL}/api/v1/data/locations`);
  const data = await res.json();
  return data.locations;
}

export async function getLocationDefaults(location: string): Promise<Record<string, number>> {
  const res = await fetch(`${API_URL}/api/v1/data/locations/${encodeURIComponent(location)}`);
  return res.json();
}
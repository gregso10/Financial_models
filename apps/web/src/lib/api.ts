const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface SimulationRequest {
  location: string;
  price: number;
  surface_sqm: number;
  monthly_rent: number;
  apport: number;
  loan_rate?: number;
}

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

export interface SimulationResponse {
  success: boolean;
  metrics?: SimulationMetrics;
  fiscal?: FiscalComparison;
  yearly_cashflows?: YearlyCashFlow[];
  alerts?: Alert[];
  error?: string;
}

export async function simulateSimple(data: SimulationRequest): Promise<SimulationResponse> {
  const res = await fetch(`${API_URL}/api/v1/simulate/simple`, {
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
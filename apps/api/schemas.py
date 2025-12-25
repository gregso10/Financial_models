from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class SimpleSimulationRequest(BaseModel):
    location: str = "Paris"
    price: float = Field(..., gt=0)
    surface_sqm: float = Field(..., gt=0)
    monthly_rent: float = Field(..., gt=0)
    apport: float = Field(0, ge=0)
    loan_rate: float = Field(0.035, ge=0, le=0.15)

class SimulationMetrics(BaseModel):
    irr: float
    npv: float
    monthly_cashflow: float
    cash_on_cash: float
    equity_multiple: float
    exit_property_value: float
    net_exit_proceeds: float
    capital_gains_tax: float
    capital_gain: float
    remaining_loan: float
    selling_costs: float

class FiscalScenario(BaseModel):
    regime: str
    gross_revenue: float
    taxable_income: float
    total_tax: float
    effective_rate: float

class FiscalComparison(BaseModel):
    recommended: str
    reason: str
    annual_savings: float
    micro: FiscalScenario
    reel: FiscalScenario

class YearlyCashFlow(BaseModel):
    year: int
    net_change: float
    cumulative: float

class Alert(BaseModel):
    type: str  # success, warning, error
    icon: str
    message_fr: str
    message_en: str

class SimulationResponse(BaseModel):
    success: bool
    metrics: Optional[SimulationMetrics] = None
    fiscal: Optional[FiscalComparison] = None
    yearly_cashflows: Optional[List[YearlyCashFlow]] = None
    alerts: Optional[List[Alert]] = None
    error: Optional[str] = None

class LocationDefaults(BaseModel):
    notary_pct: float
    property_tax_per_sqm: float
    condo_fees_per_sqm: float
    vacancy_rate: float
    rent_per_sqm_furnished: float
    price_growth: float
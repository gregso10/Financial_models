"""
API Schemas for Immo Invest
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


# === ENUMS ===

class LeaseTypeEnum(str, Enum):
    FURNISHED_1YR = "furnished_1yr"
    UNFURNISHED_3YR = "unfurnished_3yr"
    AIRBNB = "airbnb"


# === SIMPLE MODE REQUEST ===

class SimpleSimulationRequest(BaseModel):
    location: str = "Paris"
    price: float = Field(..., gt=0)
    surface_sqm: float = Field(..., gt=0)
    monthly_rent: float = Field(..., gt=0)
    apport: float = Field(0, ge=0)
    loan_rate: float = Field(0.035, ge=0, le=0.15)


# === SIMPLE MODE RESPONSE COMPONENTS (must be defined before SimulationResponse) ===

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


class YearlyCashFlow(BaseModel):
    year: int
    net_change: float
    cumulative: float


class Alert(BaseModel):
    type: str  # "success", "warning", "error"
    icon: str
    message_fr: str
    message_en: str


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


# === SIMPLE MODE RESPONSE ===

class SimulationResponse(BaseModel):
    success: bool
    metrics: Optional[SimulationMetrics] = None
    fiscal: Optional[FiscalComparison] = None
    yearly_cashflows: Optional[List[YearlyCashFlow]] = None
    alerts: Optional[List[Alert]] = None
    error: Optional[str] = None


# === DATA ===

class LocationDefaults(BaseModel):
    notary_pct: float
    property_tax_per_sqm: float
    condo_fees_per_sqm: float
    pno_insurance: float
    vacancy_rate: float
    price_growth: float
    rent_per_sqm_furnished: float
    rent_per_sqm_unfurnished: float
    management_fee_pct: float
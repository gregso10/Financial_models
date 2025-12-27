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

# === EXPERT MODE ===

class ExpertSimulationRequest(BaseModel):
    """Full parameter set for expert mode simulation."""
    # Property
    location: str = "Paris"
    property_price: float = Field(..., gt=0)
    surface_sqm: float = Field(..., gt=0)
    agency_fees_pct: float = Field(0.0, ge=0, le=0.10)
    notary_fees_pct: float = Field(0.08, ge=0, le=0.15)
    initial_renovation: float = Field(0, ge=0)
    furnishing_costs: float = Field(0, ge=0)
    
    # Financing
    apport: float = Field(0, ge=0)
    loan_rate: float = Field(0.035, ge=0, le=0.15)
    loan_duration_years: int = Field(20, ge=5, le=30)
    loan_insurance_rate: float = Field(0.003, ge=0, le=0.01)
    
    # Rental
    lease_type: LeaseTypeEnum = LeaseTypeEnum.FURNISHED_1YR
    monthly_rent: Optional[float] = None
    daily_rate: Optional[float] = None
    vacancy_rate: float = Field(0.05, ge=0, le=0.30)
    occupancy_rate: Optional[float] = Field(0.70, ge=0.3, le=1.0)
    rent_growth_rate: float = Field(0.015, ge=-0.05, le=0.10)
    
    # Expenses
    property_tax_yearly: Optional[float] = None
    condo_fees_monthly: Optional[float] = None
    pno_insurance_yearly: float = Field(150, ge=0)
    maintenance_pct: float = Field(0.05, ge=0, le=0.20)
    management_fee_pct: float = Field(0.07, ge=0, le=0.30)
    
    # Fiscal
    tmi: float = Field(0.30, ge=0, le=0.45)
    
    # Exit
    holding_years: int = Field(10, ge=1, le=30)
    property_growth_rate: float = Field(0.02, ge=-0.05, le=0.10)
    exit_fees_pct: float = Field(0.05, ge=0, le=0.10)
    
    # Analysis
    discount_rate: float = Field(0.05, ge=0, le=0.15)


class ExpertSimulationResponse(BaseModel):
    """Expert mode returns same structure as simple + extras."""
    success: bool
    metrics: Optional[SimulationMetrics] = None
    fiscal: Optional[FiscalComparison] = None
    yearly_cashflows: Optional[List[YearlyCashFlow]] = None
    alerts: Optional[List[Alert]] = None
    lmp_status: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FiscalComparisonRequest(BaseModel):
    gross_revenue: float = Field(..., gt=0)
    deductible_expenses: float = Field(0, ge=0)
    depreciation: float = Field(0, ge=0)
    lease_type: LeaseTypeEnum = LeaseTypeEnum.FURNISHED_1YR
    tmi: float = Field(0.30, ge=0, le=0.45)
    holding_years: int = Field(10, ge=1, le=30)


class FiscalComparisonResponse(BaseModel):
    recommended: str
    reason_fr: str
    reason_en: str
    annual_savings: float
    total_savings: float
    micro: FiscalScenario
    reel: FiscalScenario


class LMPCheckRequest(BaseModel):
    annual_revenue: float = Field(..., gt=0)
    other_income: float = Field(0, ge=0)


class LMPCheckResponse(BaseModel):
    is_lmp: bool
    revenue_threshold_met: bool
    income_condition_met: bool
    annual_revenue: float
    threshold: float
    implications_fr: Dict[str, str]
    implications_en: Dict[str, str]


class SensitivityRequest(BaseModel):
    base_params: ExpertSimulationRequest
    variable: str = "loan_rate"  # or "property_growth_rate"
    range_min: float = Field(-0.02)
    range_max: float = Field(0.02)
    steps: int = Field(5, ge=3, le=10)


class SensitivityPoint(BaseModel):
    value: float
    irr: float
    npv: float
    monthly_cashflow: float


class SensitivityResponse(BaseModel):
    success: bool
    variable: str
    base_value: float
    points: Optional[List[SensitivityPoint]] = None
    error: Optional[str] = None
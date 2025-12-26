"""
Immo Core - French Real Estate Investment Analysis Package
"""

__version__ = "0.1.0"

from .models.params import ModelParameters
from .models.financial import FinancialModel

__all__ = ["ModelParameters", "FinancialModel"]
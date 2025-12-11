# In file: scripts/_12_excel_exporter.py

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from typing import Dict, Optional
from io import BytesIO


class ExcelExporter:
    """
    Exports financial model to Excel with formulas, formatting, and linked sheets.
    Follows accounting conventions: brackets for negatives, sums only for totals.
    """
    
    # Style constants
    BLUE_INPUT = Font(color="0000FF", bold=False)
    BLACK_FORMULA = Font(color="000000", bold=False)
    BOLD = Font(bold=True)
    BOLD_TOTAL = Font(bold=True, color="000000")
    
    HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
    HEADER_FONT = Font(color="FFFFFF", bold=True)
    SUBTOTAL_FILL = PatternFill("solid", fgColor="D9E2F3")
    TOTAL_FILL = PatternFill("solid", fgColor="BDD7EE")
    
    THIN_BORDER = Border(
        bottom=Side(style='thin', color='000000')
    )
    THICK_BORDER = Border(
        top=Side(style='medium', color='000000'),
        bottom=Side(style='double', color='000000')
    )
    
    # Number formats (no currency symbol, brackets for negatives)
    NUM_FORMAT = '#,##0;(#,##0);"-"'
    NUM_FORMAT_DEC = '#,##0.00;(#,##0.00);"-"'
    PCT_FORMAT = '0.0%;(0.0%);"-"'
    
    def __init__(self, params, pnl_df: pd.DataFrame, bs_df: pd.DataFrame, 
                 cf_df: pd.DataFrame, loan_schedule: pd.DataFrame,
                 investment_metrics: Dict):
        self.params = params
        self.pnl_df = pnl_df
        self.bs_df = bs_df
        self.cf_df = cf_df
        self.loan_schedule = loan_schedule
        self.metrics = investment_metrics or {}
        self.wb = Workbook()
        
    def export(self) -> BytesIO:
        """Generate Excel workbook and return as BytesIO for download."""
        # Remove default sheet
        self.wb.remove(self.wb.active)
        
        # Create sheets in order
        self._create_assumptions_sheet()
        self._create_pnl_sheet()
        self._create_bs_sheet()
        self._create_cf_sheet()
        self._create_loan_sheet()
        self._create_metrics_sheet()
        
        # Save to BytesIO
        output = BytesIO()
        self.wb.save(output)
        output.seek(0)
        return output
    
    def _create_assumptions_sheet(self):
        """Create Assumptions tab with all input parameters."""
        ws = self.wb.create_sheet("Assumptions")
        
        # Define assumptions with named ranges
        assumptions = [
            ("PROPERTY & ACQUISITION", None, None),
            ("Property Price (FAI)", self.params.property_price, "property_price"),
            ("Property Size (sqm)", self.params.property_size_sqm, "property_size"),
            ("Agency Fees %", self.params.agency_fees_percentage, "agency_fees_pct"),
            ("Notary Fees %", self.params.notary_fees_percentage_estimate, "notary_fees_pct"),
            ("Initial Renovation", self.params.initial_renovation_costs, "renovation_costs"),
            ("Furnishing Costs", self.params.furnishing_costs, "furnishing_costs"),
            ("", None, None),
            ("FINANCING", None, None),
            ("Loan Percentage", self.params.loan_percentage, "loan_pct"),
            ("Loan Interest Rate", self.params.loan_interest_rate, "loan_rate"),
            ("Loan Duration (Years)", self.params.loan_duration_years, "loan_years"),
            ("Loan Insurance Rate", self.params.loan_insurance_rate, "loan_insurance_rate"),
            ("", None, None),
            ("OPERATING EXPENSES", None, None),
            ("Property Tax (Yearly)", self.params.property_tax_yearly, "property_tax"),
            ("Condo Fees (Monthly)", self.params.condo_fees_monthly, "condo_fees"),
            ("PNO Insurance (Yearly)", self.params.pno_insurance_yearly, "pno_insurance"),
            ("Maintenance % of Rent", self.params.maintenance_percentage_rent, "maintenance_pct"),
            ("Expenses Growth Rate", self.params.expenses_growth_rate, "expenses_growth"),
            ("", None, None),
            ("FISCAL PARAMETERS", None, None),
            ("Fiscal Regime", self.params.fiscal_regime, None),
            ("Income Tax Bracket (TMI)", self.params.personal_income_tax_bracket, "tmi"),
            ("Social Contributions Rate", self.params.social_contributions_rate, "social_rate"),
            ("", None, None),
            ("EXIT PARAMETERS", None, None),
            ("Holding Period (Years)", self.params.holding_period_years, "holding_years"),
            ("Property Growth Rate", self.params.property_value_growth_rate, "property_growth"),
            ("Selling Fees %", self.params.exit_selling_fees_percentage, "selling_fees_pct"),
            ("", None, None),
            ("INVESTMENT ANALYSIS", None, None),
            ("Risk-Free Rate", getattr(self.params, 'risk_free_rate', 0.035), "risk_free"),
            ("Discount Rate", getattr(self.params, 'discount_rate', 0.05), "discount_rate"),
        ]
        
        # Write assumptions
        row = 1
        for label, value, name in assumptions:
            if value is None and name is None and label:
                # Section header
                ws.cell(row=row, column=1, value=label)
                ws.cell(row=row, column=1).font = self.BOLD
                ws.cell(row=row, column=1).fill = self.HEADER_FILL
                ws.cell(row=row, column=1).font = self.HEADER_FONT
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
            elif label == "":
                pass  # Empty row
            else:
                ws.cell(row=row, column=1, value=label)
                cell = ws.cell(row=row, column=2, value=value)
                cell.font = self.BLUE_INPUT
                
                # Format based on type
                if isinstance(value, float):
                    if "%" in label or "Rate" in label:
                        cell.number_format = self.PCT_FORMAT
                    else:
                        cell.number_format = self.NUM_FORMAT
                
                # Create named range if specified
                if name:
                    self.wb.defined_names.add(
                        self.wb.defined_names.add.__class__(name, f"Assumptions!$B${row}")
                    )
            row += 1
        
        # Column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 15
        
    def _create_pnl_sheet(self):
        """Create P&L tab with yearly data and formulas."""
        ws = self.wb.create_sheet("P&L")
        
        # Aggregate to yearly
        pnl_yearly = self.pnl_df.groupby("Year").sum()
        
        # Define row structure with sign handling
        # Positive = inflow, stored as positive
        # Expenses stored as positive (will show in brackets via format)
        pnl_rows = [
            ("Gross Potential Rent", "Gross Potential Rent", 1, False),
            ("Vacancy Loss", "Vacancy Loss", -1, True),  # Show as negative (expense)
            ("Gross Operating Income", "GOI", None, False),  # Formula
            ("", None, None, False),
            ("Property Tax", "Property Tax", -1, True),
            ("Condo Fees", "Condo Fees", -1, True),
            ("PNO Insurance", "PNO Insurance", -1, True),
            ("Maintenance", "Maintenance", -1, True),
            ("Management Fees", "Management Fees", -1, True),
            ("Total Operating Expenses", "OpEx", None, True),  # Formula
            ("Net Operating Income", "NOI", None, False),  # Formula
            ("", None, None, False),
            ("Loan Interest", "Loan Interest", -1, True),
            ("Loan Insurance", "Loan Insurance", -1, True),
            ("Depreciation/Amortization", "Depreciation/Amortization", -1, True),
            ("Taxable Income", "Taxable Income", None, False),
            ("", None, None, False),
            ("Income Tax", "Income Tax", -1, True),
            ("Social Contributions", "Social Contributions", -1, True),
            ("Total Taxes", "Total Taxes", None, True),  # Formula
            ("Net Income", "Net Income", None, False),  # Formula
        ]
        
        years = list(pnl_yearly.index)
        
        # Header row
        ws.cell(row=1, column=1, value="P&L Statement (€)")
        ws.cell(row=1, column=1).font = self.HEADER_FONT
        ws.cell(row=1, column=1).fill = self.HEADER_FILL
        
        for col_idx, year in enumerate(years, start=2):
            cell = ws.cell(row=1, column=col_idx, value=f"Year {year}")
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = Alignment(horizontal='center')
        
        # Data rows
        row_map = {}  # Track row numbers for formula references
        current_row = 2
        
        for label, col_name, sign, is_expense in pnl_rows:
            if label == "":
                current_row += 1
                continue
                
            ws.cell(row=current_row, column=1, value=label)
            row_map[label] = current_row
            
            if col_name and col_name in pnl_yearly.columns:
                # Data row
                for col_idx, year in enumerate(years, start=2):
                    value = pnl_yearly.loc[year, col_name]
                    if sign:
                        value = value * sign  # Flip sign for expenses
                    cell = ws.cell(row=current_row, column=col_idx, value=abs(value) if is_expense else value)
                    cell.number_format = self.NUM_FORMAT
                    if is_expense and value != 0:
                        # Store as negative for bracket display
                        cell.value = -abs(value)
            
            elif col_name is None and label in ["Gross Operating Income", "Total Operating Expenses", 
                                                  "Net Operating Income", "Taxable Income", 
                                                  "Total Taxes", "Net Income"]:
                # Formula rows
                for col_idx, year in enumerate(years, start=2):
                    col_letter = get_column_letter(col_idx)
                    
                    if label == "Gross Operating Income":
                        formula = f"={col_letter}{row_map['Gross Potential Rent']}+{col_letter}{row_map['Vacancy Loss']}"
                    elif label == "Total Operating Expenses":
                        formula = f"=SUM({col_letter}{row_map['Property Tax']}:{col_letter}{row_map['Management Fees']})"
                    elif label == "Net Operating Income":
                        formula = f"={col_letter}{row_map['Gross Operating Income']}+{col_letter}{row_map['Total Operating Expenses']}"
                    elif label == "Taxable Income":
                        formula = f"={col_letter}{row_map['Net Operating Income']}+{col_letter}{row_map['Loan Interest']}+{col_letter}{row_map['Loan Insurance']}+{col_letter}{row_map['Depreciation/Amortization']}"
                    elif label == "Total Taxes":
                        formula = f"=SUM({col_letter}{row_map['Income Tax']}:{col_letter}{row_map['Social Contributions']})"
                    elif label == "Net Income":
                        formula = f"={col_letter}{row_map['Taxable Income']}+{col_letter}{row_map['Total Taxes']}"
                    
                    cell = ws.cell(row=current_row, column=col_idx, value=formula)
                    cell.number_format = self.NUM_FORMAT
                    cell.font = self.BLACK_FORMULA
            
            # Apply formatting
            if "Total" in label or label in ["Gross Operating Income", "Net Operating Income", 
                                              "Taxable Income", "Net Income"]:
                for col_idx in range(1, len(years) + 2):
                    ws.cell(row=current_row, column=col_idx).font = self.BOLD_TOTAL
                    if "Total" in label:
                        ws.cell(row=current_row, column=col_idx).fill = self.SUBTOTAL_FILL
                    if label == "Net Income":
                        ws.cell(row=current_row, column=col_idx).fill = self.TOTAL_FILL
                        ws.cell(row=current_row, column=col_idx).border = self.THICK_BORDER
            
            current_row += 1
        
        # Column widths
        ws.column_dimensions['A'].width = 30
        for col_idx in range(2, len(years) + 2):
            ws.column_dimensions[get_column_letter(col_idx)].width = 12
    
    def _create_bs_sheet(self):
        """Create Balance Sheet tab."""
        ws = self.wb.create_sheet("Balance Sheet")
        
        # Get yearly snapshots (end of each year)
        key_months = [0] + [12 * y for y in range(1, self.params.holding_period_years + 1)]
        bs_yearly = self.bs_df.loc[self.bs_df.index.intersection(key_months)]
        
        # Define rows
        bs_rows = [
            ("ASSETS", None, True),
            ("Property Net Value", "Property Net Value", False),
            ("Renovation Net Value", "Renovation Net Value", False),
            ("Furnishing Net Value", "Furnishing Net Value", False),
            ("Total Fixed Assets", "Total Fixed Assets", True),
            ("Cash", "Cash", False),
            ("Total Assets", "Total Assets", True),
            ("", None, False),
            ("LIABILITIES", None, True),
            ("Loan Balance", "Loan Balance", False),
            ("Total Liabilities", "Total Liabilities", True),
            ("", None, False),
            ("EQUITY", None, True),
            ("Initial Equity", "Initial Equity", False),
            ("Retained Earnings", "Retained Earnings", False),
            ("Total Equity", "Total Equity", True),
            ("", None, False),
            ("Total Liabilities & Equity", "Total Liabilities and Equity", True),
            ("Balance Check", "Balance Check", True),
        ]
        
        # Header
        ws.cell(row=1, column=1, value="Balance Sheet (€)")
        ws.cell(row=1, column=1).font = self.HEADER_FONT
        ws.cell(row=1, column=1).fill = self.HEADER_FILL
        
        col_idx = 2
        for month in bs_yearly.index:
            label = "Initial" if month == 0 else f"Year {month // 12}"
            cell = ws.cell(row=1, column=col_idx, value=label)
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = Alignment(horizontal='center')
            col_idx += 1
        
        # Data rows
        current_row = 2
        for label, col_name, is_total in bs_rows:
            if label == "":
                current_row += 1
                continue
            
            ws.cell(row=current_row, column=1, value=label)
            
            if col_name and col_name in bs_yearly.columns:
                col_idx = 2
                for month in bs_yearly.index:
                    value = bs_yearly.loc[month, col_name]
                    cell = ws.cell(row=current_row, column=col_idx, value=value)
                    cell.number_format = self.NUM_FORMAT
                    col_idx += 1
            
            # Formatting
            if is_total or label in ["ASSETS", "LIABILITIES", "EQUITY"]:
                for c in range(1, len(bs_yearly) + 2):
                    ws.cell(row=current_row, column=c).font = self.BOLD_TOTAL
                    if "Total" in label:
                        ws.cell(row=current_row, column=c).fill = self.SUBTOTAL_FILL
            
            current_row += 1
        
        # Column widths
        ws.column_dimensions['A'].width = 30
        for col_idx in range(2, len(bs_yearly) + 2):
            ws.column_dimensions[get_column_letter(col_idx)].width = 12
    
    def _create_cf_sheet(self):
        """Create Cash Flow tab."""
        ws = self.wb.create_sheet("Cash Flow")
        
        # Aggregate to yearly
        cf_yearly = self.cf_df.groupby("Year").sum()
        
        # Fix beginning/ending cash (take first/last of year)
        for year in cf_yearly.index:
            year_data = self.cf_df[self.cf_df["Year"] == year]
            cf_yearly.loc[year, "Beginning Cash Balance"] = year_data["Beginning Cash Balance"].iloc[0]
            cf_yearly.loc[year, "Ending Cash Balance"] = year_data["Ending Cash Balance"].iloc[-1]
        
        # Define rows with sign convention
        cf_rows = [
            ("OPERATING ACTIVITIES", None, True, 1),
            ("Net Income", "Net Income", False, 1),
            ("Depreciation/Amortization", "Depreciation/Amortization", False, 1),
            ("Cash Flow from Operations", "Cash Flow from Operations (CFO)", True, 1),
            ("", None, False, 1),
            ("INVESTING ACTIVITIES", None, True, 1),
            ("Acquisition Costs", "Acquisition Costs Outflow", False, 1),
            ("Cash Flow from Investing", "Cash Flow from Investing (CFI)", True, 1),
            ("", None, False, 1),
            ("FINANCING ACTIVITIES", None, True, 1),
            ("Loan Proceeds", "Loan Proceeds", False, 1),
            ("Equity Injected", "Equity Injected", False, 1),
            ("Loan Principal Repayment", "Loan Principal Repayment", False, 1),
            ("Cash Flow from Financing", "Cash Flow from Financing (CFF)", True, 1),
            ("", None, False, 1),
            ("Net Change in Cash", "Net Change in Cash", True, 1),
            ("Beginning Cash", "Beginning Cash Balance", False, 1),
            ("Ending Cash", "Ending Cash Balance", True, 1),
        ]
        
        years = list(cf_yearly.index)
        
        # Header
        ws.cell(row=1, column=1, value="Cash Flow Statement (€)")
        ws.cell(row=1, column=1).font = self.HEADER_FONT
        ws.cell(row=1, column=1).fill = self.HEADER_FILL
        
        for col_idx, year in enumerate(years, start=2):
            cell = ws.cell(row=1, column=col_idx, value=f"Year {year}")
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = Alignment(horizontal='center')
        
        # Data rows
        current_row = 2
        for label, col_name, is_total, sign in cf_rows:
            if label == "":
                current_row += 1
                continue
            
            ws.cell(row=current_row, column=1, value=label)
            
            if col_name and col_name in cf_yearly.columns:
                for col_idx, year in enumerate(years, start=2):
                    value = cf_yearly.loc[year, col_name] * sign
                    cell = ws.cell(row=current_row, column=col_idx, value=value)
                    cell.number_format = self.NUM_FORMAT
            
            # Formatting
            if is_total or "ACTIVITIES" in label:
                for c in range(1, len(years) + 2):
                    ws.cell(row=current_row, column=c).font = self.BOLD_TOTAL
                    if is_total and "ACTIVITIES" not in label:
                        ws.cell(row=current_row, column=c).fill = self.SUBTOTAL_FILL
            
            current_row += 1
        
        # Column widths
        ws.column_dimensions['A'].width = 30
        for col_idx in range(2, len(years) + 2):
            ws.column_dimensions[get_column_letter(col_idx)].width = 12
    
    def _create_loan_sheet(self):
        """Create Loan Amortization tab."""
        ws = self.wb.create_sheet("Loan Schedule")
        
        if self.loan_schedule is None or len(self.loan_schedule) == 0:
            ws.cell(row=1, column=1, value="No loan in this scenario (100% equity)")
            return
        
        # Aggregate to yearly
        loan_copy = self.loan_schedule.copy()
        loan_copy['Year'] = ((loan_copy.index - 1) // 12) + 1
        
        yearly = loan_copy.groupby('Year').agg({
            'Beginning Balance': 'first',
            'Monthly Payment': 'sum',
            'Interest Payment': 'sum',
            'Principal Payment': 'sum',
            'Ending Balance': 'last'
        })
        
        # Headers
        headers = ["Year", "Beginning Balance", "Total Payments", "Interest", "Principal", "Ending Balance"]
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = Alignment(horizontal='center')
        
        # Data
        for row_idx, (year, data) in enumerate(yearly.iterrows(), start=2):
            ws.cell(row=row_idx, column=1, value=year)
            ws.cell(row=row_idx, column=2, value=data['Beginning Balance']).number_format = self.NUM_FORMAT
            ws.cell(row=row_idx, column=3, value=data['Monthly Payment']).number_format = self.NUM_FORMAT
            ws.cell(row=row_idx, column=4, value=data['Interest Payment']).number_format = self.NUM_FORMAT
            ws.cell(row=row_idx, column=5, value=data['Principal Payment']).number_format = self.NUM_FORMAT
            ws.cell(row=row_idx, column=6, value=data['Ending Balance']).number_format = self.NUM_FORMAT
        
        # Totals row
        total_row = len(yearly) + 2
        ws.cell(row=total_row, column=1, value="TOTAL").font = self.BOLD_TOTAL
        ws.cell(row=total_row, column=3, value=f"=SUM(C2:C{total_row-1})").number_format = self.NUM_FORMAT
        ws.cell(row=total_row, column=4, value=f"=SUM(D2:D{total_row-1})").number_format = self.NUM_FORMAT
        ws.cell(row=total_row, column=5, value=f"=SUM(E2:E{total_row-1})").number_format = self.NUM_FORMAT
        
        for col_idx in range(1, 7):
            ws.cell(row=total_row, column=col_idx).fill = self.TOTAL_FILL
            ws.cell(row=total_row, column=col_idx).font = self.BOLD_TOTAL
        
        # Column widths
        for col_idx in range(1, 7):
            ws.column_dimensions[get_column_letter(col_idx)].width = 18
    
    def _create_metrics_sheet(self):
        """Create Investment Metrics tab."""
        ws = self.wb.create_sheet("Investment Metrics")
        
        metrics_data = [
            ("INVESTMENT PERFORMANCE", None, None),
            ("IRR (Annual)", self.metrics.get('irr', 0), self.PCT_FORMAT),
            ("NPV", self.metrics.get('npv', 0), self.NUM_FORMAT),
            ("Cash-on-Cash (Year 1)", self.metrics.get('cash_on_cash', 0), self.PCT_FORMAT),
            ("Equity Multiple", self.metrics.get('equity_multiple', 0), '0.00x'),
            ("", None, None),
            ("EXIT SCENARIO", None, None),
            ("Exit Property Value", self.metrics.get('exit_property_value', 0), self.NUM_FORMAT),
            ("Selling Costs", self.metrics.get('selling_costs', 0), self.NUM_FORMAT),
            ("Remaining Loan Balance", self.metrics.get('remaining_loan_balance', 0), self.NUM_FORMAT),
            ("Capital Gain", self.metrics.get('capital_gain', 0), self.NUM_FORMAT),
            ("Capital Gains Tax", self.metrics.get('capital_gains_tax', 0), self.NUM_FORMAT),
            ("Net Exit Proceeds", self.metrics.get('net_exit_proceeds', 0), self.NUM_FORMAT),
        ]
        
        row = 1
        for label, value, fmt in metrics_data:
            if value is None and label:
                # Section header
                ws.cell(row=row, column=1, value=label)
                ws.cell(row=row, column=1).font = self.HEADER_FONT
                ws.cell(row=row, column=1).fill = self.HEADER_FILL
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
            elif label == "":
                pass
            else:
                ws.cell(row=row, column=1, value=label)
                cell = ws.cell(row=row, column=2, value=value)
                if fmt:
                    cell.number_format = fmt
                
                if label in ["Net Exit Proceeds", "Equity Multiple"]:
                    ws.cell(row=row, column=1).font = self.BOLD_TOTAL
                    cell.font = self.BOLD_TOTAL
                    cell.fill = self.TOTAL_FILL
            
            row += 1
        
        # Column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 18

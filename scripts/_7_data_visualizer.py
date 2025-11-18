# In file: scripts/_7_data_visualizer.py

import pandas as pd
import plotly.graph_objects as go
from typing import Optional
from ._1_model_params import ModelParameters
from ._8_loan_calculator import LoanCalculator

class DataVisualizer:
    """
    Handles all data visualizations for the financial model.
    Enhanced with dashboard charts and sensitivity analysis.
    """

    def __init__(self):
        pass

    # ===== DASHBOARD METHODS =====
    
    def create_consolidated_cf_table(self, pnl_df: Optional[pd.DataFrame], 
                                     cf_df: Optional[pd.DataFrame],
                                     params: ModelParameters) -> Optional[pd.DataFrame]:
        """
        Creates consolidated cash flow table from P&L to Net Income,
        then adds back D&A for CFO, plus CFI and CFF.
        Shows the bridge from accounting income to cash flow.
        """
        if pnl_df is None or cf_df is None:
            return None
        
        try:
            # Sum over entire holding period
            pnl_total = pnl_df.sum()
            cf_total = cf_df.sum()
            
            # Build the consolidated waterfall-style table
            data = {
                'Total Period (€)': [
                    pnl_total.get("Gross Operating Income", 0),
                    -pnl_total.get("Total Operating Expenses", 0),
                    pnl_total.get("Net Operating Income", 0),
                    -pnl_total.get("Loan Interest", 0),
                    -pnl_total.get("Depreciation/Amortization", 0),
                    pnl_total.get("Taxable Income", 0),
                    -pnl_total.get("Total Taxes", 0),
                    pnl_total.get("Net Income", 0),
                    pnl_total.get("Depreciation/Amortization", 0),  # Add back non-cash
                    cf_total.get("Cash Flow from Operations (CFO)", 0),
                    cf_total.get("Cash Flow from Investing (CFI)", 0),
                    cf_total.get("Cash Flow from Financing (CFF)", 0),
                    cf_total.get("Net Change in Cash", 0)
                ]
            }
            
            index = [
                "Gross Operating Income",
                "  Total Operating Expenses",
                "Net Operating Income",
                "  Loan Interest",
                "  Depreciation/Amortization",
                "Taxable Income",
                "  Total Taxes",
                "Net Income",
                "Add back: Depreciation/Amortization",
                "Cash Flow from Operations (CFO)",
                "Cash Flow from Investing (CFI)",
                "Cash Flow from Financing (CFF)",
                "Net Change in Cash"
            ]
            
            df = pd.DataFrame(data, index=index)
            df.index.name = ""
            
            return df
            
        except Exception as e:
            print(f"Error creating consolidated CF table: {e}")
            return None

    def create_pnl_sankey_total(self, pnl_df: Optional[pd.DataFrame]) -> Optional[go.Figure]:
        """
        Creates P&L Sankey diagram for the entire investment period (not just Year 1).
        Shows flow from GOI through expenses to Net Income.
        """
        if pnl_df is None:
            return None

        try:
            # Sum all years
            pnl_sum = pnl_df.sum()
            
            goi = pnl_sum.get("Gross Operating Income", 0)
            opex = pnl_sum.get("Total Operating Expenses", 0)
            noi = pnl_sum.get("Net Operating Income", 0)
            interest = pnl_sum.get("Loan Interest", 0)
            depreciation = pnl_sum.get("Depreciation/Amortization", 0)
            taxes = pnl_sum.get("Total Taxes", 0)
            net_income = pnl_sum.get("Net Income", 0)
            
            ebt_calc = noi - interest - depreciation
            
            # Node labels
            labels = [
                f"Gross Operating Income<br>€{goi:,.0f}",  # 0
                f"Operating Expenses<br>€{opex:,.0f}",      # 1
                f"Net Operating Income<br>€{noi:,.0f}",     # 2
                f"Loan Interest<br>€{interest:,.0f}",       # 3
                f"Depreciation<br>€{depreciation:,.0f}",    # 4
                "Earnings Before Tax",                       # 5
                f"Taxes<br>€{taxes:,.0f}",                  # 6
                "Net Income"                                 # 7
            ]
            
            # Define flows
            source = [0, 0, 2, 2, 2]  # GOI splits, NOI splits
            target = [1, 2, 3, 4, 5]
            value = [abs(opex), abs(noi), abs(interest), abs(depreciation), abs(ebt_calc)]
            
            # Handle profit vs loss
            if ebt_calc >= 0:
                labels[5] = f"EBT (Profit)<br>€{ebt_calc:,.0f}"
                labels[7] = f"Net Income<br>€{net_income:,.0f}"
                source.extend([5, 5])
                target.extend([6, 7])
                value.extend([abs(taxes), abs(net_income)])
            else:
                labels[5] = f"EBT (Loss)<br>€{ebt_calc:,.0f}"
                labels[7] = f"Net Income (Loss)<br>€{net_income:,.0f}"
                source.extend([5, 5])
                target.extend([6, 7])
                value.extend([abs(taxes), abs(net_income)])
            
            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=labels,
                    color="#4a90e2"
                ),
                link=dict(source=source, target=target, value=value)
            )])
            
            fig.update_layout(
                title_text=None,
                font_size=11,
                template="plotly_dark",
                margin=dict(l=10, r=10, t=10, b=10),
                height=350
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating P&L Sankey (total): {e}")
            return None

    def create_cf_sankey_total(self, cf_df: Optional[pd.DataFrame]) -> Optional[go.Figure]:
        """
        Creates Cash Flow Sankey for the entire investment period.
        Shows sources and uses of cash across CFO/CFI/CFF.
        """
        if cf_df is None:
            return None
        
        try:
            cf_sum = cf_df.sum()
            
            # Main categories
            cfo = cf_sum.get("Cash Flow from Operations (CFO)", 0)
            cfi = cf_sum.get("Cash Flow from Investing (CFI)", 0)
            cff = cf_sum.get("Cash Flow from Financing (CFF)", 0)
            net_change = cf_sum.get("Net Change in Cash", 0)
            
            # Detailed breakdowns
            acq_outflow = cf_sum.get("Acquisition Costs Outflow", 0)  # Already negative
            loan_proceeds = cf_sum.get("Loan Proceeds", 0)
            equity_injected = cf_sum.get("Equity Injected", 0)
            principal_repay = cf_sum.get("Loan Principal Repayment", 0)  # Already negative
            
            # Node labels (adjust indices carefully)
            labels = [
                f"CFO<br>€{cfo:,.0f}",                              # 0
                f"CFI<br>€{cfi:,.0f}",                              # 1
                f"CFF<br>€{cff:,.0f}",                              # 2
                f"Net Cash Change<br>€{net_change:,.0f}",          # 3
                f"Acquisition<br>€{abs(acq_outflow):,.0f}",        # 4
                f"Loan<br>€{loan_proceeds:,.0f}",                  # 5
                f"Equity<br>€{equity_injected:,.0f}",              # 6
                f"Principal<br>€{abs(principal_repay):,.0f}"       # 7
            ]
            
            # Define flows
            source = []
            target = []
            value = []
            
            # CFO contribution to net change
            if cfo != 0:
                source.append(0)
                target.append(3)
                value.append(abs(cfo))
            
            # CFI breakdown and contribution
            if acq_outflow != 0:
                source.append(1)
                target.append(4)
                value.append(abs(acq_outflow))
            
            if cfi != 0:
                source.append(1)
                target.append(3)
                value.append(abs(cfi))
            
            # CFF breakdown
            if loan_proceeds != 0:
                source.append(5)
                target.append(2)
                value.append(abs(loan_proceeds))
            
            if equity_injected != 0:
                source.append(6)
                target.append(2)
                value.append(abs(equity_injected))
            
            if principal_repay != 0:
                source.append(2)
                target.append(7)
                value.append(abs(principal_repay))
            
            # CFF contribution to net change
            if cff != 0:
                source.append(2)
                target.append(3)
                value.append(abs(cff))
            
            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=labels,
                    color="#2ecc71"
                ),
                link=dict(source=source, target=target, value=value)
            )])
            
            fig.update_layout(
                title_text=None,
                font_size=11,
                template="plotly_dark",
                margin=dict(l=10, r=10, t=10, b=10),
                height=350
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating CF Sankey (total): {e}")
            return None

    def create_loan_sensitivity_heatmap(self, params: ModelParameters) -> Optional[go.Figure]:
        """
        Creates loan payment sensitivity analysis as a heatmap.
        Shows how monthly payment varies with interest rate and duration.
        """
        try:
            loan_calc = LoanCalculator(params)
            
            # Generate sensitivity matrix
            sensitivity_df = loan_calc.generate_sensitivity_analysis(
                rate_delta=0.005,      # 0.5% steps
                rate_range=0.01,       # ±1% range
                duration_delta_months=24,  # 2-year steps
                duration_range_months=48   # ±4 years range
            )
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=sensitivity_df.values,
                x=sensitivity_df.columns,
                y=sensitivity_df.index,
                colorscale='RdYlGn_r',  # Red = high, Green = low
                text=sensitivity_df.values,
                texttemplate='€%{text:,.0f}',
                textfont={"size": 9},
                colorbar=dict(title="Monthly<br>Payment (€)")
            ))
            
            fig.update_layout(
                title="Loan Payment Sensitivity Analysis",
                xaxis_title="Interest Rate",
                yaxis_title="Loan Duration (Months)",
                template="plotly_dark",
                height=400,
                margin=dict(l=60, r=80, t=60, b=60)
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating loan sensitivity heatmap: {e}")
            return None

    # ===== EXISTING METHODS (Year 1 P&L, Cumulative Chart) =====
    
    def create_pnl_sankey(self, pnl_df: Optional[pd.DataFrame]) -> Optional[go.Figure]:
        """
        Generates Year 1 P&L Sankey diagram (kept for P&L detail page).
        """
        if pnl_df is None:
            return None

        try:
            pnl_y1 = pnl_df[pnl_df["Year"] == 1]
            pnl_y1_sum = pnl_y1.sum()

            goi = pnl_y1_sum.get("Gross Operating Income", 0)
            opex = pnl_y1_sum.get("Total Operating Expenses", 0)
            noi = pnl_y1_sum.get("Net Operating Income", 0)
            interest = pnl_y1_sum.get("Loan Interest", 0)
            depreciation = pnl_y1_sum.get("Depreciation/Amortization", 0)
            taxes = pnl_y1_sum.get("Total Taxes", 0)
            net_income = pnl_y1_sum.get("Net Income", 0)

            ebt_calc = noi - interest - depreciation

            labels = [
                f"Gross Operating Income<br>€{goi:,.0f}",
                f"Total OpEx<br>€{opex:,.0f}",
                f"Net Operating Income<br>€{noi:,.0f}",
                f"Loan Interest<br>€{interest:,.0f}",
                f"Depreciation<br>€{depreciation:,.0f}",
                "Earnings Before Tax",
                f"Total Taxes<br>€{taxes:,.0f}",
                "Net Income"
            ]

            source = [0, 0, 2, 2, 2]
            target = [1, 2, 3, 4, 5]
            value = [abs(opex), abs(noi), abs(interest), abs(depreciation), abs(ebt_calc)]

            if ebt_calc >= 0:
                labels[5] = f"EBT (Profit)<br>€{ebt_calc:,.0f}"
                labels[7] = f"Net Income<br>€{net_income:,.0f}"
                source.extend([5, 5])
                target.extend([6, 7])
                value.extend([abs(taxes), abs(net_income)])
            else:
                labels[5] = f"EBT (Loss)<br>€{ebt_calc:,.0f}"
                labels[7] = f"Net Income (Loss)<br>€{net_income:,.0f}"
                source.extend([5, 5])
                target.extend([6, 7])
                value.extend([abs(taxes), abs(net_income)])

            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=labels,
                    color="#4a90e2"
                ),
                link=dict(source=source, target=target, value=value)
            )])

            fig.update_layout(
                title_text=None,
                font_size=12,
                template="plotly_dark",
                margin=dict(l=20, r=20, t=20, b=20)
            )
            
            return fig

        except Exception as e:
            print(f"Error generating Year 1 Sankey: {e}")
            return None

    def create_pnl_cumulative_chart(self, pnl_df: Optional[pd.DataFrame]) -> Optional[go.Figure]:
        """
        Generates cumulative line chart for key P&L metrics over holding period.
        """
        if pnl_df is None:
            return None

        try:
            pnl_yearly = pnl_df.groupby("Year").sum()
            
            metrics_to_plot = [
                "Gross Operating Income", 
                "Net Operating Income", 
                "Net Income"
            ]
            
            pnl_cumulative = pnl_yearly[metrics_to_plot].cumsum()
            pnl_cumulative.index.name = "Year"
            
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=pnl_cumulative.index, 
                y=pnl_cumulative["Gross Operating Income"],
                mode='lines+markers',
                name='Cumulative GOI',
                line=dict(color='cyan', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=pnl_cumulative.index, 
                y=pnl_cumulative["Net Operating Income"],
                mode='lines+markers',
                name='Cumulative NOI',
                line=dict(color='lightgreen', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=pnl_cumulative.index, 
                y=pnl_cumulative["Net Income"],
                mode='lines+markers',
                name='Cumulative Net Income',
                line=dict(color='white', width=3, dash='dot')
            ))
            
            fig.update_layout(
                title_text=None,
                template="plotly_dark",
                font_size=12,
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    yanchor="bottom", y=1.02,
                    xanchor="right", x=1
                ),
                margin=dict(l=20, r=20, t=20, b=20)
            )
            
            return fig

        except Exception as e:
            print(f"Error generating cumulative P&L chart: {e}")
            return None

    def format_loan_schedule_table(self, loan_schedule: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
        """
        Formats loan amortization schedule for display.
        Converts to yearly summary with beginning/ending balances.
        """
        if loan_schedule is None or len(loan_schedule) == 0:
            return None
        
        try:
            # Add year column
            loan_schedule_copy = loan_schedule.copy()
            loan_schedule_copy['Year'] = ((loan_schedule_copy.index - 1) // 12) + 1
            
            # Group by year and aggregate
            yearly_summary = loan_schedule_copy.groupby('Year').agg({
                'Beginning Balance': 'first',
                'Monthly Payment': 'sum',
                'Interest Payment': 'sum',
                'Principal Payment': 'sum',
                'Ending Balance': 'last'
            })
            
            # Rename for clarity
            yearly_summary.columns = [
                'Beginning Balance',
                'Total Payments',
                'Total Interest',
                'Total Principal',
                'Ending Balance'
            ]
            
            # Convert to k€
            yearly_summary_k = yearly_summary / 1000.0
            yearly_summary_k.index.name = 'Year'
            
            return yearly_summary_k
            
        except Exception as e:
            print(f"Error formatting loan schedule: {e}")
            return None

    def create_loan_balance_chart(self, loan_schedule: Optional[pd.DataFrame]) -> Optional[go.Figure]:
        """
        Creates chart showing loan balance decline over time with principal/interest stacked area.
        """
        if loan_schedule is None or len(loan_schedule) == 0:
            return None
        
        try:
            # Convert to yearly for cleaner visualization
            loan_schedule_copy = loan_schedule.copy()
            loan_schedule_copy['Year'] = ((loan_schedule_copy.index - 1) // 12) + 1
            
            yearly = loan_schedule_copy.groupby('Year').agg({
                'Beginning Balance': 'first',
                'Ending Balance': 'last',
                'Interest Payment': 'sum',
                'Principal Payment': 'sum'
            })
            
            fig = go.Figure()
            
            # Loan balance line
            fig.add_trace(go.Scatter(
                x=yearly.index,
                y=yearly['Ending Balance'],
                mode='lines+markers',
                name='Loan Balance',
                line=dict(color='#e74c3c', width=3),
                yaxis='y1'
            ))
            
            # Principal payment bars
            fig.add_trace(go.Bar(
                x=yearly.index,
                y=yearly['Principal Payment'],
                name='Principal Paid',
                marker_color='#2ecc71',
                yaxis='y2'
            ))
            
            # Interest payment bars
            fig.add_trace(go.Bar(
                x=yearly.index,
                y=yearly['Interest Payment'],
                name='Interest Paid',
                marker_color='#3498db',
                yaxis='y2'
            ))
            
            fig.update_layout(
                title='Loan Amortization Progress',
                template='plotly_dark',
                barmode='stack',
                hovermode='x unified',
                yaxis=dict(
                    title='Loan Balance (€)',
                    side='left'
                ),
                yaxis2=dict(
                    title='Annual Payments (€)',
                    side='right',
                    overlaying='y'
                ),
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1
                ),
                margin=dict(l=60, r=60, t=60, b=40),
                height=400
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating loan balance chart: {e}")
            return None

    # ===== INVESTMENT METRICS VISUALIZATION =====
    
    def create_irr_sensitivity_heatmap(self, params: ModelParameters) -> Optional[go.Figure]:
        """
        Creates IRR sensitivity heatmap (same format as loan sensitivity).
        Varies property growth rate and loan interest rate.
        
        Returns:
            Plotly heatmap figure
        """
        try:
            from ._9_investment_metrics import InvestmentMetrics
            from ._0_financial_model import FinancialModel
            
            # Base values
            base_property_growth = params.property_value_growth_rate
            base_loan_interest = params.loan_interest_rate
            
            # Define ranges
            property_growth_values = [
                base_property_growth - 0.01,
                base_property_growth - 0.005,
                base_property_growth,
                base_property_growth + 0.005,
                base_property_growth + 0.01
            ]
            
            loan_interest_values = [
                max(0.001, base_loan_interest - 0.01),
                max(0.001, base_loan_interest - 0.005),
                base_loan_interest,
                base_loan_interest + 0.005,
                base_loan_interest + 0.01
            ]
            
            # Build sensitivity matrix
            irr_matrix = []
            
            for prop_growth in property_growth_values:
                irr_row = []
                
                for loan_rate in loan_interest_values:
                    import copy
                    params_copy = copy.deepcopy(params)
                    
                    params_copy.property_value_growth_rate = prop_growth
                    params_copy.loan_interest_rate = loan_rate
                    
                    try:
                        model = FinancialModel(params_copy)
                        model.run_simulation(lease_type='furnished_1yr')
                        
                        metrics = model.get_investment_metrics()
                        irr = metrics.get('irr', 0.0) * 100
                        
                        irr_row.append(irr)
                    except Exception as e:
                        print(f"Error in sensitivity calculation: {e}")
                        irr_row.append(0.0)
                
                irr_matrix.append(irr_row)
            
            # Create DataFrame
            import pandas as pd
            df_sensitivity = pd.DataFrame(
                irr_matrix,
                index=[f"{v*100:.1f}%" for v in property_growth_values],
                columns=[f"{v*100:.1f}%" for v in loan_interest_values]
            )
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=df_sensitivity.values,
                x=df_sensitivity.columns,
                y=df_sensitivity.index,
                colorscale='RdYlGn',
                text=df_sensitivity.values,
                texttemplate='%{text:.2f}%',
                textfont={"size": 10},
                colorbar=dict(title="IRR (%)")
            ))
            
            fig.update_layout(
                title="IRR Sensitivity Analysis",
                xaxis_title="Loan Interest Rate",
                yaxis_title="Property Growth Rate",
                template="plotly_dark",
                height=400,
                margin=dict(l=80, r=80, t=60, b=60)
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating IRR sensitivity heatmap: {e}")
            return None

    def create_npv_football_field(self, model, params) -> Optional[go.Figure]:
        """
        Creates NPV football field chart showing scenario ranges.
        """
        try:
            from ._9_investment_metrics import InvestmentMetrics
            
            metrics_calc = InvestmentMetrics(params)
            cf_df = model.get_cash_flow()
            bs_df = model.get_balance_sheet()
            
            # Generate scenarios
            scenarios_df = metrics_calc.generate_npv_scenarios(cf_df, bs_df)
            
            if scenarios_df.empty:
                return None
            
            # Create football field chart
            fig = go.Figure()
            
            # Add bars for each scenario
            colors = {'Pessimistic': '#e74c3c', 'Base': '#3498db', 'Optimistic': '#2ecc71'}
            
            for idx, row in scenarios_df.iterrows():
                scenario = row['Scenario']
                npv = row['NPV']
                
                fig.add_trace(go.Bar(
                    x=[scenario],
                    y=[npv],
                    name=scenario,
                    marker_color=colors.get(scenario, '#95a5a6'),
                    text=[f"€{npv/1000:.1f}k"],
                    textposition='outside',
                    hovertemplate=(
                        f"<b>{scenario}</b><br>" +
                        f"NPV: €{npv:,.0f}<br>" +
                        f"Exit: {row['Exit Price Adj']}<br>" +
                        f"Rent: {row['Rent Adj']}<br>" +
                        f"Discount: {row['Discount Rate']}<br>" +
                        "<extra></extra>"
                    )
                ))
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
            
            fig.update_layout(
                title="NPV Scenario Analysis",
                xaxis_title="",
                yaxis_title="NPV (€)",
                template="plotly_dark",
                showlegend=False,
                height=400,
                margin=dict(l=60, r=60, t=60, b=40)
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating NPV football field: {e}")
            return None
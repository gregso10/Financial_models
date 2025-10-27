import pandas as pd
import plotly.graph_objects as go
from typing import Optional

class DataVisualizer:
    """
    Handles the creation of all complex data visualizations (Plotly charts, etc.)
    for the financial model.
    """

    def __init__(self):
        pass

    def create_pnl_sankey(self, pnl_df: Optional[pd.DataFrame]) -> Optional[go.Figure]:
        """
        Generates the Year 1 P&L Sankey diagram.
        #TODO: Improve Sankey dynamics and visualisation, especially in case of negative net income.
        #TODO: create a Sankey class dynamic for the CFs viz as well. 
        """
        if pnl_df is None:
            return None

        try:
            # 1. Get Year 1 data and sum it
            pnl_y1 = pnl_df[pnl_df["Year"] == 1]
            pnl_y1_sum = pnl_y1.sum()

            # 2. Extract P&L values
            goi = pnl_y1_sum.get("Gross Operating Income", 0)
            opex = pnl_y1_sum.get("Total Operating Expenses", 0)
            noi = pnl_y1_sum.get("Net Operating Income", 0)
            interest = pnl_y1_sum.get("Loan Interest", 0)
            depreciation = pnl_y1_sum.get("Depreciation/Amortization", 0)
            taxes = pnl_y1_sum.get("Total Taxes", 0)
            net_income = pnl_y1_sum.get("Net Income", 0)

            # 3. Calculate intermediate EBT
            ebt_calc = noi - interest - depreciation

            # 4. Define nodes (labels)
            labels = [
                f"Gross Operating Income<br>€{goi:,.0f}",  # 0
                f"Total OpEx<br>€{opex:,.0f}",             # 1
                f"Net Operating Income<br>€{noi:,.0f}",    # 2
                f"Loan Interest<br>€{interest:,.0f}",      # 3
                f"Depreciation<br>€{depreciation:,.0f}",   # 4
                "Earnings Before Tax",                      # 5
                f"Total Taxes<br>€{taxes:,.0f}",           # 6
                "Net Income"                                # 7
            ]

            # 5. Define links (source, target, value)
            source = [0, 0, 2, 2, 2] # GOI -> OpEx, GOI -> NOI, NOI -> Int, NOI -> Dep, NOI -> EBT
            target = [1, 2, 3, 4, 5]
            
            # --- FIX: Use abs() for all values ---
            value = [
                abs(opex), 
                abs(noi), 
                abs(interest), 
                abs(depreciation), 
                abs(ebt_calc)
            ]

            # 6. Handle EBT split (profit vs. loss)
            if ebt_calc >= 0:
                labels[5] = f"EBT (Profit)<br>€{ebt_calc:,.0f}"
                labels[7] = f"Net Income (Profit)<br>€{net_income:,.0f}"
                source.extend([5, 5]) # EBT -> Taxes, EBT -> Net Income
                target.extend([6, 7])
                value.extend([abs(taxes), abs(net_income)])
            else:
                labels[5] = f"EBT (Loss)<br>€{ebt_calc:,.0f}"
                labels[7] = f"Net Income (Loss)<br>€{net_income:,.0f}"
                source.extend([5, 5]) # EBT -> Taxes (0), EBT -> Net Income
                target.extend([6, 7])
                value.extend([abs(taxes), abs(net_income)]) # taxes will be 0, net_income negative

            # 7. Create the figure
            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=labels,
                    color="#4a90e2" # A better blue
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=value
                ))])

            fig.update_layout(
                title_text=None,
                font_size=12, 
                template="plotly_dark",
                margin=dict(l=20, r=20, t=20, b=20) # Tighten margins
            )
            
            return fig

        except Exception as e:
            print(f"Error generating Sankey chart: {e}")
            return None

    def create_pnl_cumulative_chart(self, pnl_df: Optional[pd.DataFrame]) -> Optional[go.Figure]:
        """
        Generates a cumulative line chart for key P&L metrics over the holding period.
        """
        if pnl_df is None:
            return None

        try:
            # 1. Group by Year and sum to get annual figures
            pnl_yearly = pnl_df.groupby("Year").sum()
            
            # 2. Select key metrics
            metrics_to_plot = [
                "Gross Operating Income", 
                "Net Operating Income", 
                "Net Income"
            ]
            
            # 3. Calculate the cumulative sum (running total)
            pnl_cumulative = pnl_yearly[metrics_to_plot].cumsum()
            pnl_cumulative.index.name = "Year" # Ensure index is named for hover
            
            # 4. Create the figure
            fig = go.Figure()

            # 5. Add traces
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
            
            # 6. Update layout
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

import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Real Estate ROI Calculator", layout="wide")

st.title("🏠 Real Estate ROI Calculator")

# 1) INPUTS
st.sidebar.header("Input Parameters")

# 1.a) Full purchase price
purchase_price = st.sidebar.slider(
    label="Purchase Price (USD)",
    min_value=0,
    max_value=1_000_000,
    value=200_000,
    step=1_000,
    help="Select the full amount you paid for the property (including any one-time acquisition costs)."
)

# 1.b) Annual rent as a percentage of purchase price
rent_pct = st.sidebar.slider(
    label="Annual Rent Yield (%)",
    min_value=0.0,
    max_value=100.0,
    value=6.0,
    step=0.1,
    help="Enter the annual rent as a percentage of the purchase price. E.g. 6% means Annual Rent = 0.06 × Purchase Price."
)

st.sidebar.markdown("---")
st.sidebar.markdown("No taxes or financing assumed.\nROI is shown on a quarterly basis.")

# 2) CALCULATIONS
rent_decimal = rent_pct / 100.0
annual_rent = purchase_price * rent_decimal
quarterly_rent = annual_rent / 4.0

# ROI metrics
annual_roi_pct = rent_pct  # since annual_rent / purchase_price × 100 = rent_pct
quarterly_roi_pct = annual_roi_pct / 4.0

# Build a DataFrame for quarterly rents
quarters = ["Q1", "Q2", "Q3", "Q4"]
quarterly_values = [quarterly_rent] * 4
df_quarters = pd.DataFrame({
    "Quarter": quarters,
    "Rent (USD)": quarterly_values
})

# Build a DataFrame for the pie chart (Capital vs Annual Rent)
pie_df = pd.DataFrame({
    "Category": ["Capital (Purchase Price)", "Annual Rent (Return)"],
    "Value": [purchase_price, annual_rent]
})

# 3) DISPLAY SUMMARY METRICS
st.subheader("Summary Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Purchase Price (USD)", f"${purchase_price:,.0f}")
col2.metric("Annual Rent (USD)", f"${annual_rent:,.0f}", help="Total rent collected over 12 months.")
col3.metric("Annual ROI (%)", f"{annual_roi_pct:.2f}%")

col4, col5, col6 = st.columns(3)
col4.metric("Quarterly Rent (USD)", f"${quarterly_rent:,.0f}")
col5.metric("Quarterly ROI (%)", f"{quarterly_roi_pct:.2f}%")
col6.metric("Total ROI (First Year)", f"{annual_roi_pct:.2f}%")

st.markdown("---")

# 4) QUARTERLY RENT TABLE
st.subheader("Quarterly Rent Breakdown")
st.table(df_quarters.style.format({"Rent (USD)": "${:,.0f}"}))

# 5) CHARTS
st.subheader("Charts")

# 5.a) Bar chart of quarterly rent (using Altair)
bar_chart = (
    alt.Chart(df_quarters)
    .mark_bar()
    .encode(
        x=alt.X("Quarter:N", title="Quarter"),
        y=alt.Y("Rent (USD):Q", title="Rent (USD)"),
        tooltip=[alt.Tooltip("Rent (USD):Q", format="$,.0f")]
    )
    .properties(
        width=500,
        height=300,
        title="Quarterly Rent Distribution"
    )
)
st.altair_chart(bar_chart, use_container_width=True)

# 5.b) Pie chart: Purchase Price vs Annual Rent (using Altair)
pie_chart = (
    alt.Chart(pie_df)
    .mark_arc(innerRadius=50)
    .encode(
        theta=alt.Theta("Value:Q", title=""),
        color=alt.Color("Category:N", title=""),
        tooltip=[alt.Tooltip("Category:N"), alt.Tooltip("Value:Q", format="$,.0f")]
    )
    .properties(
        width=400,
        height=400,
        title="Capital vs Annual Rent (Return)"
    )
)
st.altair_chart(pie_chart, use_container_width=False)

# 6) FOOTER NOTE
st.markdown(
    """
    *All calculations assume no financing (cash purchase) and no taxes or additional operating expenses.*
    """
)

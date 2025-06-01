import streamlit as st
import pandas as pd
import altair as alt
from fpdf import FPDF
import io

st.set_page_config(page_title="Real Estate ROI Calculator", layout="wide")
st.title("🏠 Real Estate ROI Calculator")

# 1) INPUTS
st.sidebar.header("Input Parameters")

purchase_price = st.sidebar.slider(
    label="Purchase Price (USD)",
    min_value=0,
    max_value=1_000_000,
    value=200_000,
    step=1_000,
    help="Select the full amount you paid for the property (including any one-time acquisition costs)."
)

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

annual_roi_pct = rent_pct
quarterly_roi_pct = annual_roi_pct / 4.0

quarters = ["Q1", "Q2", "Q3", "Q4"]
quarterly_values = [quarterly_rent] * 4
df_quarters = pd.DataFrame({
    "Quarter": quarters,
    "Rent (USD)": quarterly_values
})

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

st.markdown(
    """
    *All calculations assume no financing (cash purchase) and no taxes or additional operating expenses.*
    """
)

st.markdown("---")

# 6) PDF REPORT GENERATION
st.subheader("📄 Generate PDF Report")

def create_pdf(purchase_price, rent_pct, annual_rent, annual_roi_pct,
               quarterly_rent, quarterly_roi_pct, df_quarters):
    """
    Build a PDF in memory containing all inputs and computed outputs.
    Returns: PDF data as bytes.
    """
    pdf = FPDF(format="letter", unit="pt")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 20, "Real Estate ROI Report", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 12)
    # Input parameters section
    pdf.cell(0, 16, "1. Input Parameters:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 14, f"   - Purchase Price:   ${purchase_price:,.0f}", ln=True)
    pdf.cell(0, 14, f"   - Annual Rent Yield (%):   {rent_pct:.2f}%", ln=True)
    pdf.ln(6)

    # Computed outputs section
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 16, "2. Computed Outputs:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 14, f"   - Annual Rent (USD):   ${annual_rent:,.0f}", ln=True)
    pdf.cell(0, 14, f"   - Annual ROI (%):   {annual_roi_pct:.2f}%", ln=True)
    pdf.cell(0, 14, f"   - Quarterly Rent (USD):   ${quarterly_rent:,.0f}", ln=True)
    pdf.cell(0, 14, f"   - Quarterly ROI (%):   {quarterly_roi_pct:.2f}%", ln=True)
    pdf.ln(10)

    # Quarterly table
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 16, "3. Quarterly Rent Breakdown:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    # Table header
    col_width = 150
    row_height = 18
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(col_width, row_height, "Quarter", border=1, fill=True, align="C")
    pdf.cell(col_width, row_height, "Rent (USD)", border=1, fill=True, align="C")
    pdf.ln(row_height)

    # Table rows
    for idx, row in df_quarters.iterrows():
        q = row["Quarter"]
        r = f"${row['Rent (USD)']:,.0f}"
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_width, row_height, q, border=1, fill=True, align="C")
        pdf.cell(col_width, row_height, r, border=1, fill=True, align="C")
        pdf.ln(row_height)

    # Footer note
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    footer = (
        "Note: All calculations assume no financing (cash purchase) "
        "and no taxes or additional operating expenses."
    )
    pdf.multi_cell(0, 12, footer, align="L")

    # Return PDF as bytes
    return pdf.output(dest="S").encode("latin1")


# When user clicks the button, build PDF in memory and make it downloadable
if st.button("📥 Download PDF Report"):
    pdf_bytes = create_pdf(
        purchase_price=purchase_price,
        rent_pct=rent_pct,
        annual_rent=annual_rent,
        annual_roi_pct=annual_roi_pct,
        quarterly_rent=quarterly_rent,
        quarterly_roi_pct=quarterly_roi_pct,
        df_quarters=df_quarters
    )

    st.download_button(
        label="Click here to save your ROI_Report.pdf",
        data=pdf_bytes,
        file_name="ROI_Report.pdf",
        mime="application/pdf"
    )

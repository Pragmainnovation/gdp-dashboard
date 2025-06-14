import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Real Estate ROI Calculator", layout="wide")
st.title("🏠 Real Estate ROI Calculator")

# ──────────────────────────────────────────────────────────────────────────────
# 1) INPUTS
# ──────────────────────────────────────────────────────────────────────────────
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



# ──────────────────────────────────────────────────────────────────────────────
# 2) CALCULATIONS
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# 3) DISPLAY SUMMARY METRICS
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# 4) QUARTERLY RENT TABLE
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("Quarterly Rent Breakdown")
st.table(df_quarters.style.format({"Rent (USD)": "${:,.0f}"}))

# ──────────────────────────────────────────────────────────────────────────────
# 5) CHARTS (on-screen with Altair)
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("Charts")

# 5.a) Bar chart of quarterly rent (Altair)
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

# 5.b) Pie chart (Altair)
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

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# 6) PDF REPORT GENERATION (with full styling)
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("📄 Generate PDF Report")

def create_pdf_with_charts(
    purchase_price, rent_pct, annual_rent, annual_roi_pct,
    quarterly_rent, quarterly_roi_pct, df_quarters
):
    """
    Build a PDF in memory containing:
      1. Black background + white 2-pt border on each page
      2. Dummy logo + contact info at top of Page 1
      3. Inputs & computed outputs (white text)
      4. Quarterly-rent table (white text on black)
      5. Bar-chart PNG + Pie-chart PNG (white-on-black Matplotlib) embedded
      6. No footer line
    Returns: PDF data as bytes.
    """

    # Helper: draw black background + white border on current page
    def page_setup(pdf):
        # Fill entire page black
        pdf.set_fill_color(0, 0, 0)
        pdf.rect(0, 0, pdf.w, pdf.h, style="F")
        # Draw white border (2 pt thick) with margin=10
        margin = 30
        pdf.set_line_width(2)
        pdf.set_draw_color(255, 255, 255)
        pdf.rect(margin, margin, pdf.w - 2*margin, pdf.h - 2*margin)

    # --- STEP A: Generate Matplotlib figures as PNGs ---
    # A.1) Bar chart (white-on-black)
    fig_bar, ax_bar = plt.subplots(figsize=(6, 4), facecolor="black")
    ax_bar.bar(df_quarters["Quarter"], df_quarters["Rent (USD)"], color="white")
    ax_bar.set_facecolor("black")
    ax_bar.tick_params(colors="white", which="both")
    ax_bar.set_xlabel("Quarter", color="white")
    ax_bar.set_ylabel("Rent (USD)", color="white")
    ax_bar.set_title("Quarterly Rent Distribution", color="white")
    for spine in ax_bar.spines.values():
        spine.set_color("white")
    plt.tight_layout()

    tmp_bar = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig_bar.savefig(tmp_bar.name, dpi=150, facecolor="black")
    plt.close(fig_bar)

    # A.2) Pie chart (white-on-black)
    fig_pie, ax_pie = plt.subplots(figsize=(5, 5), facecolor="black")
    categories = ["Capital (Purchase Price)", "Annual Rent (Return)"]
    values = [purchase_price, annual_rent]
    wedges, texts, autotexts = ax_pie.pie(
        values,
        labels=categories,
        autopct=lambda pct: f"{pct:.1f}%" if pct > 0 else "",
        startangle=90,
        counterclock=False,
        textprops={"color": "white"},
        wedgeprops={"edgecolor": "white"}
    )
    ax_pie.set_title("Capital vs Annual Rent (Return)", color="white")
    ax_pie.axis("equal")
    plt.tight_layout()

    tmp_pie = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig_pie.savefig(tmp_pie.name, dpi=150, facecolor="black")
    plt.close(fig_pie)

    # --- STEP B: Build the PDF with FPDF ---
    pdf = FPDF(format="letter", unit="pt")

    # === PAGE 1 ===
    pdf.add_page()
    page_setup(pdf)

    # Logo placeholder: white box with "LOGO" in black
    logo_w, logo_h = 100, 50
    logo_x, logo_y = 20, 20
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(logo_x, logo_y, logo_w, logo_h, style="F")
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(0, 0, 0)
    pdf.text(logo_x + (logo_w/2) - 15, logo_y + (logo_h/2) + 5, "LOGO")

    # Contact info (white text)
    contact_x = logo_x + logo_w + 20
    contact_y = logo_y + 15
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(255, 255, 255)
    pdf.text(contact_x, contact_y, "Contact: 123-456-7890")
    pdf.text(contact_x, contact_y + 15, "Email: dummy@example.com")

    # Report title (white)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.text(logo_x, logo_y + logo_h + 40, "Real Estate ROI Report")

    # Move down before writing inputs/outputs
    pdf.ln(logo_h + 60)

    # 1) Input parameters (white text)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 16, "1. Input Parameters:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 14, f"   - Purchase Price:        ${purchase_price:,.0f}", ln=True)
    pdf.cell(0, 14, f"   - Annual Rent Yield (%):  {rent_pct:.2f}%", ln=True)
    pdf.ln(8)

    # 2) Computed outputs (white text)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 16, "2. Computed Outputs:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 14, f"   - Annual Rent (USD):      ${annual_rent:,.0f}", ln=True)
    pdf.cell(0, 14, f"   - Annual ROI (%):         {annual_roi_pct:.2f}%", ln=True)
    pdf.cell(0, 14, f"   - Quarterly Rent (USD):   ${quarterly_rent:,.0f}", ln=True)
    pdf.cell(0, 14, f"   - Quarterly ROI (%):      {quarterly_roi_pct:.2f}%", ln=True)
    pdf.ln(10)

    # 3) Quarterly table (white text on black rows)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 16, "3. Quarterly Rent Breakdown:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    col_width = 150
    row_height = 18

    # Table header: light gray fill, black text
    pdf.set_fill_color(200, 200, 200)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(col_width, row_height, "Quarter", border=1, fill=True, align="C")
    pdf.cell(col_width, row_height, "Rent (USD)", border=1, fill=True, align="C")
    pdf.ln(row_height)

    # Table rows: black fill, white text
    pdf.set_fill_color(0, 0, 0)
    pdf.set_text_color(255, 255, 255)
    for _, row in df_quarters.iterrows():
        q = row["Quarter"]
        r = f"${row['Rent (USD)']:,.0f}"
        pdf.cell(col_width, row_height, q, border=1, fill=True, align="C")
        pdf.cell(col_width, row_height, r, border=1, fill=True, align="C")
        pdf.ln(row_height)

    # === PAGE 2 ===
    pdf.add_page()
    page_setup(pdf)

    # 4) Charts on Page 2
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.text(20, 40, "4. Charts:")

    # 4.a) Bar chart image (placed at x=20, y=60, width=500)
    pdf.image(tmp_bar.name, x=20, y=60, w=500)

    # 4.b) Pie chart image (placed at x=150, y=380, width=300)
    pdf.image(tmp_pie.name, x=150, y=380, w=300)

    # Convert PDF to bytes
    pdf_bytes = pdf.output(dest="S").encode("latin1")

    # Clean up temporary PNGs
    tmp_bar.close()
    tmp_pie.close()
    try:
        os.remove(tmp_bar.name)
        os.remove(tmp_pie.name)
    except OSError:
        pass

    return pdf_bytes


# When the user clicks “Download PDF Report,” build PDF (with full styling) and offer it
if st.button("📥 Download PDF Report"):
    pdf_bytes = create_pdf_with_charts(
        purchase_price=purchase_price,
        rent_pct=rent_pct,
        annual_rent=annual_rent,
        annual_roi_pct=annual_roi_pct,
        quarterly_rent=quarterly_rent,
        quarterly_roi_pct=quarterly_roi_pct,
        df_quarters=df_quarters
    )

    st.download_button(
        label="Click here to save your ROI_Report_with_Charts.pdf",
        data=pdf_bytes,
        file_name="ROI_Report_with_Charts.pdf",
        mime="application/pdf"
    )

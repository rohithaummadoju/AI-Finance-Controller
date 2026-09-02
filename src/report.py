import pandas as pd

# Load reconciliation results
df = pd.read_csv("data/reconciliation_report.csv")

# Total records
total_records = len(df)

# Matched records
matched = (df["status"] == "MATCH").sum()

# Exceptions
exceptions = total_records - matched

# Match rate
match_rate = (matched / total_records) * 100

# Exception rate
exception_rate = (exceptions / total_records) * 100

print("\n==============================")
print("      FINANCE CONTROLLER")
print("==============================")

st.markdown(
    '<div class="section-title">📊 Financial Control Overview</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Records</div>
            <div class="kpi-value">{total_records:,}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Matched Records</div>
            <div class="kpi-value">{matched:,}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Exceptions</div>
            <div class="kpi-value">{exceptions:,}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Match Rate</div>
            <div class="kpi-value">{match_rate:.2f}%</div>
        </div>
        """,
        unsafe_allow_html=True
    )
print(f"Exception rate    : {exception_rate:.2f}%")

print("\n===== EXCEPTION BREAKDOWN =====")

breakdown = df[
    df["status"] != "MATCH"
]["status"].value_counts()

print(breakdown)

print("\n===== FINANCIAL IMPACT =====")

# Calculate absolute differences
payment_difference = (
    df["payment_difference"]
    .fillna(0)
    .abs()
    .sum()
)

bank_difference = (
    df["bank_difference"]
    .fillna(0)
    .abs()
    .sum()
)

print(f"Payment discrepancies : ₹{payment_difference:,.2f}")
print(f"Bank discrepancies    : ₹{bank_difference:,.2f}")

print("\n===== TOP EXCEPTIONS =====")

exceptions_df = df[
    df["status"] != "MATCH"
].copy()

exceptions_df["total_difference"] = (
    exceptions_df["payment_difference"]
    .fillna(0)
    .abs()
    +
    exceptions_df["bank_difference"]
    .fillna(0)
    .abs()
)

top_exceptions = exceptions_df.sort_values(
    "total_difference",
    ascending=False
).head(10)

print(
    top_exceptions[
        [
            "transaction_id",
            "status",
            "total_difference"
        ]
    ].to_string(index=False)
)
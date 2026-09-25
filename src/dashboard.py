import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os

from reconcile import reconcile_data, get_summary, save_audit_log
from ai_analyzer import (
    analyze_exception,
    ask_finance_assistant,
    generate_finance_summary
)

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Finance Controller",
    page_icon="💰",
    layout="wide"
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 40px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 17px;
        color: #666666;
        margin-bottom: 25px;
    }

    .kpi-card { 
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #dddddd;
        background: white;
        text-align: center;
        min-height: 120px;
        color: #000000;
    }

    .kpi-title {
        font-size: 14px;
        color: #333333;
        margin-bottom: 10px;
    }

    .kpi-value {
        font-size: 30px;
        font-weight: 700;
        color: #000000;
    }

    .section-title {
        font-size: 25px;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def read_uploaded_file(uploaded_file):
    """
    Read CSV or Excel file safely.
    """

    file_bytes = uploaded_file.getvalue()

    if uploaded_file.name.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))

    if uploaded_file.name.lower().endswith(".xlsx"):
        return pd.read_excel(io.BytesIO(file_bytes))

    raise ValueError("Unsupported file format.")


def calculate_quality_score(df, file_type):

    total_checks = 0
    passed_checks = 0
    issues = []

    required_columns = {
        "sales": [
            "transaction_id",
            "date",
            "customer",
            "amount"
        ],
        "payments": [
            "transaction_id",
            "date",
            "customer",
            "amount",
            "status"
        ],
        "bank": [
            "transaction_id",
            "date",
            "customer",
            "amount"
        ]
    }

    # File not empty
    total_checks += 1

    if not df.empty:
        passed_checks += 1
    else:
        issues.append("File is empty.")

    if df.empty:
        return 0, issues

    # Required columns
    total_checks += 1

    missing_columns = [
        column
        for column in required_columns[file_type]
        if column not in df.columns
    ]

    if not missing_columns:
        passed_checks += 1
    else:
        issues.append(
            "Missing columns: "
            + ", ".join(missing_columns)
        )

    # Transaction ID
    total_checks += 1

    if (
        "transaction_id" in df.columns
        and not df["transaction_id"].isna().any()
    ):
        passed_checks += 1
    else:
        issues.append(
            "Some transaction IDs are missing."
        )

    # Amount
    total_checks += 1

    if "amount" in df.columns:

        numeric_amount = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        invalid_amounts = numeric_amount.isna().sum()

        if invalid_amounts == 0:
            passed_checks += 1
        else:
            issues.append(
                f"{invalid_amounts} invalid amount value(s)."
            )

    else:
        issues.append("Amount column is missing.")

    # Date
    total_checks += 1

    if "date" in df.columns:

        dates = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        invalid_dates = dates.isna().sum()

        if invalid_dates == 0:
            passed_checks += 1
        else:
            issues.append(
                f"{invalid_dates} invalid date value(s)."
            )

    else:
        issues.append("Date column is missing.")

    # Duplicate IDs
    total_checks += 1

    if "transaction_id" in df.columns:

        duplicate_count = (
            df["transaction_id"]
            .duplicated()
            .sum()
        )

        if duplicate_count == 0 or file_type == "payments":
            passed_checks += 1
        else:
            issues.append(
                f"{duplicate_count} duplicate "
                f"transaction ID(s)."
            )

    score = (
        passed_checks / total_checks * 100
        if total_checks > 0
        else 0
    )

    return round(score), issues
def style_exception_status(value):
    if value == "MATCH":
        return "color: #198754; font-weight: 700;"

    if value in [
        "PAYMENT_MISSING",
        "BANK_MISSING",
        "DUPLICATE_PAYMENT"
    ]:
        return "color: #dc3545; font-weight: 700;"

    if value in [
        "PAYMENT_AMOUNT_MISMATCH",
        "BANK_AMOUNT_MISMATCH"
    ]:
        return "color: #fd7e14; font-weight: 700;"

    return "color: #000000; font-weight: 700;"


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">💰 AI Finance Controller</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Financial reconciliation, exception detection '
    'and AI-powered financial analysis'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# TABS
# ============================================================

tab_upload, tab_summary, tab_issues, tab_ai = st.tabs(
    [
        "📂 Upload Data",
        "📊 Dashboard",
        "🚨 Issues & Analytics",
        "🤖 AI Assistant"
    ]
)


# ============================================================
# UPLOAD DATA TAB
# ============================================================

with tab_upload:

    st.markdown(
        '<div class="section-title">'
        '📂 Upload Financial Data'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Upload Sales, Payments and Bank data "
        "in CSV or Excel format."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        sales_file = st.file_uploader(
            "📊 Sales File",
            type=["csv", "xlsx"],
            key="sales_upload"
        )

    with col2:

        payments_file = st.file_uploader(
            "💳 Payments File",
            type=["csv", "xlsx"],
            key="payments_upload"
        )

    with col3:

        bank_file = st.file_uploader(
            "🏦 Bank File",
            type=["csv", "xlsx"],
            key="bank_upload"
        )

    # --------------------------------------------------------
    # Load uploaded data
    # --------------------------------------------------------

    if (
        sales_file is not None
        and payments_file is not None
        and bank_file is not None
    ):

        try:

            sales = read_uploaded_file(sales_file)
            payments = read_uploaded_file(payments_file)
            bank = read_uploaded_file(bank_file)


            # ============================================================
            # VALIDATE FILE NAMES
            # ============================================================

            if sales_file is not None:
                sales_filename = sales_file.name.lower()
                if "sales" not in sales_filename:
                    st.error(
                        "❌ Invalid Sales file.\n\n"
                        "Please upload the Sales file in the Sales File section."
                    )
                    st.stop()


            if payments_file is not None:
                payments_filename = payments_file.name.lower()

                if (
                    "payment" not in payments_filename
                    and "payments" not in payments_filename
                ):
                    st.error(
                        "❌ Invalid Payments file.\n\n"
                        "Please upload the Payments file in the Payments File section."
                    )
                    st.stop()


            if bank_file is not None:
                bank_filename = bank_file.name.lower()

                if "bank" not in bank_filename:
                    st.error(
                        "❌ Invalid Bank file.\n\n"
                        "Please upload the Bank file in the Bank File section."
                    )
                    st.stop()

            st.success(
                "✅ All three files uploaded successfully."
            )

            # ------------------------------------------------
            # Quality scores
            # ------------------------------------------------

            st.markdown(
                "### 🔎 Data Quality"
            )

            q1, q2, q3 = st.columns(3)

            sales_score, sales_issues = (
                calculate_quality_score(
                    sales,
                    "sales"
                )
            )

            payment_score, payment_issues = (
                calculate_quality_score(
                    payments,
                    "payments"
                )
            )

            bank_score, bank_issues = (
                calculate_quality_score(
                    bank,
                    "bank"
                )
            )

            q1.metric(
                "Sales Quality",
                f"{sales_score}%"
            )

            q2.metric(
                "Payments Quality",
                f"{payment_score}%"
            )

            q3.metric(
                "Bank Quality",
                f"{bank_score}%"
            )

            # ------------------------------------------------
            # Validation messages
            # ------------------------------------------------

            all_validation_issues = []

            for name, issues in [
                ("Sales", sales_issues),
                ("Payments", payment_issues),
                ("Bank", bank_issues)
            ]:

                for issue in issues:
                    all_validation_issues.append(
                        f"{name}: {issue}"
                    )

            if all_validation_issues:

                with st.expander(
                    "⚠️ Data Validation Details"
                ):

                    for issue in all_validation_issues:
                        st.warning(issue)

            else:

                st.success(
                    "✅ All uploaded files passed validation."
                )

            # ------------------------------------------------
            # Preview
            # ------------------------------------------------

            with st.expander(
                "🔍 Preview Uploaded Data"
            ):

                st.write("### Sales")

                st.dataframe(
                    sales.head(10),
                    use_container_width=True,
                    hide_index=True
                )

                st.write("### Payments")

                st.dataframe(
                    payments.head(10),
                    use_container_width=True,
                    hide_index=True
                )

                st.write("### Bank")

                st.dataframe(
                    bank.head(10),
                    use_container_width=True,
                    hide_index=True
                )

            # ------------------------------------------------
            # Uploaded record counts
            # ------------------------------------------------

            st.markdown(
                "### 📋 Uploaded Records"
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Sales Records",
                len(sales)
            )

            c2.metric(
                "Payment Records",
                len(payments)
            )

            c3.metric(
                "Bank Records",
                len(bank)
            )

            # ------------------------------------------------
            # Run reconciliation
            # ------------------------------------------------

            st.divider()

            if st.button(
                "🚀 Run Reconciliation",
                type="primary",
                use_container_width=True
            ):

                with st.spinner(
                    "Reconciling financial records..."
                ):
                    if st.button("🔄 Re-run Reconciliation"):
                        st.rerun()

                    df = reconcile_data(
                        sales,
                        payments,
                        bank
                    )
                    summary = get_summary(df)
                    if summary["exception_records"] == 0:
                        st.success("🟢 Reconciliation completed — No exceptions found.")
                    elif summary["match_rate"] >= 90:
                        st.warning("🟡 Reconciliation completed — Minor exceptions detected.")
                    else:
                        st.error("🔴 Reconciliation completed — Exceptions require review.")
                    save_audit_log(summary)

                    st.session_state[
                        "reconciliation"
                    ] = df

                    os.makedirs(
                        "data",
                        exist_ok=True
                    )

                    df.to_csv(
                        "data/reconciliation_report.csv",
                        index=False
                    )

                st.success(
                    "✅ Reconciliation completed successfully!"
                )

                st.info(
                    "Go to the 📊 Dashboard tab "
                    "to view the results."
                )

        except Exception as e:

            st.error(
                f"❌ Error processing uploaded files: {e}"
            )


# ============================================================
# CHECK RECONCILIATION
# ============================================================

if "reconciliation" not in st.session_state:

    with tab_summary:

        st.info(
            "👆 Upload all three files and click "
            "'Run Reconciliation' to view the dashboard."
        )

    with tab_issues:

        st.info(
            "Run reconciliation first to view issues."
        )

    with tab_ai:

        st.info(
            "Run reconciliation first to use "
            "the AI Finance Assistant."
        )

else:

    df = st.session_state["reconciliation"]

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = get_summary(df)

    total_records = summary["total_records"]
    matched = summary["matched_records"]
    exceptions = summary["exception_records"]
    match_rate = summary["match_rate"]

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

    exceptions_df = df[
        df["status"] != "MATCH"
    ].copy()

    # ========================================================
    # DASHBOARD TAB
    # ========================================================

    with tab_summary:

        st.markdown(
            '<div class="section-title">'
            '📊 Financial Control Overview'
            '</div>',
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # KPI CARDS
        # ----------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">
                        Total Records
                    </div>
                    <div class="kpi-value">
                        {total_records:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:

            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">
                        Matched Records
                    </div>
                    <div class="kpi-value">
                        {matched:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:

            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">
                        Exceptions
                    </div>
                    <div class="kpi-value">
                        {exceptions:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col4:

            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">
                        Match Rate
                    </div>
                    <div class="kpi-value">
                        {match_rate:.2f}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write("")

        # ----------------------------------------------------
        # AI Financial Summary
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">'
            '🤖 AI Financial Summary'
            '</div>',
            unsafe_allow_html=True
        )

        st.write(
            "Generate an AI-powered management summary "
            "of the reconciliation results."
        )

        if st.button(
            "✨ Generate AI Financial Summary",
            type="primary"
        ):

            with st.spinner(
                "🤖 Gemini is analyzing the reconciliation..."
            ):

                ai_summary = generate_finance_summary(
                    df
                )

                st.markdown(
                    "### 📋 Management Summary"
                )

                st.markdown(
                    ai_summary
                )
        # ----------------------------------------------------
        # Charts
        # ----------------------------------------------------

        chart1, chart2 = st.columns(2)

        with chart1:

            status_chart = pd.DataFrame(
                {
                    "Status": [
                        "Matched",
                        "Exceptions"
                    ],
                    "Count": [
                        matched,
                        exceptions
                    ]
                }
            )

            fig_status = px.pie(
                status_chart,
                names="Status",
                values="Count",
                hole=0.55,
                title="Matched vs Exceptions"
            )

            fig_status.update_traces(
                textinfo="label+percent",
                textposition="outside",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Transactions: %{value}<br>"
                    "Share: %{percent}"
                    "<extra></extra>"
                )
            )

            fig_status.update_layout(
                height=400,
                legend_title_text="Status"
            )

            st.plotly_chart(
                fig_status,
                use_container_width=True
            )

        with chart2:

            discrepancy_chart = pd.DataFrame(
                {
                    "Category": [
                        "Payment Discrepancy",
                        "Bank Discrepancy"
                    ],
                    "Amount": [
                        payment_difference,
                        bank_difference
                    ]
                }
            )

            fig_discrepancy = px.bar(
                discrepancy_chart,
                x="Category",
                y="Amount",
                title="Financial Discrepancies",
                text="Amount"
            )

            fig_discrepancy.update_traces(
                texttemplate="₹%{text:,.2f}",
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Amount: ₹%{y:,.2f}"
                    "<extra></extra>"
                )
            )

            fig_discrepancy.update_layout(
                height=400,
                yaxis_title="Amount (₹)",
                xaxis_title="",
                showlegend=False
            )
            st.plotly_chart(
                fig_discrepancy,
                use_container_width=True
            )

        # ----------------------------------------------------
        # Financial metrics
        # ----------------------------------------------------

        st.markdown(
            "### 💰 Financial Impact"
        )
        total_financial_impact = (
            payment_difference + bank_difference
        )
        if total_financial_impact == 0:
            impact_label = "🟢 No Financial Impact"
        elif total_financial_impact < 1000:
            impact_label = "🟡 Low Financial Impact"
        elif total_financial_impact < 10000:
            impact_label = "🟠 Moderate Financial Impact"
        else:
            impact_label = "🔴 High Financial Impact"

        st.info(f"Financial Impact Assessment: **{impact_label}**")
        f1, f2, f3 = st.columns(3)

        with f1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">
                        Payment Discrepancies
                    </div>
                    <div class="kpi-value">
                        ₹{payment_difference:,.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with f2:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">
                        Bank Discrepancies
                    </div>
                    <div class="kpi-value">
                        ₹{bank_difference:,.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with f3:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">
                        Total Financial Impact
                    </div>
                    <div class="kpi-value">
                        ₹{total_financial_impact:,.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # ----------------------------------------------------
        # Download report
        # ----------------------------------------------------

        st.divider()

        st.markdown(
            "### 📥 Reports"
        )

        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Reconciliation Report",
            data=csv_data,
            file_name="reconciliation_report.csv",
            mime="text/csv"
        )
        st.subheader("📋 Audit Trail")
        audit_file = "data/audit_log.txt"
        if os.path.exists(audit_file):
            with open(audit_file, "r", encoding="utf-8") as file:
                audit_content = file.read()

            if audit_content.strip():
                st.text_area(
                    "Reconciliation Audit History",
                    audit_content,
                    height=300
                )
            else:
                st.info("No audit records available yet.")
        else:
            st.info("No audit records available yet.")

        if not exceptions_df.empty:

            exception_csv = (
                exceptions_df
                .to_csv(index=False)
                .encode("utf-8")
            )

            st.download_button(
                "⬇️ Download Exceptions Report",
                data=exception_csv,
                file_name="financial_exceptions.csv",
                mime="text/csv"
            )

    # ========================================================
    # ISSUES & ANALYTICS TAB
    # ========================================================

    with tab_issues:

        st.markdown(
            '<div class="section-title">'
            '🚨 Issues & Analytics'
            '</div>',
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # Exception breakdown
        # ----------------------------------------------------

        if not exceptions_df.empty:

            exception_counts = (
                exceptions_df["status"]
                .value_counts()
                .reset_index()
            )

            exception_counts.columns = [
                "Exception Type",
                "Count"
            ]

            fig_exception = px.bar(
                exception_counts,
                x="Exception Type",
                y="Count",
                title="Exceptions by Type",
                text="Count"
            )

            fig_exception.update_layout(
                height=450,
                xaxis_title="Exception Type",
                yaxis_title="Number of Transactions"
            )

            st.plotly_chart(
                fig_exception,
                use_container_width=True
            )

        else:

            st.success(
                "🎉 No exceptions found!"
            )

        # ----------------------------------------------------
        # Exception details
        # ----------------------------------------------------

        st.markdown(
            "### ⚠️ Exception Details"
        )

        if not exceptions_df.empty:

            display_columns = [
                "transaction_id",
                "amount_sales",
                "amount_payment",
                "amount_bank",
                "status",
                "payment_difference",
                "bank_difference"
            ]

            display_columns = [
                column
                for column in display_columns
                if column in exceptions_df.columns
            ]

            styled_exceptions = (
                exceptions_df[
                    display_columns
                ]
                .style
                .map(
                    style_exception_status,
                    subset=["status"]
                )
            )
            st.dataframe(
                styled_exceptions,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.success(
                "No financial exceptions require review."
            )

        # ----------------------------------------------------
        # Highest financial impact
        # ----------------------------------------------------

        st.markdown(
            "### 🔎 Highest Financial Impact Transactions"
        )

        if not exceptions_df.empty:

            impact_df = exceptions_df.copy()

            impact_df["total_difference"] = (
                impact_df[
                    "payment_difference"
                ]
                .fillna(0)
                .abs()
                +
                impact_df[
                    "bank_difference"
                ]
                .fillna(0)
                .abs()
            )

            top_transactions = (
                impact_df
                .sort_values(
                    "total_difference",
                    ascending=False
                )
                .head(10)
            )

            top_columns = [
                "transaction_id",
                "status",
                "amount_sales",
                "amount_payment",
                "amount_bank",
                "total_difference"
            ]

            top_columns = [
                column
                for column in top_columns
                if column in top_transactions.columns
            ]

            st.dataframe(
                top_transactions[
                    top_columns
                ],
                use_container_width=True,
                hide_index=True
            )

        # ----------------------------------------------------
        # Transaction status summary
        # ----------------------------------------------------

        st.markdown(
            "### 📋 Transaction Status Summary"
        )

        status_summary = (
            df["status"]
            .value_counts()
            .reset_index()
        )

        status_summary.columns = [
            "Status",
            "Transactions"
        ]

        st.dataframe(
            status_summary,
            use_container_width=True,
            hide_index=True
        )

    # ========================================================
    # AI ASSISTANT TAB
    # ========================================================

    with tab_ai:

        st.markdown(
            '<div class="section-title">'
            '🤖 AI Finance Assistant'
            '</div>',
            unsafe_allow_html=True
        )

        st.write(
            "Ask questions about your financial "
            "reconciliation results."
        )

        # ----------------------------------------------------
        # Example questions
        # ----------------------------------------------------

        st.markdown(
            """
            **Example questions:**

            - Which transactions have exceptions?
            - What is the match rate?
            - Which transaction has the largest discrepancy?
            - What is the total financial impact?
            - How many payments are missing?
            - How many bank transactions are missing?
            - Are there any duplicate payments?
            - Which transactions require manual review?
            - Why is TX010 an exception?
            - Summarize the reconciliation results for management.
            """
        )

        question = st.text_input(
            "Ask a finance question:",
            placeholder=(
                "Example: Which transactions "
                "have exceptions?"
            )
        )

        if question:

            with st.spinner(
                "🤖 Gemini is analyzing your financial data..."
            ):

                answer = ask_finance_assistant(
                    question,
                    df
                )

            st.markdown(
                "### 🤖 AI Response"
            )

            st.markdown(
                answer
            )

        # ----------------------------------------------------
        # AI Exception Analyzer
        # ----------------------------------------------------

        st.divider()

        st.markdown(
            "### 🔍 AI Exception Analyzer"
        )

        if not exceptions_df.empty:

            transaction_options = (
                exceptions_df[
                    "transaction_id"
                ]
                .astype(str)
                .tolist()
            )

            selected_transaction = st.selectbox(
                "Select an exception:",
                transaction_options
            )

            selected_row = exceptions_df[
                exceptions_df[
                    "transaction_id"
                ]
                .astype(str)
                == selected_transaction
            ].iloc[0]

            # ----------------------------------------------
            # Selected transaction information
            # ----------------------------------------------

            st.markdown(
                "#### Selected Transaction"
            )

            c1, c2, c3, c4 = st.columns(4)

            sales_amount = selected_row[
                "amount_sales"
            ]

            payment_amount = selected_row[
                "amount_payment"
            ]

            bank_amount = selected_row[
                "amount_bank"
            ]

            c1.metric(
                "Sales",
                (
                    "Missing"
                    if pd.isna(sales_amount)
                    else f"₹{sales_amount:,.2f}"
                )
            )

            c2.metric(
                "Payment",
                (
                    "Missing"
                    if pd.isna(payment_amount)
                    else f"₹{payment_amount:,.2f}"
                )
            )

            c3.metric(
                "Bank",
                (
                    "Missing"
                    if pd.isna(bank_amount)
                    else f"₹{bank_amount:,.2f}"
                )
            )

            c4.metric(
                "Status",
                selected_row["status"]
            )

            # ----------------------------------------------
            # Gemini analysis
            # ----------------------------------------------

            if st.button(
                "🤖 Analyze Selected Exception",
                type="primary"
            ):

                with st.spinner(
                    "Gemini is analyzing the exception..."
                ):

                    analysis = analyze_exception(
                        selected_row
                    )

                st.markdown(
                    "### 🤖 Gemini Analysis"
                )

                st.markdown(
                    analysis
                )

                # ------------------------------------------
                # Audit trail
                # ------------------------------------------

                st.divider()

                st.markdown(
                    "### 📝 AI Audit Trail"
                )

                st.write(
                    f"**Transaction:** "
                    f"{selected_transaction}"
                )

                st.write(
                    f"**Status:** "
                    f"{selected_row['status']}"
                )

                st.write(
                    "**Analysis Mode:** Gemini AI"
                )

                st.write(
                    "**Financial Records Modified:** No"
                )

                st.caption(
                    "Gemini provides analysis and "
                    "recommendations only. Financial "
                    "adjustments require human approval."
                )

        else:

            st.success(
                "🎉 There are no exceptions to analyze."
            )
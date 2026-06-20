import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Factory Compliance Monitor",
    layout="wide"
)

st.title("🏭 Factory Compliance Monitoring System")

DB_PATH = "outputs/compliance_logs.db"

conn = sqlite3.connect(DB_PATH)

df = pd.read_sql_query(
    "SELECT * FROM violations",
    conn
)

conn.close()

# ==========================
# KPI CARDS
# ==========================

total_violations = len(df)

high_count = len(
    df[df["severity"] == "HIGH"]
)

critical_count = len(
    df[df["severity"] == "CRITICAL"]
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Violations",
    total_violations
)

col2.metric(
    "HIGH Violations",
    high_count
)

col3.metric(
    "CRITICAL Violations",
    critical_count
)

st.divider()

# ==========================
# TABLE
# ==========================

st.subheader("Violation History")

st.dataframe(
    df,
    use_container_width=True
)
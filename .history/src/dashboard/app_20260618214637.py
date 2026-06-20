import sqlite3
import pandas as pd
import streamlit as st

# ==========================
# PAGE CONFIG
# ==========================

st.set_page_config(
    page_title="Factory Compliance Monitor",
    page_icon="🏭",
    layout="wide"
)

# ==========================
# TITLE
# ==========================

st.title("🏭 Factory Compliance Monitoring System")
st.caption("AI-Powered Factory Safety & Compliance Monitoring Dashboard")

# ==========================
# DATABASE LOADER
# ==========================

DB_PATH = "outputs/compliance_logs.db"


@st.cache_data(ttl=5)
def load_data():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        "SELECT * FROM violations",
        conn
    )

    conn.close()

    return df


# ==========================
# REFRESH BUTTON
# ==========================

col_a, col_b = st.columns([1, 5])

with col_a:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()

df = load_data()

# ==========================
# HANDLE EMPTY DB
# ==========================

if df.empty:
    st.warning("No violations found in database.")
    st.stop()

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

medium_count = len(
    df[df["severity"] == "MEDIUM"]
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Violations",
        total_violations
    )

with col2:
    st.metric(
        "HIGH",
        high_count
    )

with col3:
    st.metric(
        "CRITICAL",
        critical_count
    )

with col4:
    st.metric(
        "MEDIUM",
        medium_count
    )

st.divider()

# ==========================
# CHARTS
# ==========================

left_col, right_col = st.columns(2)

# --------------------------
# Severity Chart
# --------------------------

with left_col:

    st.subheader("📊 Violations by Severity")

    severity_counts = (
        df["severity"]
        .value_counts()
    )

    st.bar_chart(severity_counts)

# --------------------------
# Behavior Chart
# --------------------------

with right_col:

    st.subheader("📈 Violations by Behavior")

    behavior_counts = (
        df["behavior_class"]
        .value_counts()
    )

    st.bar_chart(behavior_counts)

st.divider()

# ==========================
# FILTERS
# ==========================

st.subheader("🔍 Filters")

filter_col1, filter_col2 = st.columns(2)

with filter_col1:

    severity_options = [
        "All"
    ] + sorted(
        df["severity"]
        .unique()
        .tolist()
    )

    severity_filter = st.selectbox(
        "Filter by Severity",
        severity_options
    )

with filter_col2:

    behavior_options = [
        "All"
    ] + sorted(
        df["behavior_class"]
        .unique()
        .tolist()
    )

    behavior_filter = st.selectbox(
        "Filter by Behavior",
        behavior_options
    )

filtered_df = df.copy()

if severity_filter != "All":

    filtered_df = filtered_df[
        filtered_df["severity"]
        == severity_filter
    ]

if behavior_filter != "All":

    filtered_df = filtered_df[
        filtered_df["behavior_class"]
        == behavior_filter
    ]

st.divider()

# ==========================
# CSV EXPORT
# ==========================

csv = filtered_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="⬇ Download Audit Log CSV",
    data=csv,
    file_name="audit_log.csv",
    mime="text/csv"
)

# ==========================
# VIOLATION TABLE
# ==========================

st.subheader("📋 Violation History")

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

# ==========================
# FOOTER STATS
# ==========================

st.divider()

st.subheader("📌 Dashboard Summary")

col1, col2 = st.columns(2)

with col1:

    st.info(
        f"Total Records: {len(filtered_df)}"
    )

with col2:

    latest_event = (
        filtered_df.iloc[-1]["event_id"]
        if len(filtered_df) > 0
        else "N/A"
    )

    st.success(
        f"Latest Event: {latest_event}"
    )
import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Factory Compliance", page_icon="🏭", layout="wide")

# --- DATA LOADING (With Caching & Error Handling) ---
@st.cache_data(ttl=2)  # Refreshes every 2 seconds for near real-time updates
def load_data():
    db_path = "outputs/compliance_logs.db"
    
    # Graceful degradation if DB doesn't exist yet
    if not os.path.exists(db_path):
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM violations", conn)
        conn.close()
        
        if not df.empty:
            # Convert string timestamp to actual datetime objects for sorting
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Sort newest first
            df = df.sort_values(by="timestamp", ascending=False)
        return df
        
    except Exception as e:
        st.error(f"Failed to load database: {e}")
        return pd.DataFrame()

def main():
    st.title("🏭 Real-Time Compliance Dashboard")
    st.markdown("Live monitoring of automated safety violations and policy tracking.")

    df = load_data()

    if df.empty:
        st.info("No violations logged yet. Start the YOLO detection engine to see data here!")
        return

    # ==========================
    # SIDEBAR: FILTERS & EXPORT (V3 & V4)
    # ==========================
    st.sidebar.header("🔍 Filter Records")
    
    # Dynamic Severity Filter
    severities = df['severity'].unique().tolist()
    selected_severities = st.sidebar.multiselect("Filter by Severity", severities, default=severities)

    # Dynamic Behavior Filter
    behaviors = df['behavior_class'].unique().tolist()
    selected_behaviors = st.sidebar.multiselect("Filter by Behavior", behaviors, default=behaviors)

    # Apply Filters
    filtered_df = df[
        (df['severity'].isin(selected_severities)) & 
        (df['behavior_class'].isin(selected_behaviors))
    ]

    # Export to CSV Button
    st.sidebar.divider()
    st.sidebar.subheader("📥 Export Reports")
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="Download Audit Log (CSV)",
        data=csv_data,
        file_name="compliance_audit_log.csv",
        mime="text/csv"
    )

    # ==========================
    # KPI CARDS (V1)
    # ==========================
    total_violations = len(filtered_df)
    high_count = len(filtered_df[filtered_df["severity"] == "HIGH"])
    critical_count = len(filtered_df[filtered_df["severity"] == "CRITICAL"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Violations", total_violations)
    col2.metric("HIGH Severity", high_count)
    col3.metric("CRITICAL Severity", critical_count)

    st.divider()

    # ==========================
    # INTERACTIVE CHARTS (V2)
    # ==========================
    st.subheader("📊 Analytics Overview")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        if not filtered_df.empty:
            # Color-coded pie chart based on severity
            fig_severity = px.pie(
                filtered_df, 
                names='severity', 
                title="Violations by Severity",
                color='severity',
                color_discrete_map={"LOW": "#2ECC71", "MEDIUM": "#F1C40F", "HIGH": "#E67E22", "CRITICAL": "#E74C3C"}
            )
            st.plotly_chart(fig_severity, use_container_width=True)

    with chart_col2:
        if not filtered_df.empty:
            # Bar chart for behavior classes
            fig_behavior = px.bar(
                filtered_df['behavior_class'].value_counts().reset_index(),
                x='behavior_class',
                y='count',
                title="Violations by Rule Class",
                labels={'behavior_class': 'Behavior Rule', 'count': 'Frequency'},
                color_discrete_sequence=['#3498DB']
            )
            st.plotly_chart(fig_behavior, use_container_width=True)

    st.divider()

    # ==========================
    # DATA TABLE
    # ==========================
    st.subheader("📋 Violation History")
    
    # Display a clean dataframe (hide the internal DB ID)
    display_df = filtered_df.drop(columns=['id'], errors='ignore').copy()
    display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
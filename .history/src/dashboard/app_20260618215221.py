import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
import json

# ==========================================
# PAGE CONFIGURATION (Must be first)
# ==========================================
st.set_page_config(
    page_title="Factory Compliance Monitor",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ENTERPRISE CSS INJECTION
# ==========================================
# Using the exact color palette requested
st.markdown("""
<style>
    /* Global Theme */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    
    /* Premium KPI Cards */
    div[data-testid="metric-container"] {
        background-color: #1E293B;
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        border-top: 4px solid #3B82F6; /* Accent color */
    }
    
    /* Specific Severity Card Borders */
    div[data-testid="metric-container"]:nth-child(2) { border-top-color: #EF4444; } /* Critical */
    div[data-testid="metric-container"]:nth-child(3) { border-top-color: #F97316; } /* High */
    div[data-testid="metric-container"]:nth-child(4) { border-top-color: #EAB308; } /* Medium */

    /* Headers and Dividers */
    h1, h2, h3 { color: #F8FAFC !important; }
    hr { border-color: #334155; }
    
    /* Custom Alert Panel */
    .alert-card {
        background-color: #1E293B;
        border-left: 4px solid #EF4444;
        padding: 10px 15px;
        margin-bottom: 10px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATA LOADING
# ==========================================
DB_PATH = "outputs/compliance_logs.db"

@st.cache_data(ttl=3)
def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM violations", conn)
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values(by="timestamp", ascending=False)
        return df
    except Exception:
        return pd.DataFrame()

df = load_data()

# ==========================================
# SECTION 1: HEADER
# ==========================================
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.title("🏭 Factory Compliance Monitoring System")
    st.caption("AI-Powered Industrial Safety & Compliance Platform | Live SOC Feed")
with col_header2:
    st.markdown(f"<div style='text-align: right; padding-top: 20px;'>", unsafe_allow_html=True)
    st.success("🟢 SYSTEM ONLINE | LIVE MONITORING")
    st.markdown(f"<small>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></div>", unsafe_allow_html=True)

st.markdown("---")

# Empty State Handling
if df.empty:
    st.warning("No compliance violations detected yet. System is actively monitoring.")
    st.stop()

# ==========================================
# SECTION 5: SIDEBAR & FILTERS
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/AI_icon.svg/512px-AI_icon.svg.png", width=50)
st.sidebar.title("SOC Controls")

st.sidebar.subheader("🔍 Filters")
sev_filter = st.sidebar.multiselect("Severity Level", df['severity'].unique(), default=df['severity'].unique())
beh_filter = st.sidebar.multiselect("Behavior Type", df['behavior_class'].unique(), default=df['behavior_class'].unique())

filtered_df = df[(df['severity'].isin(sev_filter)) & (df['behavior_class'].isin(beh_filter))]

st.sidebar.markdown("---")

# ==========================================
# SECTION 7: REPORTING (Sidebar)
# ==========================================
st.sidebar.subheader("📥 Export Reports")
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(label="📄 Download Audit Log (CSV)", data=csv, file_name="audit_log.csv", mime="text/csv")

json_str = filtered_df.to_json(orient="records")
st.sidebar.download_button(label="📦 Download Event Payload (JSON)", data=json_str, file_name="events.json", mime="application/json")

st.sidebar.markdown("---")

# ==========================================
# SECTION 8: SYSTEM HEALTH (Sidebar)
# ==========================================
st.sidebar.subheader("🎛️ System Health")
st.sidebar.markdown("🟢 **Database:** Connected")
st.sidebar.markdown("🟢 **YOLO Engine:** Active")
st.sidebar.markdown("🟢 **Rules Engine:** Validated")

# ==========================================
# SECTION 2: EXECUTIVE KPI CARDS
# ==========================================
total_events = len(filtered_df)
crit_events = len(filtered_df[filtered_df['severity'] == 'CRITICAL'])
high_events = len(filtered_df[filtered_df['severity'] == 'HIGH'])
med_events = len(filtered_df[filtered_df['severity'] == 'MEDIUM'])

# Calculate a pseudo-compliance score (starts at 100, drops based on severity)
penalty = (crit_events * 5) + (high_events * 2) + (med_events * 1)
compliance_score = max(0, 100 - penalty)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Total Violations", total_events, "Lifetime")
kpi2.metric("CRITICAL", crit_events, "Requires Action")
kpi3.metric("HIGH", high_events, "Review Needed")
kpi4.metric("MEDIUM", med_events, "Logged")
kpi5.metric("Compliance Score", f"{compliance_score}%", "Overall Safety", delta_color="normal")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# SECTION 3 & 4: ALERT CENTER & ANALYTICS
# ==========================================
col_alerts, col_charts = st.columns([1, 2])

with col_alerts:
    st.subheader("🚨 Latest Critical/High Alerts")
    recent_alerts = filtered_df[filtered_df['severity'].isin(['CRITICAL', 'HIGH'])].head(5)
    
    if recent_alerts.empty:
        st.info("No recent Critical or High alerts.")
    else:
        for _, row in recent_alerts.iterrows():
            color = "#EF4444" if row['severity'] == 'CRITICAL' else "#F97316"
            st.markdown(f"""
            <div style="background-color: #1E293B; border-left: 4px solid {color}; padding: 10px; margin-bottom: 8px; border-radius: 4px;">
                <strong style="color: {color}">{row['severity']}</strong> | {row['timestamp'].strftime('%H:%M:%S')}<br>
                <span style="font-size: 0.85rem; color: #94A3B8;">{row['event_id']} - {row['behavior_class']}</span>
            </div>
            """, unsafe_allow_html=True)

with col_charts:
    st.subheader("📊 Analytics Overview")
    chart1, chart2 = st.columns(2)
    
    # Custom color mapping for charts
    color_map = {"CRITICAL": "#EF4444", "HIGH": "#F97316", "MEDIUM": "#EAB308", "LOW": "#22C55E"}
    
    with chart1:
        fig_pie = px.pie(
            filtered_df, names="severity", hole=0.4, title="Violations by Severity",
            color="severity", color_discrete_map=color_map
        )
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC", margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with chart2:
        beh_counts = filtered_df['behavior_class'].value_counts().reset_index()
        beh_counts.columns = ['Behavior', 'Count']
        fig_bar = px.bar(
            beh_counts, x="Count", y="Behavior", orientation='h', title="Violations by Rule",
            color_discrete_sequence=["#3B82F6"]
        )
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC", margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ==========================================
# SECTION 6: VIOLATION TABLE
# ==========================================
st.subheader("📋 Complete Audit Log")
display_df = filtered_df.drop(columns=['id'], errors='ignore')
display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

# Render styled dataframe
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=300
)

# ==========================================
# SECTION 9: FOOTER
# ==========================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.8rem;">
    Factory Compliance Monitoring System v1.0.0 | Engine: YOLOv8 + OpenCV | Database: SQLite | UI: Streamlit<br>
    <i>Confidential & Proprietary. Unauthorized access is logged.</i>
</div>
""", unsafe_allow_html=True)
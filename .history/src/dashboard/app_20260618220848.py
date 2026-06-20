"""
Factory Compliance Monitoring System - Enterprise Dashboard
Version: 2.0.0
A professional industrial AI monitoring platform for compliance tracking.
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Tuple

# ==========================================
# PAGE CONFIGURATION (Must be first)
# ==========================================
st.set_page_config(
    page_title="Factory Compliance Monitoring System",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# COLOR PALETTE & CONSTANTS
# ==========================================
COLORS = {
    "bg_primary": "#0F172A",
    "bg_secondary": "#1E293B",
    "border": "#334155",
    "text": "#F8FAFC",
    "text_muted": "#94A3B8",
    "critical": "#EF4444",
    "high": "#F97316",
    "medium": "#EAB308",
    "safe": "#22C55E",
    "accent": "#3B82F6",
    "info": "#06B6D4",
}

SEVERITY_COLORS = {
    "CRITICAL": COLORS["critical"],
    "HIGH": COLORS["high"],
    "MEDIUM": COLORS["medium"],
    "LOW": COLORS["safe"],
}

# ==========================================
# ENTERPRISE CSS INJECTION
# ==========================================
st.markdown(f"""
<style>
    /* Global Theme */
    .stApp {{
        background-color: {COLORS["bg_primary"]};
        color: {COLORS["text"]};
    }}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: {COLORS["bg_primary"]};
        border-right: 1px solid {COLORS["border"]};
    }}
    
    /* Premium KPI Cards */
    div[data-testid="metric-container"] {{
        background: linear-gradient(135deg, {COLORS["bg_secondary"]} 0%, rgba(30, 41, 59, 0.5) 100%);
        border: 1px solid {COLORS["border"]};
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        border-top: 4px solid {COLORS["accent"]};
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }}
    
    div[data-testid="metric-container"]:hover {{
        box-shadow: 0 20px 40px rgba(59, 130, 246, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transform: translateY(-2px);
    }}
    
    /* Severity Card Top Borders */
    div[data-testid="metric-container"]:nth-child(1) {{ border-top-color: {COLORS["info"]}; }}
    div[data-testid="metric-container"]:nth-child(2) {{ border-top-color: {COLORS["critical"]}; }}
    div[data-testid="metric-container"]:nth-child(3) {{ border-top-color: {COLORS["high"]}; }}
    div[data-testid="metric-container"]:nth-child(4) {{ border-top-color: {COLORS["medium"]}; }}
    div[data-testid="metric-container"]:nth-child(5) {{ border-top-color: {COLORS["safe"]}; }}
    div[data-testid="metric-container"]:nth-child(6) {{ border-top-color: {COLORS["accent"]}; }}

    /* Headers */
    h1, h2, h3, h4, h5, h6 {{
        color: {COLORS["text"]} !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }}
    
    /* Dividers */
    hr {{
        border: 0;
        border-top: 1px solid {COLORS["border"]};
        margin: 2rem 0;
    }}
    
    /* Alert Panel Styling */
    .alert-critical {{
        background-color: rgba(239, 68, 68, 0.1);
        border-left: 4px solid {COLORS["critical"]};
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);
    }}
    
    .alert-high {{
        background-color: rgba(249, 115, 22, 0.1);
        border-left: 4px solid {COLORS["high"]};
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.15);
    }}
    
    /* Status Badges */
    .status-online {{
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: {COLORS["safe"]};
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 10px {COLORS["safe"]};
        animation: pulse 2s infinite;
    }}
    
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 10px {COLORS["safe"]}; }}
        50% {{ box-shadow: 0 0 20px {COLORS["safe"]}; }}
        100% {{ box-shadow: 0 0 10px {COLORS["safe"]}; }}
    }}
    
    /* Buttons */
    .stButton button {{
        background: linear-gradient(135deg, {COLORS["accent"]} 0%, rgba(59, 130, 246, 0.8) 100%);
        border: 1px solid {COLORS["accent"]};
        color: {COLORS["text"]};
        font-weight: 600;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }}
    
    .stButton button:hover {{
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.5);
        transform: translateY(-2px);
    }}
    
    /* Download Button */
    .stDownloadButton button {{
        background: linear-gradient(135deg, {COLORS["safe"]} 0%, rgba(34, 197, 94, 0.8) 100%);
        border: 1px solid {COLORS["safe"]};
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATA LOADING & HELPER FUNCTIONS
# ==========================================
DB_PATH = "outputs/compliance_logs.db"

@st.cache_data(ttl=3)
def load_data():
    """Load compliance violations from SQLite database."""
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
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def render_header():
    """Render professional header section with system status."""
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <h1 style="margin: 0; font-size: 2.5rem;">🏭 Factory Compliance Monitoring System</h1>
            <p style="color: {COLORS['text_muted']}; margin: 10px 0 0 0; font-size: 1.1rem;">AI-Powered Industrial Safety & Compliance Platform</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        col_status1, col_status2 = st.columns(2)
        with col_status1:
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 5px;">
                    <span class="status-online"></span>ONLINE
                </div>
                <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">System</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_status2:
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 1rem; font-weight: bold; color: {COLORS['info']}; margin-bottom: 5px;">🔴 LIVE</div>
                <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">Monitoring</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="text-align: right; color: {COLORS['text_muted']}; font-size: 0.9rem; margin-top: 10px;">
        Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

def render_kpi_cards(data: pd.DataFrame):
    """Render professional KPI cards with metrics."""
    if data.empty:
        return
    
    total_events = len(data)
    crit_count = len(data[data['severity'] == 'CRITICAL'])
    high_count = len(data[data['severity'] == 'HIGH'])
    medium_count = len(data[data['severity'] == 'MEDIUM'])
    low_count = len(data[data['severity'] == 'LOW'])
    
    penalty = (crit_count * 5) + (high_count * 2) + (medium_count * 0.5)
    compliance_score = max(0, min(100, 100 - penalty))
    
    cols = st.columns(6)
    
    with cols[0]:
        st.metric("Total Violations", total_events, "Events Monitored")
    
    with cols[1]:
        st.metric("🔴 Critical", crit_count, "Immediate Action")
    
    with cols[2]:
        st.metric("🟠 High", high_count, "Requires Review")
    
    with cols[3]:
        st.metric("🟡 Medium", medium_count, "Monitor")
    
    with cols[4]:
        st.metric("🟢 Low", low_count, "Logged")
    
    with cols[5]:
        st.metric("Compliance %", f"{compliance_score:.1f}%", "Safety Score")
    
    st.markdown("")

def render_alert_center(data: pd.DataFrame):
    """Render alert center with latest violations."""
    st.subheader("🚨 Alert Center - Latest Critical/High Violations")
    
    alerts = data[data['severity'].isin(['CRITICAL', 'HIGH'])].head(8)
    
    if alerts.empty:
        st.info("✅ No critical or high-severity violations detected.")
        return
    
    for idx, row in alerts.iterrows():
        severity = row['severity']
        color = SEVERITY_COLORS.get(severity, COLORS["accent"])
        icon = "🔴" if severity == "CRITICAL" else "🟠"
        
        ts = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        st.markdown(f"""
        <div class="alert-{severity.lower()}">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <div style="font-weight: 700; color: {color}; margin-bottom: 6px;">
                        {icon} [{severity}] {row['behavior_class']}
                    </div>
                    <div style="color: {COLORS['text_muted']}; font-size: 0.9rem; margin-bottom: 8px;">
                        Event ID: <code>{row['event_id']}</code>
                    </div>
                    <div style="color: {COLORS['text']}; font-size: 0.9rem; margin-bottom: 8px;">
                        {row['description'][:100]}...
                    </div>
                    <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">
                        📍 {ts} | Policy: {row['policy_rule_ref']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_analytics_section(data: pd.DataFrame):
    """Render professional analytics charts."""
    st.subheader("📊 Analytics Dashboard")
    
    if data.empty:
        st.info("No data available for analytics.")
        return
    
    col_pie, col_bar = st.columns([1, 1])
    
    with col_pie:
        severity_counts = data['severity'].value_counts().reset_index()
        severity_counts.columns = ['Severity', 'Count']
        
        colors_list = [SEVERITY_COLORS.get(sev, COLORS["accent"]) for sev in severity_counts['Severity']]
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=severity_counts['Severity'],
            values=severity_counts['Count'],
            hole=0.4,
            marker=dict(colors=colors_list, line=dict(color=COLORS["bg_primary"], width=2)),
            textposition='inside',
            textfont=dict(color=COLORS["text"], size=12),
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
        )])
        
        fig_donut.update_layout(
            title=dict(text="Violations by Severity", font=dict(size=16, color=COLORS["text"])),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=COLORS["text"],
            margin=dict(t=50, b=20, l=20, r=20),
            showlegend=True,
            height=350
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with col_bar:
        behavior_counts = data['behavior_class'].value_counts().head(10).reset_index()
        behavior_counts.columns = ['Behavior', 'Count']
        
        fig_bar = go.Figure(data=[go.Bar(
            y=behavior_counts['Behavior'],
            x=behavior_counts['Count'],
            orientation='h',
            marker=dict(
                color=behavior_counts['Count'],
                colorscale=[[0, COLORS["safe"]], [0.5, COLORS["medium"]], [1, COLORS["critical"]]],
                line=dict(color=COLORS["border"], width=1)
            ),
            text=behavior_counts['Count'],
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>Violations: %{x}<extra></extra>'
        )])
        
        fig_bar.update_layout(
            title=dict(text="Violations by Behavior Type", font=dict(size=16, color=COLORS["text"])),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=COLORS["text"],
            margin=dict(t=50, b=20, l=150, r=20),
            showlegend=False,
            height=350,
            xaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS["border"]),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    col_trend = st.columns(1)[0]
    with col_trend:
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['timestamp']).dt.date
        trend_data = data_copy.groupby(['date', 'severity']).size().reset_index(name='count')
        
        fig_trend = px.line(
            trend_data,
            x='date',
            y='count',
            color='severity',
            markers=True,
            color_discrete_map=SEVERITY_COLORS,
            title="Violation Trend Over Time",
            labels={'date': 'Date', 'count': 'Violation Count', 'severity': 'Severity'},
        )
        
        fig_trend.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=COLORS["text"],
            margin=dict(t=50, b=20, l=50, r=20),
            height=350,
            hovermode='x unified',
            xaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS["border"]),
            yaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS["border"]),
        )
        
        fig_trend.update_traces(
            line=dict(width=3),
            marker=dict(size=8),
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)

def render_filter_panel(data: pd.DataFrame) -> Tuple[list, list, tuple]:
    """Render filter panel and return filter values."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        severity_filter = st.multiselect(
            "🔴 Severity Levels",
            ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
            default=["CRITICAL", "HIGH", "MEDIUM"],
            help="Filter violations by severity level"
        )
    
    with col2:
        behavior_options = sorted(data['behavior_class'].unique().tolist()) if not data.empty else []
        behavior_filter = st.multiselect(
            "📋 Behavior Types",
            behavior_options,
            default=behavior_options,
            help="Filter violations by detected behavior"
        )
    
    with col3:
        date_range = st.date_input(
            "📅 Date Range",
            value=(
                (pd.Timestamp.now() - timedelta(days=30)).date(),
                pd.Timestamp.now().date()
            ),
            max_value=pd.Timestamp.now().date(),
            help="Select date range for filtering"
        )
    
    return severity_filter, behavior_filter, date_range

def render_violation_table(data: pd.DataFrame):
    """Render enhanced violation table."""
    st.subheader("📋 Violation Audit Log")
    
    if data.empty:
        st.info("No violations matching the selected filters.")
        return
    
    display_df = data.copy()
    display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    display_columns = [
        'timestamp', 'event_id', 'severity', 'behavior_class',
        'description', 'policy_rule_ref', 'escalation_action'
    ]
    
    display_df = display_df[display_columns]
    display_df.columns = [
        'Timestamp', 'Event ID', 'Severity', 'Behavior',
        'Description', 'Policy', 'Action'
    ]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    st.markdown(f"<small style='color: {COLORS['text_muted']}'>Total Records: {len(display_df)}</small>", unsafe_allow_html=True)

def render_system_health():
    """Render system health status panel."""
    st.subheader("🎛️ System Health & Diagnostics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    health_items = [
        ("Database", "Connected", True),
        ("YOLO Engine", "Active", True),
        ("Rules Engine", "Validated", True),
        ("Dashboard", "Online", True),
    ]
    
    for col, (name, status, is_online) in zip([col1, col2, col3, col4], health_items):
        with col:
            indicator = "🟢" if is_online else "🔴"
            status_color = COLORS["safe"] if is_online else COLORS["critical"]
            st.markdown(f"""
            <div style="background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 16px; text-align: center;">
                <div style="font-size: 1.8rem; margin-bottom: 8px;">{indicator}</div>
                <div style="font-weight: 600; margin-bottom: 4px;">{name}</div>
                <div style="color: {status_color}; font-size: 0.9rem;">{status}</div>
            </div>
            """, unsafe_allow_html=True)

def render_export_section(data: pd.DataFrame):
    """Render export and reporting section."""
    st.subheader("📥 Export & Reporting")
    
    if data.empty:
        st.warning("No data available for export.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_data = data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download CSV Report",
            data=csv_data,
            file_name=f"compliance_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        json_data = data.to_json(orient="records", indent=2).encode('utf-8')
        st.download_button(
            label="📦 Download JSON Export",
            data=json_data,
            file_name=f"compliance_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col3:
        if st.button("📊 Generate Compliance Report"):
            total = len(data)
            critical = len(data[data['severity'] == 'CRITICAL'])
            high = len(data[data['severity'] == 'HIGH'])
            compliance = max(0, 100 - ((critical * 5) + (high * 2)))
            
            st.success(f"✅ Report Generated: {total} total events, {critical} critical, Compliance: {compliance:.1f}%")

def render_footer():
    """Render professional footer."""
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <small style="color: {COLORS['text_muted']}">
        <strong>Factory Compliance Monitoring System v2.0.0</strong><br>
        © 2024 All Rights Reserved
        </small>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <small style="color: {COLORS['text_muted']}">
        <strong>Technology Stack:</strong><br>
        YOLOv8 • OpenCV • PyTorch • SQLite • Streamlit
        </small>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <small style="color: {COLORS['text_muted']}">
        <strong>Last Refresh:</strong><br>
        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
        </small>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="text-align: center; color: {COLORS['text_muted']}; font-size: 0.75rem; margin-top: 20px;">
    <i>Confidential & Proprietary. Unauthorized access is logged and monitored.</i>
    </div>
    """, unsafe_allow_html=True)

# Load Data
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
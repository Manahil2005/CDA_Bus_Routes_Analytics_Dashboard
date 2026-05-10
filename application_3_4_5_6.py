import streamlit as st
import pandas as pd
from pyvis.network import Network
import tempfile, json
import networkx as nx
import os
import json
import collections
import pandas as pd
import networkx as nx
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

st.set_page_config(page_title="CDA Bus Route Analytics Dashboard", layout="wide")

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Custom CSS for dark theme and styling
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .stApp { background-color: #0f1117; color: #e0e0e0; }
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #252a3a);
        border: 1px solid #3a4060;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
    }
    .metric-label { font-size: 12px; color: #8899bb; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #4fc3f7; margin: 4px 0; }
    .metric-sub   { font-size: 11px; color: #6677aa; }
    .section-header {
        font-size: 15px; font-weight: 600; color: #90caf9;
        border-left: 3px solid #4fc3f7; padding-left: 10px; margin: 12px 0 8px 0;
    }
    .freq-row {
        display: flex; justify-content: space-between;
        background: #1a1f2e; border: 1px solid #3a4060;
        border-radius: 8px; padding: 7px 12px; margin: 3px 0;
        font-size: 12px;
    }
    .bottleneck-row {
        display: flex; justify-content: space-between;
        background: #2a1a1a; border: 1px solid #c62828;
        border-radius: 8px; padding: 7px 12px; margin: 3px 0;
        font-size: 12px;
    }
    .stSelectbox label { color: #90caf9 !important; font-size: 13px; }
    iframe { border-radius: 10px; border: 1px solid #2a3050; }
    .stat-box {
        background: #1a1f2e;
        border: 1px solid #3a4060;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    
    /* Tab color fix */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #4fc3f7 !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }
    .stTabs [data-baseweb="tab-list"] button:hover [data-testid="stMarkdownContainer"] p {
        color: #90caf9 !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] [data-testid="stMarkdownContainer"] p {
        color: #e3f2fd !important;
        font-weight: 700 !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom-color: #4fc3f7 !important;
        border-bottom-width: 3px !important;
    }
    .stTabs [data-baseweb="tab-list"] button:hover {
        background-color: rgba(79, 195, 247, 0.1) !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1a1f2e;
        padding: 5px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
    }

    /* ═══════════════════════════════════════════
       CHAT INPUT — dark background, white text
    ═══════════════════════════════════════════ */
    /* Outer wrapper */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] > div > div {
        background-color: #0d1b2a !important;
        border-color: #1e3a5f !important;
    }
    /* The actual textarea */
    [data-testid="stChatInput"] textarea,
    div[class*="chatInputWrapper"] textarea,
    div[class*="ChatInput"] textarea {
        background-color: #0d1b2a !important;
        color: #ffffff !important;
        caret-color: #4fc3f7 !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    /* Placeholder text */
    [data-testid="stChatInput"] textarea::placeholder {
        color: #4a6fa5 !important;
        opacity: 1 !important;
    }
    /* Send button */
    [data-testid="stChatInput"] button {
        background-color: #1e3a5f !important;
        border-color: #4fc3f7 !important;
    }
    [data-testid="stChatInput"] button svg {
        fill: #4fc3f7 !important;
        stroke: #4fc3f7 !important;
    }
    [data-testid="stChatInput"] button:hover {
        background-color: #4fc3f7 !important;
    }
    [data-testid="stChatInput"] button:hover svg {
        fill: #0d1b2a !important;
        stroke: #0d1b2a !important;
    }

    /* ═══════════════════════════════════════════
       CHAT MESSAGES — force white text everywhere
    ═══════════════════════════════════════════ */
    [data-testid="stChatMessage"] {
        background-color: #111827 !important;
        border: 1px solid #1e2d40 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin: 4px 0 !important;
    }
    /* Every possible text node inside a message */
    [data-testid="stChatMessage"] *,
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] em,
    [data-testid="stChatMessage"] code {
        color: #e3f2fd !important;
        -webkit-text-fill-color: #e3f2fd !important;
    }
    /* User bubble slightly different */
    [data-testid="stChatMessage"][data-testid*="user"],
    .stChatMessage:nth-child(odd) {
        background-color: #0d1f35 !important;
    }

    /* ═══════════════════════════════════════════
       SPINNER TEXT
    ═══════════════════════════════════════════ */
    [data-testid="stChatMessage"] [data-testid="stText"],
    [data-testid="stChatMessage"] small {
        color: #90caf9 !important;
        -webkit-text-fill-color: #90caf9 !important;
    }
</style>
""", unsafe_allow_html=True)

# Data Loading and Preprocessing
@st.cache_data
def load_data():
    df = pd.read_csv('routes.csv')
    df['arrival_time'] = pd.to_datetime(df['arrival_time'])
    df['departure_time'] = pd.to_datetime(df['departure_time'])
    return df

@st.cache_data
def build_graph_data(df):
    """Build edge statistics: avg transition duration and case frequency."""
    edges = {}
    for trip_id, grp in df.groupby('trip_id'):
        grp = grp.sort_values('stop_order')
        route_id = grp['route_id'].iloc[0]
        stops = grp[['stop_name', 'departure_time']].values.tolist()
        for i in range(len(stops) - 1):
            src, dep = stops[i]
            dst      = stops[i + 1][0]
            arr      = grp.iloc[i + 1]['arrival_time']
            dur      = (arr - dep).total_seconds()
            if dur < 0:
                dur = 0
            key = (src, dst, route_id)
            if key not in edges:
                edges[key] = {'durations': [], 'trips': set()}
            edges[key]['durations'].append(dur)
            edges[key]['trips'].add(trip_id)

    records = []
    for (src, dst, route_id), v in edges.items():
        avg = sum(v['durations']) / len(v['durations'])
        records.append({
            'src': src, 'dst': dst, 'route_id': route_id,
            'avg_dur': avg,
            'case_freq': len(v['trips'])
        })
    return pd.DataFrame(records)

@st.cache_data
def calculate_throughput_times(df):
    """Calculate throughput time per trip."""
    trip_times = df.groupby('trip_id').agg(
        first_arrival=('arrival_time', 'min'),
        last_departure=('departure_time', 'max')
    )
    trip_times['total_duration'] = trip_times['last_departure'] - trip_times['first_arrival']
    return trip_times

@st.cache_data
def detect_bottlenecks(df):
    """Detect bottleneck transitions."""
    # Sort data
    df_sorted = df.sort_values(by=['trip_id', 'stop_order']).copy()
    
    # Calculate next stop and next departure
    df_sorted['next_stop'] = df_sorted.groupby('trip_id')['stop_name'].shift(-1)
    df_sorted['next_arrival'] = df_sorted.groupby('trip_id')['arrival_time'].shift(-1)
    
    # Calculate transition duration
    df_sorted['duration'] = df_sorted['next_arrival'] - df_sorted['departure_time']
    
    # Clean data (remove last stops)
    df_clean = df_sorted.dropna(subset=['next_stop'])
    df_clean['duration_seconds'] = df_clean['duration'].dt.total_seconds()
    
    # Calculate average duration per edge
    edges = df_clean.groupby(['stop_name', 'next_stop']).agg(
        avg_duration_seconds=('duration_seconds', 'mean')
    ).reset_index()
    
    # Convert back to timedelta
    edges['avg_duration'] = pd.to_timedelta(edges['avg_duration_seconds'], unit='s')
    
    # Define bottleneck threshold (75th percentile)
    threshold = edges['avg_duration_seconds'].quantile(0.75)
    
    # Mark bottlenecks
    edges['is_bottleneck'] = edges['avg_duration_seconds'] > threshold
    
    # Get top 3 slowest transitions
    top3 = edges.nlargest(3, 'avg_duration_seconds')
    
    return edges, top3, threshold

def fmt_sec(seconds):
    s = int(seconds)
    m, sec = divmod(s, 60)
    if m == 0:
        return f"{sec}s"
    elif m < 60:
        return f"{m}m {sec}s"
    else:
        h, m = divmod(m, 60)
        return f"{h}h {m}m"

def fmt_timedelta(td):
    """Format timedelta object to string."""
    if pd.isna(td):
        return "N/A"
    seconds = td.total_seconds()
    return fmt_sec(seconds)

def build_pyvis(edge_df, bottleneck_edges, selected_route):
    """Build a PyVis directed process map with bottleneck highlighting."""
    if selected_route != "All Routes":
        edge_df = edge_df[edge_df['route_id'] == selected_route]

    # Aggregate data
    if selected_route == "All Routes":
        agg = edge_df.groupby(['src', 'dst']).agg(
            avg_dur=('avg_dur', 'mean'),
            case_freq=('case_freq', 'sum'),
            routes=('route_id', lambda x: ', '.join(sorted(x.unique())))
        ).reset_index()
    else:
        agg = edge_df[['src', 'dst', 'avg_dur', 'case_freq']].copy()
        agg['routes'] = selected_route

    net = Network(height="640px", width="100%", directed=True,
                  bgcolor="#0f1117", font_color="#e0e0e0")
    net.set_options(json.dumps({
        "physics": {
            "enabled": True,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
                "gravitationalConstant": -80,
                "springLength": 130,
                "springConstant": 0.05
            },
            "stabilization": {"iterations": 200}
        },
        "edges": {
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.6}},
            "smooth": {"type": "dynamic"},
            "font": {"size": 11, "color": "#cdd6f4", "strokeWidth": 2, "strokeColor": "#0f1117"}
        },
        "nodes": {
            "shape": "dot",
            "font": {"size": 12, "color": "#e0e0e0"},
            "borderWidth": 2
        },
        "interaction": {"hover": True, "tooltipDelay": 100}
    }))

    # Create a set of bottleneck edges for quick lookup
    bottleneck_set = set()
    for _, row in bottleneck_edges.iterrows():
        if row['is_bottleneck']:
            bottleneck_set.add((row['stop_name'], row['next_stop']))

    # Calculate node frequencies for sizing
    node_freq = {}
    for _, row in agg.iterrows():
        node_freq[row['src']] = node_freq.get(row['src'], 0) + row['case_freq']
        node_freq[row['dst']] = node_freq.get(row['dst'], 0) + row['case_freq']

    added_nodes = set()
    for _, row in agg.iterrows():
        for node in [row['src'], row['dst']]:
            if node not in added_nodes:
                sz = min(30, 12 + node_freq.get(node, 1) // 10)
                net.add_node(
                    node, label=node, size=sz,
                    color={"border": "#4fc3f7", "background": "#1e2a3a",
                           "highlight": {"border": "#90caf9", "background": "#2a3a5a"}},
                    title=f"<b>{node}</b><br>Total cases: {node_freq.get(node, 0)}"
                )
                added_nodes.add(node)

        # Determine if this edge is a bottleneck
        is_bottleneck = (row['src'], row['dst']) in bottleneck_set
        edge_color = "#ef5350" if is_bottleneck else "#4fc3f7"
        edge_width = 3 if is_bottleneck else 2
        
        # Edge label in required format
        label = (
            f"{row['src']} → {row['dst']} = "
            f"{fmt_sec(row['avg_dur'])}"
        )

        # Tooltip
        tooltip = (
            f"<b>{row['src']} → {row['dst']}</b><br>"
            f"Avg duration: {fmt_sec(row['avg_dur'])}<br>"
            f"Cases: {int(row['case_freq'])}<br>"
            f"Routes: {row['routes']}"
        )
        
        if is_bottleneck:
            tooltip += "<br><span style='color:#ef5350'>⚠️ BOTTLENECK TRANSITION</span>"
        
        net.add_edge(
            row['src'], row['dst'],
            label=label, title=tooltip,
            color=edge_color, width=edge_width,
            arrows="to"
        )

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode='w') as f:
        net.save_graph(f.name)
        return open(f.name).read()

@st.cache_resource
def get_transit_graph(_df):
    G = nx.DiGraph()
    # Add travel edges
    for (rid, direction), group in _df.groupby(['route_id', 'direction']):
        trip_id = group['trip_id'].iloc[0]
        trip_data = group[group['trip_id'] == trip_id].sort_values('stop_order')
        stops = trip_data.to_dict('records')
        for i in range(len(stops) - 1):
            s1, s2 = stops[i], stops[i+1]
            n1, n2 = (s1['stop_name'], rid, direction), (s2['stop_name'], rid, direction)
            dur = (s2['arrival_time'] - s1['departure_time']).total_seconds()
            # Forward edge
            G.add_edge(n1, n2, weight=max(0, dur), type='travel', action=f"Ride {rid}")
            # Backward edge (Bidirectional logic for incomplete datasets)
            G.add_edge(n2, n1, weight=max(0, dur), type='travel', action=f"Ride {rid} (Return)")
    
    # Add transfer edges
    for stop_name, group in _df.groupby('stop_name'):
        rds = group[['route_id', 'direction']].drop_duplicates().values.tolist()
        for i in range(len(rds)):
            for j in range(len(rds)):
                if i != j:
                    n1, n2 = (stop_name, rds[i][0], rds[i][1]), (stop_name, rds[j][0], rds[j][1])
                    if G.has_node(n1) and G.has_node(n2):
                        G.add_edge(n1, n2, weight=360, type='transfer', action=f"Transfer to {rds[j][0]} (6m wait)")
    return G

# Personal Routes Mapping (Task 6)
PERSONAL_ROUTES = {
    "Rizwan Saeed": {"from": "N5 Metro Station", "to": "FAST University", "home": "G-15"},
    "Maryam Farooq": {"from": "Taxila", "to": "FAST University", "home": "Taxila Chowk"},
    "Manahil": {"from": "Khanna Pul", "to": "FAST University", "home": "Khanna Pull"},
    "Ayesha Khan": {"from": "I-14 Markaz", "to": "FAST University", "home": "I-14 Markar"},
    "Zainab Naeem": {"from": "PIMS Metro Station", "to": "FAST University", "home": "PIMS"}
}

# Main App Logic
df = load_data()
edge_df = build_graph_data(df)
routes = sorted(df['route_id'].unique())

# Bottleneck detection
bottleneck_edges_all, top3_bottlenecks_all, threshold_all = detect_bottlenecks(df)

st.markdown("""
<div style='background:linear-gradient(90deg,#1a237e,#0d47a1,#01579b);
            padding:18px 28px;border-radius:12px;margin-bottom:20px;'>
  <h2 style='margin:0;color:#e3f2fd;'>🚍 CDA Bus Route Analytics Dashboard</h2>
  <p style='margin:4px 0 0;color:#90caf9;font-size:13px;'>
    Capital Development Authority · Islamabad Transit Network · Performance & Bottleneck Analytics
  </p>
</div>
""", unsafe_allow_html=True)

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
total_stops = df['stop_name'].nunique()
total_trips = df['trip_id'].nunique()
bottleneck_count = bottleneck_edges_all['is_bottleneck'].sum()

with m1:
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-label'>Total Routes</div>
        <div class='metric-value'>{len(routes)}</div>
        <div class='metric-sub'>CDA Feeder Routes</div>
    </div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-label'>Total Stops</div>
        <div class='metric-value'>{total_stops}</div>
        <div class='metric-sub'>Unique bus stops</div>
    </div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-label'>Total Trips</div>
        <div class='metric-value'>{total_trips}</div>
        <div class='metric-sub'>Across all routes</div>
    </div>""", unsafe_allow_html=True)
with m4:
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-label'>⚠️ Bottlenecks</div>
        <div class='metric-value' style='color:#ef5350'>{bottleneck_count}</div>
        <div class='metric-sub'>Slow transitions detected</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Global route filter
route_options = ["All Routes"] + routes
selected_route = st.selectbox("🔍 Filter by Route", route_options)

# Filter data based on selected route
if selected_route == "All Routes":
    filtered_df = df
    filtered_trip_times = calculate_throughput_times(df)
    filtered_bottleneck_edges, filtered_top3, filtered_threshold = detect_bottlenecks(df)
else:
    filtered_df = df[df['route_id'] == selected_route]
    filtered_trip_times = calculate_throughput_times(filtered_df)
    filtered_bottleneck_edges, filtered_top3, filtered_threshold = detect_bottlenecks(filtered_df)

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🗺️ Process Map", "📊 Throughput Analysis", "⚠️ Bottleneck Analysis", "🗺️ Trip Planner", "🤖 AI Chatbot", "👤 Personal Routes"])

with tab1:
    # Map and Side Panel
    map_col, panel_col = st.columns([3, 1])
    
    with map_col:
        st.markdown("<div class='section-header'>Process Map with Bottleneck Highlighting</div>", unsafe_allow_html=True)
        st.caption("🔴 Red edges indicate bottleneck transitions (above 75th percentile)")
        with st.spinner("Building process map..."):
            html_content = build_pyvis(edge_df, bottleneck_edges_all, selected_route)
        st.components.v1.html(html_content, height=650, scrolling=False)
    
    with panel_col:
        # Case Frequency Panel
        st.markdown("<div class='section-header'>📈 Case Frequency</div>", unsafe_allow_html=True)
        st.caption("Number of trips per transition")
        
        if selected_route == "All Routes":
            freq_df = edge_df.groupby(['src', 'dst']).agg(case_freq=('case_freq', 'sum')).reset_index()
        else:
            freq_df = edge_df[edge_df['route_id'] == selected_route][['src', 'dst', 'case_freq']].copy()
        
        top_freq = freq_df.nlargest(10, 'case_freq')
        for row in top_freq.itertuples():
            st.markdown(f"""<div class='freq-row'>
                <span style='color:#cdd6f4;font-size:11px'>{row.src[:15]} → {row.dst[:15]}</span>
                <span style='color:#4fc3f7;font-weight:600'>{row.case_freq}</span>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("<br><div class='section-header'>⚠️ Bottlenecks in View</div>", unsafe_allow_html=True)
        st.caption("Red edges = bottleneck transitions")
        
        # Show bottlenecks for selected route
        if selected_route == "All Routes":
            route_bottlenecks = bottleneck_edges_all[bottleneck_edges_all['is_bottleneck'] == True]
        else:
            route_stops = filtered_df['stop_name'].unique()
            route_bottlenecks = bottleneck_edges_all[
                (bottleneck_edges_all['is_bottleneck'] == True) &
                (bottleneck_edges_all['stop_name'].isin(route_stops))
            ]
        
        for _, row in route_bottlenecks.head(5).iterrows():
            st.markdown(f"""<div class='bottleneck-row'>
                <span style='color:#ef9a9a;font-size:11px'>{row['stop_name'][:12]} → {row['next_stop'][:12]}</span>
                <span style='color:#ef5350;font-weight:600'>{fmt_timedelta(row['avg_duration'])}</span>
            </div>""", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='section-header'>📊 Throughput Time Analysis</div>", unsafe_allow_html=True)
    
    if selected_route == "All Routes":
        st.info("📊 Showing data for **ALL ROUTES**")
    else:
        st.success(f"📊 Showing data for **{selected_route}** only")
    
    if len(filtered_trip_times) > 0:
        unique_durations = filtered_trip_times['total_duration'].nunique()
        
        if unique_durations == 1 and selected_route != "All Routes":
            # All trips have same duration
            trip_duration = filtered_trip_times['total_duration'].iloc[0]
            total_trips_count = len(filtered_trip_times)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""<div class='stat-box'>
                    <div style='color:#8899bb; font-size:12px'>Trip Duration</div>
                    <div style='font-size:32px; font-weight:700; color:#4fc3f7'>{fmt_timedelta(trip_duration)}</div>
                    <div style='color:#6677aa; font-size:11px'>all trips on this route</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class='stat-box'>
                    <div style='color:#8899bb; font-size:12px'>Total Trips</div>
                    <div style='font-size:32px; font-weight:700; color:#66bb6a'>{total_trips_count}</div>
                    <div style='color:#6677aa; font-size:11px'>on this route</div>
                </div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""<div class='stat-box'>
                    <div style='color:#8899bb; font-size:12px'>Schedule Pattern</div>
                    <div style='font-size:20px; font-weight:700; color:#ffa726'>Consistent</div>
                    <div style='color:#6677aa; font-size:11px'>identical trip times</div>
                </div>""", unsafe_allow_html=True)
            
            st.info(f"ℹ️ All {total_trips_count} trips on route **{selected_route}** have the exact same duration of **{fmt_timedelta(trip_duration)}**. This indicates a fixed schedule pattern.")
            
        else:
            avg_trip_time = filtered_trip_times['total_duration'].mean()
            min_time = filtered_trip_times['total_duration'].min()
            max_time = filtered_trip_times['total_duration'].max()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""<div class='stat-box'>
                    <div style='color:#8899bb; font-size:12px'>Average Trip Duration</div>
                    <div style='font-size:32px; font-weight:700; color:#4fc3f7'>{fmt_timedelta(avg_trip_time)}</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class='stat-box'>
                    <div style='color:#8899bb; font-size:12px'>Fastest Trip</div>
                    <div style='font-size:32px; font-weight:700; color:#66bb6a'>{fmt_timedelta(min_time)}</div>
                </div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""<div class='stat-box'>
                    <div style='color:#8899bb; font-size:12px'>Slowest Trip</div>
                    <div style='font-size:32px; font-weight:700; color:#ef5350'>{fmt_timedelta(max_time)}</div>
                </div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Summary statistics table
        st.markdown("<div class='section-header'>Summary Statistics</div>", unsafe_allow_html=True)
        
        if unique_durations == 1 and selected_route != "All Routes":
            stats_df = pd.DataFrame({
                'Metric': ['Trip Duration', 'Total Trips', 'Schedule Type', 'Consistency'],
                'Value': [
                    fmt_timedelta(filtered_trip_times['total_duration'].iloc[0]),
                    f"{len(filtered_trip_times)} trips",
                    "Fixed Schedule",
                    "100% Consistent"
                ]
            })
        else:
            stats_df = pd.DataFrame({
                'Metric': ['Mean', 'Median', 'Minimum', 'Maximum', 'Standard Deviation', 'Total Trips Analyzed'],
                'Value': [
                    fmt_timedelta(filtered_trip_times['total_duration'].mean()),
                    fmt_timedelta(filtered_trip_times['total_duration'].median()),
                    fmt_timedelta(filtered_trip_times['total_duration'].min()),
                    fmt_timedelta(filtered_trip_times['total_duration'].max()),
                    fmt_timedelta(pd.Timedelta(seconds=filtered_trip_times['total_duration'].dt.total_seconds().std())),
                    f"{len(filtered_trip_times)} trips"
                ]
            })
        
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
    else:
        st.warning(f"No trip data available for {selected_route}")

with tab3:
    st.markdown("<div class='section-header'>⚠️ Bottleneck Detection & Analysis</div>", unsafe_allow_html=True)
    
    if selected_route == "All Routes":
        st.info("⚠️ Showing bottlenecks for **ALL ROUTES**")
    else:
        st.success(f"⚠️ Showing bottlenecks for **{selected_route}** only")
    
    if len(filtered_bottleneck_edges) > 0:
        st.info(f"**Methodology:** Bottlenecks are defined as transitions with average duration above the 75th percentile threshold of **{fmt_timedelta(pd.Timedelta(seconds=filtered_threshold))}**")
        
        col1, col2 = st.columns(2)
        bottleneck_count_filtered = filtered_bottleneck_edges['is_bottleneck'].sum()
        with col1:
            st.markdown(f"""<div class='stat-box'>
                <div style='color:#8899bb; font-size:12px'>Total Bottlenecks Detected</div>
                <div style='font-size:32px; font-weight:700; color:#ef5350'>{bottleneck_count_filtered}</div>
                <div style='color:#6677aa; font-size:11px'>out of {len(filtered_bottleneck_edges)} total transitions</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            bottleneck_percentage = (bottleneck_count_filtered / len(filtered_bottleneck_edges)) * 100 if len(filtered_bottleneck_edges) > 0 else 0
            st.markdown(f"""<div class='stat-box'>
                <div style='color:#8899bb; font-size:12px'>Bottleneck Percentage</div>
                <div style='font-size:32px; font-weight:700; color:#ffa726'>{bottleneck_percentage:.1f}%</div>
                <div style='color:#6677aa; font-size:11px'>of all transitions</div>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Top 3 Slowest Transitions
        st.markdown("<div class='section-header'>🐌 Top 3 Slowest Transitions</div>", unsafe_allow_html=True)
        
        filtered_top3_filtered = filtered_bottleneck_edges.nlargest(3, 'avg_duration_seconds')
        for idx, row in filtered_top3_filtered.iterrows():
            st.markdown(f"""
            <div style='background:linear-gradient(90deg,#2a1a1a,#1a1f2e); border-left:4px solid #ef5350; border-radius:8px; padding:12px; margin:10px 0'>
                <div style='display:flex; justify-content:space-between; align-items:center'>
                    <div>
                        <span style='color:#ef9a9a; font-weight:600'>⚠️ {row['stop_name']}</span>
                        <span style='color:#8899bb'> → </span>
                        <span style='color:#ef9a9a; font-weight:600'>{row['next_stop']}</span>
                    </div>
                    <div style='background:#c62828; padding:4px 12px; border-radius:20px'>
                        <span style='color:white; font-weight:700'>{fmt_timedelta(row['avg_duration'])}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # All bottlenecks table
        st.markdown("<div class='section-header'>All Bottleneck Transitions</div>", unsafe_allow_html=True)
        
        bottleneck_display = filtered_bottleneck_edges[filtered_bottleneck_edges['is_bottleneck'] == True][
            ['stop_name', 'next_stop', 'avg_duration']
        ].copy()
        bottleneck_display['avg_duration'] = bottleneck_display['avg_duration'].apply(fmt_timedelta)
        bottleneck_display.columns = ['From Stop', 'To Stop', 'Average Duration']
        
        st.dataframe(bottleneck_display, use_container_width=True, hide_index=True)
        
        # Export option
        st.markdown("<div class='section-header'>📥 Export Analysis</div>", unsafe_allow_html=True)
        csv_bottlenecks = filtered_bottleneck_edges[filtered_bottleneck_edges['is_bottleneck'] == True].to_csv(index=False)
        st.download_button(
            label="Download Bottleneck Data (CSV)",
            data=csv_bottlenecks,
            file_name=f"cda_bottlenecks_{selected_route.replace(' ', '_')}.csv",
            mime="text/csv"
        )
    else:
        st.warning(f"No bottleneck data available for {selected_route}")

with tab4:
    # Trip Planner Section
    st.markdown("<div class='section-header'>🗺️ Plan Your Journey</div>", unsafe_allow_html=True)
    
    # Get unique sorted stop names
    unique_stops = sorted(df['stop_name'].dropna().unique())
    
    col1, col2 = st.columns(2)
    with col1:
        from_stop = st.selectbox("From:", options=["Select an origin..."] + unique_stops, index=0)
    with col2:
        to_stop = st.selectbox("To:", options=["Select a destination..."] + unique_stops, index=0)
    
    if from_stop != "Select an origin..." and to_stop != "Select a destination..." and from_stop != to_stop:
        G = get_transit_graph(df)
        G_search = G.copy()
        G_search.add_node("START")
        G_search.add_node("END")
        
        for n in G.nodes():
            if n[0] == from_stop: 
                G_search.add_edge("START", n, weight=0)
            if n[0] == to_stop:   
                G_search.add_edge(n, "END", weight=0)
        
        try:
            path = nx.shortest_path(G_search, "START", "END", weight="weight")
            total_sec = nx.shortest_path_length(G_search, "START", "END", weight="weight")
            
            m, s = divmod(int(total_sec), 60)
            st.success(f"✅ Optimal route found: **{m}m {s}s** total travel time.")
            
            itinerary = []
            for i in range(1, len(path) - 2):
                u, v = path[i], path[i+1]
                edge = G_search[u][v]
                if i == 1 or edge['type'] == 'transfer':
                    itinerary.append({"Stop": u[0], "Action": edge['action']})
            
            itinerary.append({"Stop": path[-2][0], "Action": "🏁 Arrive at Destination"})
            st.table(pd.DataFrame(itinerary))
            
            with st.expander("📍 Detailed Stop-by-Stop Path"):
                full_path = []
                for i in range(1, len(path)-1):
                    full_path.append(path[i][0])
                st.write(" ➔ ".join(full_path))
                
        except nx.NetworkXNoPath:
            st.error("❌ No feasible route found between these stops.")
    elif from_stop == to_stop and from_stop != "Select an origin...":
        st.warning("⚠️ Origin and Destination cannot be the same.")

with tab5:

    # ── Tab 5 Custom CSS ─────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .ai-hero {
        background: linear-gradient(135deg, #0a1628 0%, #0d2137 40%, #0a1f3a 70%, #071525 100%);
        border: 1px solid #1e3a5f;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .ai-hero-title { font-size: 26px; font-weight: 800; color: #e3f2fd; margin: 0 0 6px 0; letter-spacing: -0.5px; }
    .ai-hero-sub { font-size: 13px; color: #64b5f6; margin: 0; display: flex; align-items: center; gap: 8px; }
    .ai-badge {
        background: rgba(79,195,247,0.15); border: 1px solid rgba(79,195,247,0.3);
        color: #4fc3f7; font-size: 10px; font-weight: 600;
        padding: 2px 8px; border-radius: 20px; letter-spacing: 0.5px; text-transform: uppercase;
    }
    .ai-status-bar {
        display: flex; align-items: center; gap: 10px;
        background: #111827; border: 1px solid #1f2d3d;
        border-radius: 10px; padding: 10px 16px; margin-bottom: 20px; font-size: 12px;
    }
    .ai-status-dot { width: 8px; height: 8px; border-radius: 50%; background: #4caf50; box-shadow: 0 0 6px #4caf50; animation: pulse-green 2s infinite; flex-shrink: 0; }
    .ai-status-dot.offline { background: #f44336; box-shadow: 0 0 6px #f44336; animation: none; }
    @keyframes pulse-green { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
    .prompts-label { font-size: 11px; font-weight: 700; color: #546e7a; text-transform: uppercase; letter-spacing: 1.5px; margin: 0 0 10px 2px; }
    .stButton > button {
        background: linear-gradient(135deg, #0d1b2a, #132030) !important;
        border: 1px solid #1e3a5f !important; color: #90caf9 !important;
        border-radius: 10px !important; font-size: 12px !important;
        padding: 9px 14px !important; transition: all 0.2s ease !important;
        text-align: left !important; white-space: normal !important;
        height: auto !important; min-height: 48px !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #132030, #1a2d45) !important;
        border-color: #4fc3f7 !important; color: #e3f2fd !important;
        transform: translateY(-1px) !important; box-shadow: 0 4px 15px rgba(79,195,247,0.15) !important;
    }
    .ai-divider { border: none; border-top: 1px solid #1a2535; margin: 20px 0; }
    .ai-stats-strip { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 18px; }
    .ai-stat-chip { background: #0d1b2a; border: 1px solid #1e3a5f; border-radius: 8px; padding: 8px 14px; font-size: 12px; color: #64b5f6; display: flex; align-items: center; gap: 6px; }
    .ai-stat-chip b { color: #e3f2fd; font-size: 14px; }
    .clear-btn > button { background: transparent !important; border: 1px solid #3a2020 !important; color: #ef9a9a !important; font-size: 11px !important; min-height: 32px !important; padding: 4px 12px !important; }
    .clear-btn > button:hover { border-color: #f44336 !important; color: #f44336 !important; transform: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Load API key ─────────────────────────────────────────────────────────
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
    ai_api_key = os.getenv("GITHUB_TOKEN")

    ai_token_ok = bool(ai_api_key)
    status_dot  = "ai-status-dot" if ai_token_ok else "ai-status-dot offline"
    status_text = "Connected · GitHub Models · GPT-4o mini" if ai_token_ok else "Token missing — add GITHUB_TOKEN to .env"

    st.markdown(f"""
    <div class="ai-hero">
      <div class="ai-hero-title">🤖 AI Trip Planner</div>
      <div class="ai-hero-sub">
        <span class="ai-badge">Free</span>
        Ask anything about CDA Islamabad bus routes — stops, times, transfers
      </div>
    </div>
    <div class="ai-status-bar">
      <div class="{status_dot}"></div>
      <span style="color:#90a4ae;font-size:12px;">{status_text}</span>
    </div>
    """, unsafe_allow_html=True)

    if not ai_token_ok:
        st.error("❌ **GITHUB_TOKEN not found.** Add it to your `.env` file and restart the app.")
        st.code("GITHUB_TOKEN=ghp_your_token_here", language="bash")
        st.stop()

    n_routes = df["route_id"].nunique()
    n_stops  = df["stop_name"].nunique()
    n_trips  = df["trip_id"].nunique()
    st.markdown(f"""
    <div class="ai-stats-strip">
      <div class="ai-stat-chip">🗺️ <b>{n_routes}</b> Routes</div>
      <div class="ai-stat-chip">🚏 <b>{n_stops}</b> Stops</div>
      <div class="ai-stat-chip">🚌 <b>{n_trips}</b> Trips</div>
      <div class="ai-stat-chip">📊 Grounded in routes.csv</div>
    </div>
    """, unsafe_allow_html=True)

    # ── FIXED: Comprehensive knowledge base builder ───────────────────────────
    def ai_build_kb(dataframe):
        """
        Build a complete knowledge base grounded entirely in routes.csv.
        Includes: all routes with full stop lists, departure times per trip,
        stop-to-route mapping, transfer points, and edge travel times.
        This prevents hallucination by giving the AI only real data.
        """
        # 1. Full route stop sequences with ALL departure times
        routes_data = []
        for route_id, route_grp in dataframe.groupby("route_id"):
            for direction, dir_grp in route_grp.groupby("direction"):
                # Get the canonical stop order from one representative trip
                rep_trip = dir_grp.sort_values("stop_order")["trip_id"].iloc[0]
                trip_stops = dir_grp[dir_grp["trip_id"] == rep_trip].sort_values("stop_order")
                stop_sequence = trip_stops["stop_name"].tolist()

                # Collect ALL departure times from the first stop across all trips
                first_stop = stop_sequence[0]
                all_departures = sorted(
                    dir_grp[dir_grp["stop_name"] == first_stop]["departure_time"]
                    .dropna()
                    .apply(lambda t: t.strftime("%H:%M"))
                    .unique()
                    .tolist()
                )

                routes_data.append({
                    "route": route_id,
                    "direction": direction,
                    "stops": stop_sequence,
                    "departures_from_first_stop": all_departures
                })

        # 2. Stop → routes mapping (which routes serve each stop)
        stop_to_routes = {}
        for stop, grp in dataframe.groupby("stop_name"):
            stop_to_routes[stop] = sorted(grp["route_id"].unique().tolist())

        # 3. Transfer points (stops served by 2+ routes — key for trip planning)
        transfer_stops = {
            stop: routes
            for stop, routes in stop_to_routes.items()
            if len(routes) > 1
        }

        # 4. Edge travel times (src → dst average minutes per route)
        edge_times = []
        df_sorted = dataframe.sort_values(["trip_id", "stop_order"])
        df_sorted = df_sorted.copy()
        df_sorted["next_stop"] = df_sorted.groupby("trip_id")["stop_name"].shift(-1)
        df_sorted["next_arrival"] = df_sorted.groupby("trip_id")["arrival_time"].shift(-1)
        df_sorted["seg_secs"] = (
            df_sorted["next_arrival"] - df_sorted["departure_time"]
        ).dt.total_seconds()
        valid = df_sorted.dropna(subset=["next_stop"]).copy()
        valid = valid[(valid["seg_secs"] >= 0) & (valid["seg_secs"] <= 7200)]
        for (src, dst, rid), grp in valid.groupby(["stop_name", "next_stop", "route_id"]):
            avg_min = round(grp["seg_secs"].mean() / 60, 1)
            edge_times.append({"from": src, "to": dst, "route": rid, "avg_min": avg_min})

        return json.dumps({
            "routes": routes_data,
            "stop_to_routes": stop_to_routes,
            "transfer_stops": transfer_stops,
            "edge_travel_times": edge_times
        }, separators=(",", ":"), default=str)

    # ── FIXED: System prompt enforcing required response format ───────────────
    def ai_system_prompt(kb_json):
        return f"""You are a trip-planning assistant for the CDA (Capital Development Authority) bus network in Islamabad, Pakistan.

CRITICAL RULES — follow every one, every time:
1. Use ONLY the data provided below. NEVER invent stops, route IDs, or times.
2. If a stop is not in the data, say "This stop is not in the current dataset."
3. For every trip-planning query, your response MUST include all three of these:
   a) ROUTE(S) & TRANSFERS: The route ID(s) to take and where to transfer (if needed).
   b) ESTIMATED TRAVEL TIME: Sum the avg_min values along the path from the edge_travel_times data.
   c) NEXT DEPARTURE: Check departures_from_first_stop for the relevant route and suggest the next time.
4. For transfer journeys: identify stops that appear in transfer_stops (served by multiple routes).
5. Keep responses concise — under 120 words. Use a clear structured format.
6. If no path exists, say so honestly.

RESPONSE FORMAT for trip queries:
🚌 Route: [route ID(s)]
🔄 Transfers: [transfer stop and route change, or "Direct — no transfer needed"]
⏱️ Est. Time: [X min based on schedule data]
🕐 Next Departure: [HH:MM from first stop]
📝 Notes: [any relevant info]

NETWORK DATA (complete, grounded in routes.csv):
{kb_json}"""

    # ── Quick-prompt buttons ─────────────────────────────────────────────────
    st.markdown('<div class="prompts-label">💡 Quick Prompts</div>', unsafe_allow_html=True)
    ai_examples = [
        ("🗺️", "How to get from Khanna Pul to NUST Metro Station?"),
        ("📍", "Which routes go through Faizabad?"),
        ("🕐", "When does the last bus leave from H-9?"),
        ("⏱️", "Travel time from Khanna Pul to Faizabad?"),
        ("🔄", "Do any routes connect G-9 Markaz to F-10 Markaz?"),
        ("🚌", "What is the headway on route FR-01?"),
    ]
    qp_cols = st.columns(3)
    for idx, (icon, example) in enumerate(ai_examples):
        with qp_cols[idx % 3]:
            if st.button(f"{icon} {example}", key=f"ai_ex_{idx}", use_container_width=True):
                st.session_state.setdefault("ai_chat", [])
                st.session_state["ai_chat"].append({"role": "user", "content": example})
                st.session_state["ai_auto"] = True
                st.rerun()

    st.markdown('<hr class="ai-divider">', unsafe_allow_html=True)

    # ── Chat history ─────────────────────────────────────────────────────────
    if "ai_chat" not in st.session_state:
        st.session_state["ai_chat"] = []

    if not st.session_state["ai_chat"]:
        st.markdown("""
        <div style="text-align:center; padding:32px 0; color:#2a3f5f;">
          <div style="font-size:40px; margin-bottom:10px;">🚍</div>
          <div style="font-size:14px; color:#3a5070;">Ask me anything about CDA bus routes!</div>
          <div style="font-size:12px; color:#2a3f5f; margin-top:4px;">Try one of the quick prompts above or type your own question</div>
        </div>
        """, unsafe_allow_html=True)

    for ai_msg in st.session_state["ai_chat"]:
        ai_av = "🧑" if ai_msg["role"] == "user" else "🚍"
        with st.chat_message(ai_msg["role"], avatar=ai_av):
            st.markdown(ai_msg["content"])

    # ── Input & response ─────────────────────────────────────────────────────
    ai_auto  = st.session_state.pop("ai_auto", False)
    ai_input = st.chat_input("Ask about routes, stops, travel times…", key="ai_input")

    if ai_input:
        st.session_state["ai_chat"].append({"role": "user", "content": ai_input})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(ai_input)
        ai_auto = True

    if ai_auto and st.session_state["ai_chat"] and \
       st.session_state["ai_chat"][-1]["role"] == "user":

        with st.chat_message("assistant", avatar="🚍"):
            with st.spinner("Planning your route…"):
                try:
                    # Build full KB — grounded in ALL route data
                    ai_kb     = ai_build_kb(df)
                    ai_system = ai_system_prompt(ai_kb)

                    # If KB is too large for context, trim edge_times only (keep routes + stops intact)
                    if len(ai_system) // 4 > 6000:
                        kb_dict = json.loads(ai_kb)
                        kb_dict["edge_travel_times"] = kb_dict["edge_travel_times"][:80]
                        ai_kb     = json.dumps(kb_dict, separators=(",", ":"), default=str)
                        ai_system = ai_system_prompt(ai_kb)

                    client = OpenAI(
                        api_key=ai_api_key,
                        base_url="https://models.github.ai/inference"
                    )

                    # Send system prompt + last 6 messages (3 turns) to stay within token limits
                    ai_messages = [{"role": "developer", "content": ai_system}]
                    for m in st.session_state["ai_chat"][-6:]:
                        ai_messages.append({"role": m["role"], "content": m["content"]})

                    try:
                        ai_response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=ai_messages,
                            temperature=0.3,   # lower = more factual, less hallucination
                            max_tokens=350
                        )
                        ai_reply = ai_response.choices[0].message.content

                    except Exception as e:
                        err = str(e)
                        if "413" in err or "tokens_limit_reached" in err:
                            # Emergency fallback: routes + stops only, no edge times
                            kb_dict = json.loads(ai_kb)
                            slim_kb = {
                                "routes": [
                                    {"route": r["route"], "direction": r["direction"],
                                     "stops": r["stops"], "departures_from_first_stop": r["departures_from_first_stop"][:5]}
                                    for r in kb_dict["routes"]
                                ],
                                "transfer_stops": kb_dict["transfer_stops"]
                            }
                            ai_messages[0]["content"] = ai_system_prompt(
                                json.dumps(slim_kb, separators=(",", ":"), default=str)
                            )
                            ai_response = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=ai_messages[:4],
                                temperature=0.3,
                                max_tokens=300
                            )
                            ai_reply = ai_response.choices[0].message.content + \
                                       "\n\n_⚠️ Note: Edge timing data was trimmed due to context size._"
                        elif "429" in err or "rate_limit" in err:
                            ai_reply = "🚦 **Rate limit reached.** Please wait a moment before asking another question."
                        elif "401" in err or "Unauthorized" in err:
                            ai_reply = "❌ **Authentication failed.** Please check your `GITHUB_TOKEN` in the `.env` file."
                        else:
                            ai_reply = f"⚠️ Error: {err[:200]}"

                except Exception as e:
                    ai_reply = f"⚠️ Setup Error: {str(e)[:200]}"

            st.markdown(ai_reply)
            st.session_state["ai_chat"].append({"role": "assistant", "content": ai_reply})

    # ── Footer row ───────────────────────────────────────────────────────────
    if st.session_state.get("ai_chat"):
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        fc1, fc2 = st.columns([6, 1])
        msg_count = len(st.session_state["ai_chat"])
        with fc1:
            st.markdown(
                f"<div style='font-size:11px;color:#37474f;padding-top:8px;'>"
                f"💬 {msg_count} message{'s' if msg_count != 1 else ''} in this session</div>",
                unsafe_allow_html=True
            )
        with fc2:
            with st.container():
                st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
                if st.button("🗑️ Clear", key="ai_clear", use_container_width=True):
                    st.session_state["ai_chat"] = []
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
with tab6:
    st.markdown("<div class='section-header'>👤 Team Member Personal Routes</div>", unsafe_allow_html=True)
    st.info("Task 6: Individual route mapping from home address to FAST University.")
    
    selected_member = st.selectbox("Select Member Name:", options=["-- Select --"] + list(PERSONAL_ROUTES.keys()))
    
    if selected_member != "-- Select --":
        route_data = PERSONAL_ROUTES[selected_member]
        st.markdown(f"### {selected_member}'s Route")
        st.markdown(f"**Home Area:** {route_data['home']}")
        st.markdown(f"**Nearest Bus Stop:** {route_data['from']}")
        st.markdown(f"**Destination:** {route_data['to']}")
        
        G = get_transit_graph(df)
        G_search = G.copy()
        G_search.add_node("HOME")
        G_search.add_node("FAST")
        
        for n in G.nodes():
            if n[0] == route_data['from']: 
                G_search.add_edge("HOME", n, weight=0)
            if n[0] == route_data['to']:   
                G_search.add_edge(n, "FAST", weight=0)
        
        try:
            path = nx.shortest_path(G_search, "HOME", "FAST", weight="weight")
            total_sec = nx.shortest_path_length(G_search, "HOME", "FAST", weight="weight")
            
            m, s = divmod(int(total_sec), 60)
            st.success(f"✅ Route Found: Approximately **{m}m {s}s** travel time.")
            
            # Build mini-map
            net = Network(height="500px", width="100%", directed=True, bgcolor="#0f1117", font_color="#e0e0e0")
            
            # Use hierarchical layout for a clean sequential path
            options = {
                "layout": {
                    "hierarchical": {
                        "enabled": True,
                        "direction": "LR",
                        "sortMethod": "directed",
                        "levelSeparation": 150,
                        "nodeSpacing": 100
                    }
                },
                "physics": {"enabled": False},
                "edges": {
                    "arrows": {"to": {"enabled": True, "scaleFactor": 0.5}},
                    "smooth": {"type": "cubicBezier", "forceDirection": "horizontal", "roundness": 0.4},
                    "font": {"size": 10, "color": "#cdd6f4", "strokeWidth": 0}
                },
                "nodes": {
                    "shape": "dot",
                    "font": {"size": 14, "face": "Inter"}
                }
            }
            net.set_options(json.dumps(options))
            
            # Add nodes with distinct styling
            for i, node in enumerate(path[1:-1]):
                stop_name = node[0]
                is_start = (stop_name == route_data['from'])
                is_end = (stop_name == route_data['to'])
                
                color = "#4fc3f7" 
                size = 15
                if is_start:
                    color = "#ffa726" 
                    size = 25
                elif is_end:
                    color = "#66bb6a" 
                    size = 25
                
                net.add_node(stop_name, label=stop_name, color=color, size=size, level=i)
            
            # Add edges
            for i in range(1, len(path) - 2):
                u, v = path[i], path[i+1]
                edge_data = G_search[u][v]
                label = edge_data['action']
                net.add_edge(u[0], v[0], label=label, color="#4fc3f7", width=2)
            
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode='w') as f:
                net.save_graph(f.name)
                st.components.v1.html(open(f.name).read(), height=520)
                
            st.markdown("#### 📋 Detailed Itinerary")
            itinerary = []
            for i in range(1, len(path) - 1):
                u = path[i]
                if i < len(path) - 2:
                    v = path[i+1]
                    edge = G_search[u][v]
                    itinerary.append({"Stop": u[0], "Instruction": edge['action']})
                else:
                    itinerary.append({"Stop": u[0], "Instruction": "🏁 Arrive at FAST University"})
            
            st.table(pd.DataFrame(itinerary))
            
        except nx.NetworkXNoPath:
            st.error(f"❌ No feasible transit route found from {route_data['from']} to FAST University in the current dataset.")

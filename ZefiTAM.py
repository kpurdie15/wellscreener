import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Appalachian Basin Oil & Gas Aggregator",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-card {
        background-color: #1E293B;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #334155;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94A3B8;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #F8FAFC;
    }
</style>
""", unsafe_allow_html=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

TARGET_COLS = ['State', 'Permit_ID', 'Well_Number', 'Operator', 'County', 'Type', 'Status']

# ---------------------------------------------------------
# HELPER: ARCGIS PAGINATED FETCH
# ---------------------------------------------------------
def fetch_arcgis_paginated(url, where_clause="1=1", max_records=5000, batch_size=1000):
    """Loops through ArcGIS REST API using resultOffset to bypass the 1k limit."""
    all_records = []
    offset = 0
    
    while offset < max_records:
        params = {
            'where': where_clause,
            'outFields': '*',
            'resultOffset': offset,
            'resultRecordCount': batch_size,
            'returnGeometry': 'false',
            'f': 'json'
        }
        try:
            res = requests.get(url, params=params, headers=HEADERS, timeout=12)
            data = res.json()
            features = data.get('features', [])
            if not features:
                break
            
            records = [f['attributes'] for f in features]
            all_records.extend(records)
            
            # If batch returned fewer than batch_size, we reached the end
            if len(features) < batch_size:
                break
                
            offset += batch_size
        except Exception:
            break
            
    return pd.DataFrame(all_records)

# ---------------------------------------------------------
# STATE FETCHERS
# ---------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_ohio_data():
    """Ohio ODNR Open GIS API"""
    url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Oil_and_Gas_Wells_Locations_of_Ohio/FeatureServer/0/query"
    try:
        df = fetch_arcgis_paginated(url, max_records=5000)
        if not df.empty:
            df['State'] = 'OH'
            # Check for multiple possible column name variants
            permit_col = 'PERMIT_NBR' if 'PERMIT_NBR' in df.columns else 'PERMIT'
            owner_col = 'OWNER_NAME' if 'OWNER_NAME' in df.columns else 'OPERATOR'
            
            df = df.rename(columns={
                permit_col: 'Permit_ID',
                'WELL_NUMBER': 'Well_Number',
                owner_col: 'Operator',
                'COUNTY': 'County',
                'WELL_TYPE': 'Type',
                'WELL_STATUS': 'Status'
            })
            return df
    except Exception as e:
        st.warning(f"Ohio Fetch Warning: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_pa_data():
    """Pennsylvania DEP GIS API"""
    url = "https://gis.dep.pa.gov/depgisprd/rest/services/OilGas/OilGasAllStrayGas/MapServer/3/query"
    try:
        df = fetch_arcgis_paginated(url, max_records=5000)
        if not df.empty:
            df['State'] = 'PA'
            df = df.rename(columns={
                'PERMIT_NUMBER': 'Permit_ID',
                'WELL_NUMBER': 'Well_Number',
                'OPERATOR_NAME': 'Operator',
                'COUNTY': 'County',
                'WELL_TYPE': 'Type',
                'WELL_STATUS': 'Status'
            })
            return df
    except Exception as e:
        st.warning(f"PA Fetch Warning: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_ny_data():
    """New York Open Data Socrata API (Paginated)"""
    url = "https://data.ny.gov/resource/3ub5-233v.json?$limit=5000"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        df = pd.DataFrame(res.json())
        if not df.empty:
            df['State'] = 'NY'
            df['Well_Number'] = df.get('well_name', df.get('api_well_number', 'N/A'))
            df = df.rename(columns={
                'api_well_number': 'Permit_ID',
                'operator_name': 'Operator',
                'county': 'County',
                'well_type': 'Type',
                'well_status': 'Status'
            })
            return df
    except Exception as e:
        st.warning(f"NY Fetch Warning: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_wv_data():
    """West Virginia DEP GIS API"""
    url = "https://services.arcgis.com/jDGuO8tYggdCCnUJ/arcgis/rest/services/W_Virginia_1112018/FeatureServer/1/query"
    try:
        df = fetch_arcgis_paginated(url, max_records=5000)
        if not df.empty:
            df['State'] = 'WV'
            df['Type'] = 'Oil/Gas'
            df = df.rename(columns={
                'API': 'Permit_ID',
                'WELL_NO': 'Well_Number',
                'OPERATOR': 'Operator',
                'COUNTY': 'County',
                'STATUS': 'Status'
            })
            return df
    except Exception as e:
        st.warning(f"WV Fetch Warning: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_ky_data():
    """Kentucky Geological Survey API"""
    url = "https://kgs.uky.edu/arcgis/rest/services/OilGas/KY_OilGas_Wells/MapServer/0/query"
    try:
        # KY KGS uses a direct query format
        params = {
            'where': '1=1',
            'outFields': '*',
            'resultRecordCount': 2000,
            'returnGeometry': 'false',
            'f': 'json'
        }
        res = requests.get(url, params=params, headers=HEADERS, timeout=15, verify=False)
        records = [f['attributes'] for f in res.json().get('features', [])]
        df = pd.DataFrame(records)
        if not df.empty:
            df['State'] = 'KY'
            op_col = 'OPERATOR_NAME' if 'OPERATOR_NAME' in df.columns else 'OPERATOR'
            df = df.rename(columns={
                'PERMIT_NO': 'Permit_ID',
                'WELL_NO': 'Well_Number',
                op_col: 'Operator',
                'COUNTY': 'County',
                'WELL_TYPE': 'Type',
                'STATUS': 'Status'
            })
            return df
    except Exception as e:
        st.warning(f"KY Fetch Warning: {e}")
    return pd.DataFrame()

def get_aggregated_data(selected_states, max_per_state):
    dfs = []
    state_map = {
        "OH": fetch_ohio_data,
        "PA": fetch_pa_data,
        "NY": fetch_ny_data,
        "WV": fetch_wv_data,
        "KY": fetch_ky_data
    }
    
    for state in selected_states:
        if state in state_map:
            df_state = state_map[state]()
            if not df_state.empty:
                # Cap records based on sidebar slider
                df_state = df_state.head(max_per_state)
                for col in TARGET_COLS:
                    if col not in df_state.columns:
                        df_state[col] = "N/A"
                dfs.append(df_state[TARGET_COLS])
                
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame(columns=TARGET_COLS)

# ---------------------------------------------------------
# INTERFACE & CONTROLS
# ---------------------------------------------------------
st.sidebar.title("🛢️ Screener Controls")

selected_states = st.sidebar.multiselect(
    "Select Active States",
    options=["OH", "PA", "NY", "WV", "KY"],
    default=["OH", "PA", "NY", "WV", "KY"]
)

record_limit = st.sidebar.slider(
    "Max Wells Per State",
    min_value=500,
    max_value=10000,
    value=3000,
    step=500,
    help="Higher limits fetch more records but take longer to pull."
)

raw_df = get_aggregated_data(selected_states, record_limit)

if not raw_df.empty:
    raw_df = raw_df.fillna("Unknown")
    
    operators = ["All"] + sorted([str(op) for op in raw_df['Operator'].unique() if op and op != "Unknown"])
    selected_operator = st.sidebar.selectbox("Operator / Owner", operators)
    
    counties = ["All"] + sorted([str(c) for c in raw_df['County'].unique() if c and c != "Unknown"])
    selected_county = st.sidebar.selectbox("County", counties)
    
    filtered_df = raw_df.copy()
    if selected_operator != "All":
        filtered_df = filtered_df[filtered_df['Operator'] == selected_operator]
    if selected_county != "All":
        filtered_df = filtered_df[filtered_df['County'] == selected_county]
else:
    filtered_df = pd.DataFrame(columns=TARGET_COLS)

# Header & Metrics
st.title("Appalachian Basin Oil & Gas Aggregator")
st.caption("Live aggregate data pulling directly from OH, PA, NY, WV, and KY state geological databases")

c1, c2, c3, c4 = st.columns(4)

total_count = len(filtered_df)
active_operators = filtered_df['Operator'].nunique() if total_count > 0 else 0
active_states = filtered_df['State'].nunique() if total_count > 0 else 0
top_operator = filtered_df['Operator'].mode()[0] if total_count > 0 and not filtered_df['Operator'].empty else "N/A"

with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Total Wells Tracked</div><div class="metric-value">{total_count:,}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Active Operators</div><div class="metric-value">{active_operators:,}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">States Represented</div><div class="metric-value">{active_states}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Top Basin Operator</div><div class="metric-value">{str(top_operator)[:15]}...</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if not filtered_df.empty:
    tab1, tab2 = st.tabs(["📊 Basin Running Tally", "📋 Combined Permit Table"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Running Well Tally by State")
            state_tally = filtered_df['State'].value_counts().reset_index()
            state_tally.columns = ['State', 'Well Count']
            fig_state = px.bar(
                state_tally, x='State', y='Well Count', color='State', template="plotly_dark"
            )
            st.plotly_chart(fig_state, use_container_width=True)
            
        with col2:
            st.subheader("Top 10 Operators")
            op_tally = filtered_df['Operator'].value_counts().head(10).reset_index()
            op_tally.columns = ['Operator', 'Well Count']
            fig_op = px.bar(
                op_tally, x='Well Count', y='Operator', orientation='h', template="plotly_dark"
            )
            fig_op.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_op, use_container_width=True)
            
    with tab2:
        st.subheader("Aggregated Well Permit Registry")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
else:
    st.info("Fetching data from state servers...")

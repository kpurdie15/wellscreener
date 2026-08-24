import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Multi-State Oil & Gas Aggregator",
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

# ---------------------------------------------------------
# STATE DATA FETCHERS (Standardized Schema Output)
# Schema: State | Permit_ID | Well_Number | Operator | County | Type | Status
# ---------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_ohio_data():
    """Ohio ODNR Open GIS API"""
    url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Oil_and_Gas_Wells_Locations_of_Ohio/FeatureServer/0/query"
    params = {
        'where': '1=1',
        'outFields': 'PERMIT_NBR,WELL_NUMBER,OWNER_NAME,COUNTY,WELL_TYPE,WELL_STATUS',
        'resultRecordCount': 2000,
        'f': 'json'
    }
    try:
        data = requests.get(url, params=params, timeout=10).json()
        records = [f['attributes'] for f in data.get('features', [])]
        df = pd.DataFrame(records)
        if not df.empty:
            df['State'] = 'OH'
            df = df.rename(columns={
                'PERMIT_NBR': 'Permit_ID',
                'WELL_NUMBER': 'Well_Number',
                'OWNER_NAME': 'Operator',
                'COUNTY': 'County',
                'WELL_TYPE': 'Type',
                'WELL_STATUS': 'Status'
            })
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_pa_data():
    """Pennsylvania DEP GIS API"""
    url = "https://gis.dep.pa.gov/depgisprd/rest/services/OilGas/OilGasAllStrayGas/MapServer/3/query"
    params = {
        'where': '1=1',
        'outFields': 'PERMIT_NUMBER,WELL_NUMBER,OPERATOR_NAME,COUNTY,WELL_TYPE,WELL_STATUS',
        'resultRecordCount': 2000,
        'f': 'json'
    }
    try:
        data = requests.get(url, params=params, timeout=10).json()
        records = [f['attributes'] for f in data.get('features', [])]
        df = pd.DataFrame(records)
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
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_ny_data():
    """New York Open Data Socrata API"""
    url = "https://data.ny.gov/resource/3ub5-233v.json?$limit=2000"
    try:
        res = requests.get(url, timeout=10).json()
        df = pd.DataFrame(res)
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
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_wv_data():
    """West Virginia DEP GIS API"""
    url = "https://services.arcgis.com/jDGuO8tYggdCCnUJ/arcgis/rest/services/W_Virginia_1112018/FeatureServer/1/query"
    params = {
        'where': '1=1',
        'outFields': 'API,WELL_NO,OPERATOR,COUNTY,STATUS',
        'resultRecordCount': 2000,
        'f': 'json'
    }
    try:
        data = requests.get(url, params=params, timeout=10).json()
        records = [f['attributes'] for f in data.get('features', [])]
        df = pd.DataFrame(records)
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
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_ky_data():
    """Kentucky Geological Survey API"""
    url = "https://kgs.uky.edu/arcgis/rest/services/OilGas/KY_OilGas_Wells/MapServer/0/query"
    params = {
        'where': '1=1',
        'outFields': 'PERMIT_NO,WELL_NO,OPERATOR_NAME,COUNTY,WELL_TYPE,STATUS',
        'resultRecordCount': 2000,
        'f': 'json'
    }
    try:
        data = requests.get(url, params=params, timeout=10).json()
        records = [f['attributes'] for f in data.get('features', [])]
        df = pd.DataFrame(records)
        if not df.empty:
            df['State'] = 'KY'
            df = df.rename(columns={
                'PERMIT_NO': 'Permit_ID',
                'WELL_NO': 'Well_Number',
                'OPERATOR_NAME': 'Operator',
                'COUNTY': 'County',
                'WELL_TYPE': 'Type',
                'STATUS': 'Status'
            })
        return df
    except Exception:
        return pd.DataFrame()

# Standard fields requirement
TARGET_COLS = ['State', 'Permit_ID', 'Well_Number', 'Operator', 'County', 'Type', 'Status']

def get_aggregated_data(selected_states):
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
                # Ensure all schema columns exist before concatenating
                for col in TARGET_COLS:
                    if col not in df_state.columns:
                        df_state[col] = "N/A"
                dfs.append(df_state[TARGET_COLS])
                
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame(columns=TARGET_COLS)

# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.title("🛢️ Screener Controls")

selected_states = st.sidebar.multiselect(
    "Select Active States",
    options=["OH", "PA", "NY", "WV", "KY"],
    default=["OH", "PA", "NY", "WV", "KY"]
)

# Fetch consolidated data
raw_df = get_aggregated_data(selected_states)

if not raw_df.empty:
    # Fill NA values for consistent filtering
    raw_df = raw_df.fillna("Unknown")
    
    # Operators Filter
    operators = ["All"] + sorted(list(raw_df['Operator'].unique()))
    selected_operator = st.sidebar.selectbox("Operator / Owner", operators)
    
    # County Filter
    counties = ["All"] + sorted(list(raw_df['County'].unique()))
    selected_county = st.sidebar.selectbox("County", counties)
    
    # Filtering logic
    filtered_df = raw_df.copy()
    if selected_operator != "All":
        filtered_df = filtered_df[filtered_df['Operator'] == selected_operator]
    if selected_county != "All":
        filtered_df = filtered_df[filtered_df['County'] == selected_county]
else:
    filtered_df = pd.DataFrame(columns=TARGET_COLS)

# ---------------------------------------------------------
# DASHBOARD INTERFACE
# ---------------------------------------------------------
st.title("Appalachian Basin Well Aggregator")
st.caption("Live running aggregate across OH, PA, NY, WV, and KY state registers")

# Metric Summary Row
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
    st.markdown(f'<div class="metric-card"><div class="metric-label">Top Basin Operator</div><div class="metric-value">{top_operator[:15]}...</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tally Tabs
if not filtered_df.empty:
    tab1, tab2 = st.tabs(["📊 Basin Running Tally", "📋 Combined Permit Table"])
    
    with tab1:
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            st.subheader("Wells Running Tally by State")
            state_tally = filtered_df['State'].value_counts().reset_index()
            state_tally.columns = ['State', 'Well Count']
            fig_state = px.bar(
                state_tally,
                x='State',
                y='Well Count',
                color='State',
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_state, use_container_width=True)
            
        with row1_col2:
            st.subheader("Top 10 Operators Across Basin")
            op_tally = filtered_df['Operator'].value_counts().head(10).reset_index()
            op_tally.columns = ['Operator', 'Well Count']
            fig_op = px.bar(
                op_tally,
                x='Well Count',
                y='Operator',
                orientation='h',
                template="plotly_dark",
                color_discrete_sequence=["#2563EB"]
            )
            fig_op.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_op, use_container_width=True)
            
    with tab2:
        st.subheader("Aggregated Well Permit Registry")
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )
else:
    st.info("No records loaded. Select states in the sidebar to fetch well registers.")

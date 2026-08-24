import concurrent.futures
import streamlit as st
import pandas as pd
import plotly.express as px
import requests

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

def get_first_valid_col(df, possible_names, default="Unknown"):
    for col in possible_names:
        if col in df.columns:
            return df[col].astype(str)
    return pd.Series([default] * len(df))

def fetch_single_state_data(state_code):
    """Fetches records for a single state with detailed error reporting."""
    if state_code == "NY":
        # New York Open Data Socrata Endpoint
        url = "https://data.ny.gov/resource/3ub5-233v.json?$limit=5000"
        try:
            res = requests.get(url, headers=HEADERS, timeout=12)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)
                    clean_df = pd.DataFrame()
                    clean_df['State'] = ['NY'] * len(df)
                    clean_df['Permit_ID'] = get_first_valid_col(df, ['api_well_number'])
                    clean_df['Well_Number'] = get_first_valid_col(df, ['well_name'])
                    clean_df['Operator'] = get_first_valid_col(df, ['operator_name'])
                    clean_df['County'] = get_first_valid_col(df, ['county'])
                    clean_df['Type'] = get_first_valid_col(df, ['well_type'])
                    clean_df['Status'] = get_first_valid_col(df, ['well_status'])
                    return clean_df, f"Success ({len(clean_df):,} records)"
                return pd.DataFrame(), "API returned 0 records"
            return pd.DataFrame(), f"HTTP Error {res.status_code}"
        except Exception as e:
            return pd.DataFrame(), f"Connection Error: {str(e)[:50]}"

    elif state_code == "OH":
        url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Oil_and_Gas_Wells_Locations_of_Ohio/FeatureServer/0/query"
        params = {'where': '1=1', 'outFields': '*', 'resultRecordCount': 2000, 'f': 'json'}
        try:
            res = requests.get(url, params=params, headers=HEADERS, timeout=12)
            if res.status_code == 200:
                data = res.json()
                features = data.get('features', [])
                if features:
                    df = pd.DataFrame([f['attributes'] for f in features])
                    clean_df = pd.DataFrame()
                    clean_df['State'] = ['OH'] * len(df)
                    clean_df['Permit_ID'] = get_first_valid_col(df, ['PERMIT_NBR', 'API_NUMBER', 'PERMIT'])
                    clean_df['Well_Number'] = get_first_valid_col(df, ['WELL_NUMBER', 'WELL_NUM'])
                    clean_df['Operator'] = get_first_valid_col(df, ['OWNER_NAME', 'OPERATOR'])
                    clean_df['County'] = get_first_valid_col(df, ['COUNTY'])
                    clean_df['Type'] = get_first_valid_col(df, ['WELL_TYPE'])
                    clean_df['Status'] = get_first_valid_col(df, ['WELL_STATUS'])
                    return clean_df, f"Success ({len(clean_df):,} records)"
                return pd.DataFrame(), "No features returned"
            return pd.DataFrame(), f"HTTP Error {res.status_code}"
        except Exception as e:
            return pd.DataFrame(), f"Connection Error: {str(e)[:50]}"

    elif state_code == "PA":
        url = "https://gis.dep.pa.gov/depgisprd/rest/services/OilGas/OilGasAllStrayGas/MapServer/3/query"
        params = {'where': '1=1', 'outFields': '*', 'resultRecordCount': 2000, 'f': 'json'}
        try:
            res = requests.get(url, params=params, headers=HEADERS, timeout=12)
            if res.status_code == 200:
                data = res.json()
                features = data.get('features', [])
                if features:
                    df = pd.DataFrame([f['attributes'] for f in features])
                    clean_df = pd.DataFrame()
                    clean_df['State'] = ['PA'] * len(df)
                    clean_df['Permit_ID'] = get_first_valid_col(df, ['PERMIT_NUMBER', 'AUTH_ID'])
                    clean_df['Well_Number'] = get_first_valid_col(df, ['WELL_NUMBER'])
                    clean_df['Operator'] = get_first_valid_col(df, ['OPERATOR_NAME'])
                    clean_df['County'] = get_first_valid_col(df, ['COUNTY'])
                    clean_df['Type'] = get_first_valid_col(df, ['WELL_TYPE'])
                    clean_df['Status'] = get_first_valid_col(df, ['WELL_STATUS'])
                    return clean_df, f"Success ({len(clean_df):,} records)"
                return pd.DataFrame(), "No features returned"
            return pd.DataFrame(), f"HTTP Error {res.status_code}"
        except Exception as e:
            return pd.DataFrame(), f"Connection Error: {str(e)[:50]}"

    elif state_code == "WV":
        url = "https://services.arcgis.com/jDGuO8tYggdCCnUJ/arcgis/rest/services/W_Virginia_1112018/FeatureServer/1/query"
        params = {'where': '1=1', 'outFields': '*', 'resultRecordCount': 2000, 'f': 'json'}
        try:
            res = requests.get(url, params=params, headers=HEADERS, timeout=12)
            if res.status_code == 200:
                data = res.json()
                features = data.get('features', [])
                if features:
                    df = pd.DataFrame([f['attributes'] for f in features])
                    clean_df = pd.DataFrame()
                    clean_df['State'] = ['WV'] * len(df)
                    clean_df['Permit_ID'] = get_first_valid_col(df, ['API'])
                    clean_df['Well_Number'] = get_first_valid_col(df, ['WELL_NO'])
                    clean_df['Operator'] = get_first_valid_col(df, ['OPERATOR'])
                    clean_df['County'] = get_first_valid_col(df, ['COUNTY'])
                    clean_df['Type'] = pd.Series(['Oil/Gas'] * len(df))
                    clean_df['Status'] = get_first_valid_col(df, ['STATUS'])
                    return clean_df, f"Success ({len(clean_df):,} records)"
                return pd.DataFrame(), "No features returned"
            return pd.DataFrame(), f"HTTP Error {res.status_code}"
        except Exception as e:
            return pd.DataFrame(), f"Connection Error: {str(e)[:50]}"

    return pd.DataFrame(), "Unknown State"

# Cache set to short 60 seconds so changes reflect instantly
@st.cache_data(ttl=60)
def load_data(selected_states):
    dfs = []
    status_log = {}
    for state in selected_states:
        df_state, status_msg = fetch_single_state_data(state)
        status_log[state] = status_msg
        if not df_state.empty:
            dfs.append(df_state)
            
    if dfs:
        return pd.concat(dfs, ignore_index=True).fillna("Unknown"), status_log
    return pd.DataFrame(columns=TARGET_COLS), status_log

# ---------------------------------------------------------
# INTERFACE & DASHBOARD
# ---------------------------------------------------------
st.sidebar.title("🛢️ Screener Controls")

selected_states = st.sidebar.multiselect(
    "Select Active States",
    options=["OH", "PA", "NY", "WV"],
    default=["OH", "PA", "NY", "WV"]
)

# Fetch Data
raw_df, status_log = load_data(selected_states)

# Diagnostic log box in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Live Feed Status")
for state, status in status_log.items():
    badge = "🟢" if "Success" in status else "🔴"
    st.sidebar.write(f"{badge} **{state}:** {status}")

# Sidebar Filters
if not raw_df.empty:
    ops = ["All"] + sorted([x for x in raw_df['Operator'].unique() if x != "Unknown"])
    selected_operator = st.sidebar.selectbox("Operator / Owner", ops)
    
    counties = ["All"] + sorted([x for x in raw_df['County'].unique() if x != "Unknown"])
    selected_county = st.sidebar.selectbox("County", counties)
    
    filtered_df = raw_df.copy()
    if selected_operator != "All":
        filtered_df = filtered_df[filtered_df['Operator'] == selected_operator]
    if selected_county != "All":
        filtered_df = filtered_df[filtered_df['County'] == selected_county]
else:
    filtered_df = raw_df.copy()

# Header Metrics
st.title("Appalachian Basin Oil & Gas Aggregator")
st.caption("Live aggregate data pulling from state geological databases")

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
    st.markdown(f'<div class="metric-card"><div class="metric-label">Top Operator</div><div class="metric-value">{str(top_operator)[:15]}...</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if not filtered_df.empty:
    tab1, tab2 = st.tabs(["📊 Basin Running Tally", "📋 Combined Permit Table"])
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Running Well Tally by State")
            state_tally = filtered_df['State'].value_counts().reset_index()
            state_tally.columns = ['State', 'Well Count']
            fig_state = px.bar(state_tally, x='State', y='Well Count', color='State', template="plotly_dark")
            st.plotly_chart(fig_state, use_container_width=True)
            
        with col2:
            st.subheader("Top 10 Operators")
            op_tally = filtered_df['Operator'].value_counts().head(10).reset_index()
            op_tally.columns = ['Operator', 'Well Count']
            fig_op = px.bar(op_tally, x='Well Count', y='Operator', orientation='h', template="plotly_dark")
            fig_op.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_op, use_container_width=True)
            
    with tab2:
        st.subheader("Aggregated Well Permit Registry")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
else:
    st.error("No data fetched. Check the 'Live Feed Status' section in the left sidebar to see specific state error messages.")

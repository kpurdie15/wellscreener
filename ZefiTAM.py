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

def fetch_arcgis_page(url, offset, batch_size=2000):
    params = {
        'where': '1=1',
        'outFields': '*',
        'resultOffset': offset,
        'resultRecordCount': batch_size,
        'returnGeometry': 'false',
        'f': 'json'
    }
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=10).json()
        return [f['attributes'] for f in res.get('features', [])]
    except Exception:
        return []

def fetch_arcgis_parallel(url, max_records=10000, batch_size=2000):
    offsets = range(0, max_records, batch_size)
    all_records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_arcgis_page, url, offset, batch_size) for offset in offsets]
        for future in concurrent.futures.as_completed(futures):
            all_records.extend(future.result())
    return pd.DataFrame(all_records)

@st.cache_data(ttl=86400) # Cache for 24 hours
def fetch_all_states():
    dfs = []
    
    # Ohio
    try:
        df_oh = fetch_arcgis_parallel("https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Oil_and_Gas_Wells_Locations_of_Ohio/FeatureServer/0/query", 10000)
        if not df_oh.empty:
            cdf = pd.DataFrame()
            cdf['State'] = ['OH'] * len(df_oh)
            cdf['Permit_ID'] = get_first_valid_col(df_oh, ['PERMIT_NBR', 'API_NUMBER', 'PERMIT'])
            cdf['Well_Number'] = get_first_valid_col(df_oh, ['WELL_NUMBER', 'WELL_NUM'])
            cdf['Operator'] = get_first_valid_col(df_oh, ['OWNER_NAME', 'OPERATOR'])
            cdf['County'] = get_first_valid_col(df_oh, ['COUNTY'])
            cdf['Type'] = get_first_valid_col(df_oh, ['WELL_TYPE'])
            cdf['Status'] = get_first_valid_col(df_oh, ['WELL_STATUS'])
            dfs.append(cdf)
    except Exception: pass

    # Pennsylvania
    try:
        df_pa = fetch_arcgis_parallel("https://gis.dep.pa.gov/depgisprd/rest/services/OilGas/OilGasAllStrayGas/MapServer/3/query", 10000)
        if not df_pa.empty:
            cdf = pd.DataFrame()
            cdf['State'] = ['PA'] * len(df_pa)
            cdf['Permit_ID'] = get_first_valid_col(df_pa, ['PERMIT_NUMBER', 'AUTH_ID'])
            cdf['Well_Number'] = get_first_valid_col(df_pa, ['WELL_NUMBER'])
            cdf['Operator'] = get_first_valid_col(df_pa, ['OPERATOR_NAME'])
            cdf['County'] = get_first_valid_col(df_pa, ['COUNTY'])
            cdf['Type'] = get_first_valid_col(df_pa, ['WELL_TYPE'])
            cdf['Status'] = get_first_valid_col(df_pa, ['WELL_STATUS'])
            dfs.append(cdf)
    except Exception: pass

    # New York (Bulk Single Request)
    try:
        res_ny = requests.get("https://data.ny.gov/resource/3ub5-233v.json?$limit=10000", headers=HEADERS, timeout=15).json()
        df_ny = pd.DataFrame(res_ny)
        if not df_ny.empty:
            cdf = pd.DataFrame()
            cdf['State'] = ['NY'] * len(df_ny)
            cdf['Permit_ID'] = get_first_valid_col(df_ny, ['api_well_number'])
            cdf['Well_Number'] = get_first_valid_col(df_ny, ['well_name'])
            cdf['Operator'] = get_first_valid_col(df_ny, ['operator_name'])
            cdf['County'] = get_first_valid_col(df_ny, ['county'])
            cdf['Type'] = get_first_valid_col(df_ny, ['well_type'])
            cdf['Status'] = get_first_valid_col(df_ny, ['well_status'])
            dfs.append(cdf)
    except Exception: pass

    # West Virginia
    try:
        df_wv = fetch_arcgis_parallel("https://services.arcgis.com/jDGuO8tYggdCCnUJ/arcgis/rest/services/W_Virginia_1112018/FeatureServer/1/query", 10000)
        if not df_wv.empty:
            cdf = pd.DataFrame()
            cdf['State'] = ['WV'] * len(df_wv)
            cdf['Permit_ID'] = get_first_valid_col(df_wv, ['API'])
            cdf['Well_Number'] = get_first_valid_col(df_wv, ['WELL_NO'])
            cdf['Operator'] = get_first_valid_col(df_wv, ['OPERATOR'])
            cdf['County'] = get_first_valid_col(df_wv, ['COUNTY'])
            cdf['Type'] = pd.Series(['Oil/Gas'] * len(df_wv))
            cdf['Status'] = get_first_valid_col(df_wv, ['STATUS'])
            dfs.append(cdf)
    except Exception: pass

    if dfs:
        return pd.concat(dfs, ignore_index=True).fillna("Unknown")
    return pd.DataFrame(columns=TARGET_COLS)

raw_df = fetch_all_states()

# ---------------------------------------------------------
# INTERFACE & CONTROLS
# ---------------------------------------------------------
st.sidebar.title("🛢️ Screener Controls")

if not raw_df.empty:
    available_states = sorted(list(raw_df['State'].unique()))
    selected_states = st.sidebar.multiselect(
        "Select Active States",
        options=available_states,
        default=available_states
    )
    
    filtered_by_state = raw_df[raw_df['State'].isin(selected_states)]
    
    ops = ["All"] + sorted([x for x in filtered_by_state['Operator'].unique() if x != "Unknown"])
    selected_operator = st.sidebar.selectbox("Operator / Owner", ops)
    
    counties = ["All"] + sorted([x for x in filtered_by_state['County'].unique() if x != "Unknown"])
    selected_county = st.sidebar.selectbox("County", counties)
    
    filtered_df = filtered_by_state.copy()
    if selected_operator != "All":
        filtered_df = filtered_df[filtered_df['Operator'] == selected_operator]
    if selected_county != "All":
        filtered_df = filtered_df[filtered_df['County'] == selected_county]
else:
    filtered_df = raw_df.copy()

st.title("Appalachian Basin Oil & Gas Aggregator")
st.caption("Live aggregate data pulling up to 10,000 wells per state in parallel")

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
            st.subheader("Top 10 Operators Across Selected Data")
            op_tally = filtered_df['Operator'].value_counts().head(10).reset_index()
            op_tally.columns = ['Operator', 'Well Count']
            fig_op = px.bar(op_tally, x='Well Count', y='Operator', orientation='h', template="plotly_dark")
            fig_op.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_op, use_container_width=True)
            
    with tab2:
        st.subheader("Aggregated Well Permit Registry")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

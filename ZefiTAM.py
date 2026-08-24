import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# ---------------------------------------------------------
# PAGE CONFIGURATION & STYLING
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

TARGET_COLS = ['State', 'Permit_ID', 'Well_Number', 'Operator', 'County', 'Type', 'Status', 'Status_Category']

def get_first_valid_col(df, possible_names, default="Unknown"):
    for col in possible_names:
        if col in df.columns:
            return df[col].astype(str)
    return pd.Series([default] * len(df))

def categorize_status(val):
    """Categorizes varied state status codes into clean buckets."""
    s = str(val).upper()
    if any(k in s for k in ['PLUG', 'P&A', 'ABANDON', 'INACTIVE', 'CANCEL']):
        return 'Plugged / Abandoned'
    elif any(k in s for k in ['ACTIVE', 'PRODUC', 'DRILL', 'OPERAT', 'IN SERVICE', 'PROD']):
        return 'Active'
    elif any(k in s for k in ['PERMIT', 'ISSUED', 'LOCATION', 'APPROVED']):
        return 'Permitted / Undrilled'
    return 'Other / Unknown'

def fetch_arcgis_paginated(url, max_records=5000, batch_size=1000, extra_params=None):
    """Utility to pull past the 1,000 record server-side pagination limit."""
    all_records = []
    offset = 0
    while offset < max_records:
        params = {
            'where': '1=1',
            'outFields': '*',
            'resultOffset': offset,
            'resultRecordCount': batch_size,
            'returnGeometry': 'false',
            'f': 'json'
        }
        if extra_params:
            params.update(extra_params)
            
        try:
            res = requests.get(url, params=params, headers=HEADERS, timeout=12)
            if res.status_code != 200:
                break
            features = res.json().get('features', [])
            if not features:
                break
            all_records.extend([f['attributes'] for f in features])
            if len(features) < batch_size:
                break
            offset += batch_size
        except Exception:
            break
            
    return pd.DataFrame(all_records)

# ---------------------------------------------------------
# STATE DATA FETCHERS
# ---------------------------------------------------------
def fetch_single_state_data(state_code, max_limit=5000):
    
    if state_code == "NY":
        # Working NYS DEC Socrata Endpoint
        url = f"https://data.ny.gov/resource/3ub5-233v.json?$limit={max_limit}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)
                    clean_df = pd.DataFrame()
                    clean_df['State'] = ['NY'] * len(df)
                    clean_df['Permit_ID'] = get_first_valid_col(df, ['api_well_number', 'api'])
                    clean_df['Well_Number'] = get_first_valid_col(df, ['well_name', 'well_number'])
                    clean_df['Operator'] = get_first_valid_col(df, ['operator_name', 'operator'])
                    clean_df['County'] = get_first_valid_col(df, ['county'])
                    clean_df['Type'] = get_first_valid_col(df, ['well_type'])
                    clean_df['Status'] = get_first_valid_col(df, ['well_status'])
                    clean_df['Status_Category'] = clean_df['Status'].apply(categorize_status)
                    return clean_df, f"Success ({len(clean_df):,} records)"
                return pd.DataFrame(), "API returned 0 records"
            return pd.DataFrame(), f"HTTP Error {res.status_code}"
        except Exception as e:
            return pd.DataFrame(), f"Error: {str(e)[:40]}"

    elif state_code == "OH":
        # Ohio ODNR with spatial bounding envelope
        url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Oil_and_Gas_Wells_Locations_of_Ohio/FeatureServer/0/query"
        oh_extra = {
            'geometry': '-84.8,38.4,-80.5,42.0',
            'geometryType': 'esriGeometryEnvelope',
            'spatialRel': 'esriSpatialRelIntersects'
        }
        try:
            df = fetch_arcgis_paginated(url, max_records=max_limit, extra_params=oh_extra)
            if not df.empty:
                clean_df = pd.DataFrame()
                clean_df['State'] = ['OH'] * len(df)
                clean_df['Permit_ID'] = get_first_valid_col(df, ['PERMIT_NBR', 'API_NUMBER', 'PERMIT'])
                clean_df['Well_Number'] = get_first_valid_col(df, ['WELL_NUMBER', 'WELL_NO'])
                clean_df['Operator'] = get_first_valid_col(df, ['OWNER_NAME', 'OPERATOR'])
                clean_df['County'] = get_first_valid_col(df, ['COUNTY'])
                clean_df['Type'] = get_first_valid_col(df, ['WELL_TYPE'])
                clean_df['Status'] = get_first_valid_col(df, ['WELL_STATUS'])
                clean_df['Status_Category'] = clean_df['Status'].apply(categorize_status)
                return clean_df, f"Success ({len(clean_df):,} records)"
            return pd.DataFrame(), "No features returned"
        except Exception as e:
            return pd.DataFrame(), f"Error: {str(e)[:40]}"

    elif state_code == "PA":
        url = "https://gis.dep.pa.gov/depgisprd/rest/services/OilGas/OilGasAllStrayGas/MapServer/3/query"
        try:
            df = fetch_arcgis_paginated(url, max_records=max_limit)
            if not df.empty:
                clean_df = pd.DataFrame()
                clean_df['State'] = ['PA'] * len(df)
                clean_df['Permit_ID'] = get_first_valid_col(df, ['PERMIT_NUMBER', 'AUTH_ID'])
                clean_df['Well_Number'] = get_first_valid_col(df, ['WELL_NUMBER'])
                clean_df['Operator'] = get_first_valid_col(df, ['OPERATOR_NAME'])
                clean_df['County'] = get_first_valid_col(df, ['COUNTY'])
                clean_df['Type'] = get_first_valid_col(df, ['WELL_TYPE'])
                clean_df['Status'] = get_first_valid_col(df, ['WELL_STATUS'])
                clean_df['Status_Category'] = clean_df['Status'].apply(categorize_status)
                return clean_df, f"Success ({len(clean_df):,} records)"
            return pd.DataFrame(), "No features returned"
        except Exception as e:
            return pd.DataFrame(), f"Error: {str(e)[:40]}"

    elif state_code == "WV":
        url = "https://services.arcgis.com/jDGuO8tYggdCCnUJ/arcgis/rest/services/W_Virginia_1112018/FeatureServer/1/query"
        try:
            df = fetch_arcgis_paginated(url, max_records=max_limit)
            if not df.empty:
                clean_df = pd.DataFrame()
                clean_df['State'] = ['WV'] * len(df)
                clean_df['Permit_ID'] = get_first_valid_col(df, ['API'])
                clean_df['Well_Number'] = get_first_valid_col(df, ['WELL_NO'])
                clean_df['Operator'] = get_first_valid_col(df, ['OPERATOR'])
                clean_df['County'] = get_first_valid_col(df, ['COUNTY'])
                clean_df['Type'] = pd.Series(['Oil/Gas'] * len(df))
                clean_df['Status'] = get_first_valid_col(df, ['STATUS'])
                clean_df['Status_Category'] = clean_df['Status'].apply(categorize_status)
                return clean_df, f"Success ({len(clean_df):,} records)"
            return pd.DataFrame(), "No features returned"
        except Exception as e:
            return pd.DataFrame(), f"Error: {str(e)[:40]}"

    return pd.DataFrame(), "Unknown State"

@st.cache_data(ttl=600)
def load_data(selected_states, max_limit):
    dfs = []
    status_log = {}
    for state in selected_states:
        df_state, status_msg = fetch_single_state_data(state, max_limit)
        status_log[state] = status_msg
        if not df_state.empty:
            dfs.append(df_state)
            
    if dfs:
        return pd.concat(dfs, ignore_index=True).fillna("Unknown"), status_log
    return pd.DataFrame(columns=TARGET_COLS), status_log

# ---------------------------------------------------------
# INTERFACE & CONTROLS
# ---------------------------------------------------------
st.sidebar.title("🛢️ Screener Controls")

selected_states = st.sidebar.multiselect(
    "Select Active States",
    options=["OH", "PA", "NY", "WV"],
    default=["OH", "PA", "NY", "WV"]
)

max_wells_slider = st.sidebar.slider(
    "Max Fetch Limit per State",
    min_value=1000,
    max_value=10000,
    value=3000,
    step=1000
)

raw_df, status_log = load_data(selected_states, max_wells_slider)

# Live Feed Status Box
st.sidebar.markdown("---")
st.sidebar.subheader("Live Feed Status")
for state, status in status_log.items():
    badge = "🟢" if "Success" in status else "🔴"
    st.sidebar.write(f"{badge} **{state}:** {status}")

# Filters
if not raw_df.empty:
    status_options = ["All"] + sorted(list(raw_df['Status_Category'].unique()))
    selected_status = st.sidebar.selectbox("Well Status Category", status_options)

    ops = ["All"] + sorted([x for x in raw_df['Operator'].unique() if x != "Unknown"])
    selected_operator = st.sidebar.selectbox("Operator / Owner", ops)
    
    counties = ["All"] + sorted([x for x in raw_df['County'].unique() if x != "Unknown"])
    selected_county = st.sidebar.selectbox("County", counties)
    
    filtered_df = raw_df.copy()
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df['Status_Category'] == selected_status]
    if selected_operator != "All":
        filtered_df = filtered_df[filtered_df['Operator'] == selected_operator]
    if selected_county != "All":
        filtered_df = filtered_df[filtered_df['County'] == selected_county]
else:
    filtered_df = raw_df.copy()

# Header Metrics
st.title("Appalachian Basin Oil & Gas Aggregator")
st.caption("Live aggregate registry disaggregating active vs. plugged well infrastructure")

c1, c2, c3, c4 = st.columns(4)
total_count = len(filtered_df)
active_wells = len(filtered_df[filtered_df['Status_Category'] == 'Active']) if total_count > 0 else 0
plugged_wells = len(filtered_df[filtered_df['Status_Category'] == 'Plugged / Abandoned']) if total_count > 0 else 0
active_operators = filtered_df['Operator'].nunique() if total_count > 0 else 0

with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Total Filtered Wells</div><div class="metric-value">{total_count:,}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Active Wells</div><div class="metric-value" style="color: #4ADE80;">{active_wells:,}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Plugged / Abandoned</div><div class="metric-value" style="color: #F87171;">{plugged_wells:,}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Active Operators</div><div class="metric-value">{active_operators:,}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Dashboard Charts & Analytics
if not filtered_df.empty:
    tab1, tab2 = st.tabs(["📊 Basin Analytics & Status Breakdown", "📋 Permit Registry Table"])
    
    with tab1:
        r1_col1, r1_col2 = st.columns(2)
        
        with r1_col1:
            st.subheader("Active vs Plugged Wells by State")
            status_by_state = filtered_df.groupby(['State', 'Status_Category']).size().reset_index(name='Count')
            fig_status_state = px.bar(
                status_by_state,
                x='State',
                y='Count',
                color='Status_Category',
                barmode='stack',
                template="plotly_dark",
                color_discrete_map={
                    'Active': '#22C55E',
                    'Plugged / Abandoned': '#EF4444',
                    'Permitted / Undrilled': '#3B82F6',
                    'Other / Unknown': '#6B7280'
                }
            )
            st.plotly_chart(fig_status_state, use_container_width=True)
            
        with r1_col2:
            st.subheader("Overall Status Distribution")
            status_pie = filtered_df['Status_Category'].value_counts().reset_index()
            status_pie.columns = ['Status', 'Count']
            fig_pie = px.pie(
                status_pie,
                names='Status',
                values='Count',
                hole=0.4,
                template="plotly_dark",
                color='Status',
                color_discrete_map={
                    'Active': '#22C55E',
                    'Plugged / Abandoned': '#EF4444',
                    'Permitted / Undrilled': '#3B82F6',
                    'Other / Unknown': '#6B7280'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        r2_col1, r2_col2 = st.columns(2)
        with r2_col1:
            st.subheader("Top Operators (Filtered Set)")
            op_tally = filtered_df['Operator'].value_counts().head(10).reset_index()
            op_tally.columns = ['Operator', 'Well Count']
            fig_op = px.bar(op_tally, x='Well Count', y='Operator', orientation='h', template="plotly_dark")
            fig_op.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_op, use_container_width=True)

        with r2_col2:
            st.subheader("Top Counties by Well Count")
            county_tally = filtered_df['County'].value_counts().head(10).reset_index()
            county_tally.columns = ['County', 'Well Count']
            fig_county = px.bar(county_tally, x='County', y='Well Count', template="plotly_dark", color_discrete_sequence=['#6366F1'])
            st.plotly_chart(fig_county, use_container_width=True)

    with tab2:
        st.subheader("Aggregated Permit Explorer")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
else:
    st.error("No records found matching current sidebar filter criteria.")

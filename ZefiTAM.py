import io
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

TARGET_COLS = ['State', 'Permit_ID', 'Well_Number', 'Operator', 'County', 'Type', 'Status', 'Status_Category']

def get_first_valid_col(df, possible_names, default="Unknown"):
    for col in possible_names:
        if col in df.columns:
            return df[col].astype(str)
    return pd.Series([default] * len(df))

def categorize_status(val):
    s = str(val).upper()
    if any(k in s for k in ['PLUG', 'P&A', 'ABANDON', 'INACTIVE', 'CANCEL', 'DRY']):
        return 'Plugged / Abandoned'
    elif any(k in s for k in ['ACTIVE', 'PRODUC', 'DRILL', 'OPERAT', 'IN SERVICE', 'PROD', 'COMPLETED']):
        return 'Active'
    elif any(k in s for k in ['PERMIT', 'ISSUED', 'LOCATION', 'APPROVED']):
        return 'Permitted / Undrilled'
    return 'Other / Unknown'

def fetch_arcgis_paginated(url, max_records=5000, batch_size=1000):
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
# STATE FETCHERS
# ---------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_all_states_data(max_per_state):
    dfs = []
    status_log = {}

    # 1. PENNSYLVANIA (PA DEP)
    try:
        pa_url = "https://gis.dep.pa.gov/depgisprd/rest/services/OilGas/OilGasAllStrayGas/MapServer/3/query"
        pa_df = fetch_arcgis_paginated(pa_url, max_records=max_per_state)
        if not pa_df.empty:
            clean_pa = pd.DataFrame()
            clean_pa['State'] = ['PA'] * len(pa_df)
            clean_pa['Permit_ID'] = get_first_valid_col(pa_df, ['PERMIT_NUMBER', 'AUTH_ID'])
            clean_pa['Well_Number'] = get_first_valid_col(pa_df, ['WELL_NUMBER'])
            clean_pa['Operator'] = get_first_valid_col(pa_df, ['OPERATOR_NAME'])
            clean_pa['County'] = get_first_valid_col(pa_df, ['COUNTY'])
            clean_pa['Type'] = get_first_valid_col(pa_df, ['WELL_TYPE'])
            clean_pa['Status'] = get_first_valid_col(pa_df, ['WELL_STATUS'])
            clean_pa['Status_Category'] = clean_pa['Status'].apply(categorize_status)
            dfs.append(clean_pa)
            status_log['PA'] = f"Success ({len(clean_pa):,} records)"
        else:
            status_log['PA'] = "No records returned"
    except Exception as e:
        status_log['PA'] = f"Error: {str(e)[:30]}"

    # 2. WEST VIRGINIA (WV DEP)
    try:
        wv_url = "https://services.arcgis.com/jDGuO8tYggdCCnUJ/arcgis/rest/services/W_Virginia_1112018/FeatureServer/1/query"
        wv_df = fetch_arcgis_paginated(wv_url, max_records=max_per_state)
        if not wv_df.empty:
            clean_wv = pd.DataFrame()
            clean_wv['State'] = ['WV'] * len(wv_df)
            clean_wv['Permit_ID'] = get_first_valid_col(wv_df, ['API'])
            clean_wv['Well_Number'] = get_first_valid_col(wv_df, ['WELL_NO'])
            clean_wv['Operator'] = get_first_valid_col(wv_df, ['OPERATOR'])
            clean_wv['County'] = get_first_valid_col(wv_df, ['COUNTY'])
            clean_wv['Type'] = pd.Series(['Oil/Gas'] * len(wv_df))
            clean_wv['Status'] = get_first_valid_col(wv_df, ['STATUS'])
            clean_wv['Status_Category'] = clean_wv['Status'].apply(categorize_status)
            dfs.append(clean_wv)
            status_log['WV'] = f"Success ({len(clean_wv):,} records)"
        else:
            status_log['WV'] = "No records returned"
    except Exception as e:
        status_log['WV'] = f"Error: {str(e)[:30]}"

    # 3. OHIO (ODNR Open GIS FeatureServer)
    try:
        oh_url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Oil_and_Gas_Wells_Locations_of_Ohio/FeatureServer/0/query"
        oh_df = fetch_arcgis_paginated(oh_url, max_records=max_per_state)
        if not oh_df.empty:
            clean_oh = pd.DataFrame()
            clean_oh['State'] = ['OH'] * len(oh_df)
            clean_oh['Permit_ID'] = get_first_valid_col(oh_df, ['PERMIT_NBR', 'API_NUMBER'])
            clean_oh['Well_Number'] = get_first_valid_col(oh_df, ['WELL_NUMBER'])
            clean_oh['Operator'] = get_first_valid_col(oh_df, ['OWNER_NAME', 'OPERATOR'])
            clean_oh['County'] = get_first_valid_col(oh_df, ['COUNTY'])
            clean_oh['Type'] = get_first_valid_col(oh_df, ['WELL_TYPE'])
            clean_oh['Status'] = get_first_valid_col(oh_df, ['WELL_STATUS'])
            clean_oh['Status_Category'] = clean_oh['Status'].apply(categorize_status)
            dfs.append(clean_oh)
            status_log['OH'] = f"Success ({len(clean_oh):,} records)"
        else:
            status_log['OH'] = "No records returned"
    except Exception as e:
        status_log['OH'] = f"Error: {str(e)[:30]}"

    # 4. NEW YORK (DEC Socrata JSON Endpoint)
    try:
        ny_url = f"https://data.ny.gov/resource/3ub5-233v.json?$limit={max_per_state}"
        res = requests.get(ny_url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                ny_df = pd.DataFrame(data)
                clean_ny = pd.DataFrame()
                clean_ny['State'] = ['NY'] * len(ny_df)
                clean_ny['Permit_ID'] = get_first_valid_col(ny_df, ['api_well_number'])
                clean_ny['Well_Number'] = get_first_valid_col(ny_df, ['well_name'])
                clean_ny['Operator'] = get_first_valid_col(ny_df, ['operator_name'])
                clean_ny['County'] = get_first_valid_col(ny_df, ['county'])
                clean_ny['Type'] = get_first_valid_col(ny_df, ['well_type'])
                clean_ny['Status'] = get_first_valid_col(ny_df, ['well_status'])
                clean_ny['Status_Category'] = clean_ny['Status'].apply(categorize_status)
                dfs.append(clean_ny)
                status_log['NY'] = f"Success ({len(clean_ny):,} records)"
            else:
                status_log['NY'] = "Empty payload"
        else:
            status_log['NY'] = f"HTTP Error {res.status_code}"
    except Exception as e:
        status_log['NY'] = f"Error: {str(e)[:30]}"

    if dfs:
        return pd.concat(dfs, ignore_index=True).fillna("Unknown"), status_log
    return pd.DataFrame(columns=TARGET_COLS), status_log

# ---------------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------------
st.sidebar.title("🛢️ Screener Controls")

max_limit = st.sidebar.slider(
    "Records Per State Limit",
    min_value=1000,
    max_value=10000,
    value=5000,
    step=1000
)

raw_df, status_log = fetch_all_states_data(max_limit)

st.sidebar.markdown("---")
st.sidebar.subheader("Live Feed Status")
for st_code in ["PA", "WV", "OH", "NY"]:
    msg = status_log.get(st_code, "Not Loaded")
    badge = "🟢" if "Success" in msg else "🔴"
    st.sidebar.write(f"{badge} **{st_code}:** {msg}")

if not raw_df.empty:
    states_available = sorted(list(raw_df['State'].unique()))
    selected_states = st.sidebar.multiselect("Active States", states_available, default=states_available)
    filtered_df = raw_df[raw_df['State'].isin(selected_states)]

    status_options = ["All"] + sorted(list(filtered_df['Status_Category'].unique()))
    selected_status = st.sidebar.selectbox("Well Status Category", status_options)

    ops = ["All"] + sorted([x for x in filtered_df['Operator'].unique() if x != "Unknown"])
    selected_operator = st.sidebar.selectbox("Operator / Owner", ops)

    counties = ["All"] + sorted([x for x in filtered_df['County'].unique() if x != "Unknown"])
    selected_county = st.sidebar.selectbox("County", counties)

    if selected_status != "All":
        filtered_df = filtered_df[filtered_df['Status_Category'] == selected_status]
    if selected_operator != "All":
        filtered_df = filtered_df[filtered_df['Operator'] == selected_operator]
    if selected_county != "All":
        filtered_df = filtered_df[filtered_df['County'] == selected_county]
else:
    filtered_df = raw_df.copy()

# ---------------------------------------------------------
# DASHBOARD INTERFACE
# ---------------------------------------------------------
st.title("Appalachian Basin Oil & Gas Aggregator")
st.caption("Aggregated registry disaggregating active vs. plugged well infrastructure")

c1, c2, c3, c4 = st.columns(4)
total_count = len(filtered_df)
active_wells = len(filtered_df[filtered_df['Status_Category'] == 'Active']) if total_count > 0 else 0
plugged_wells = len(filtered_df[filtered_df['Status_Category'] == 'Plugged / Abandoned']) if total_count > 0 else 0
active_operators = filtered_df['Operator'].nunique() if total_count > 0 else 0

with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Total Tracked Wells</div><div class="metric-value">{total_count:,}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Active Wells</div><div class="metric-value" style="color: #4ADE80;">{active_wells:,}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Plugged / Abandoned</div><div class="metric-value" style="color: #F87171;">{plugged_wells:,}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Active Operators</div><div class="metric-value">{active_operators:,}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if not filtered_df.empty:
    tab1, tab2 = st.tabs(["📊 Active vs Plugged Analytics", "📋 Well Permit Registry"])

    with tab1:
        r1_col1, r1_col2 = st.columns(2)
        with r1_col1:
            st.subheader("Active vs Plugged Wells by State")
            status_by_state = filtered_df.groupby(['State', 'Status_Category']).size().reset_index(name='Count')
            fig_status = px.bar(
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
            st.plotly_chart(fig_status, use_container_width=True)

        with r1_col2:
            st.subheader("Status Category Breakdown")
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
            st.subheader("Top 10 Operators")
            op_tally = filtered_df['Operator'].value_counts().head(10).reset_index()
            op_tally.columns = ['Operator', 'Well Count']
            fig_op = px.bar(op_tally, x='Well Count', y='Operator', orientation='h', template="plotly_dark")
            fig_op.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_op, use_container_width=True)

        with r2_col2:
            st.subheader("Top 10 Counties")
            county_tally = filtered_df['County'].value_counts().head(10).reset_index()
            county_tally.columns = ['County', 'Well Count']
            fig_county = px.bar(county_tally, x='County', y='Well Count', template="plotly_dark", color_discrete_sequence=['#6366F1'])
            st.plotly_chart(fig_county, use_container_width=True)

    with tab2:
        st.subheader("Aggregated Well Registry Data")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

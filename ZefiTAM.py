import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Appalachian Basin Oil & Gas Screener",
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

@st.cache_data(ttl=86400)
def load_master_dataset():
    # Fallback loader in case parquet hasn't compiled yet locally
    if os.path.exists("wells_master.parquet"):
        return pd.read_parquet("wells_master.parquet")
    return pd.DataFrame(columns=['State', 'Permit_ID', 'Well_Number', 'Operator', 'County', 'Type', 'Status', 'Status_Category'])

raw_df = load_master_dataset()

# ---------------------------------------------------------
# INTERFACE & DASHBOARD CONTROLS
# ---------------------------------------------------------
st.sidebar.title("🛢️ Screener Controls")

if not raw_df.empty:
    states_available = sorted(list(raw_df['State'].unique()))
    selected_states = st.sidebar.multiselect("Active States", states_available, default=states_available)
    
    filtered_df = raw_df[raw_df['State'].isin(selected_states)]

    status_options = ["All"] + sorted(list(filtered_df['Status_Category'].unique()))
    selected_status = st.sidebar.selectbox("Well Status Category", status_options)

    ops = ["All"] + sorted([x for x in filtered_df['Operator'].unique() if x != "Unknown Operator"])
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

# Header Metrics
st.title("Appalachian Basin Oil & Gas Aggregator")
st.caption("Master verified state database tracking active vs. plugged well infrastructure")

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

# Visual Dashboards
if not filtered_df.empty:
    tab1, tab2 = st.tabs(["📊 Active vs Plugged Analytics", "📋 Well Permit Registry Explorer"])

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
            st.subheader("Top 10 Active Counties")
            county_tally = filtered_df['County'].value_counts().head(10).reset_index()
            county_tally.columns = ['County', 'Well Count']
            fig_county = px.bar(county_tally, x='County', y='Well Count', template="plotly_dark", color_discrete_sequence=['#6366F1'])
            st.plotly_chart(fig_county, use_container_width=True)

    with tab2:
        st.subheader("Aggregated Well Registry Data")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
else:
    st.warning("Database build in progress. Run build_database.py to generate wells_master.parquet.")

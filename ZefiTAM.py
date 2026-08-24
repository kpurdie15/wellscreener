import os
import streamlit as st
import pandas as pd
import plotly.express as px

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

@st.cache_data(ttl=3600)
def load_cached_data():
    file_path = "wells_data.parquet"
    if os.path.exists(file_path):
        return pd.read_parquet(file_path)
    return pd.DataFrame(columns=['State', 'Permit_ID', 'Well_Number', 'Operator', 'County', 'Type', 'Status'])

raw_df = load_cached_data()

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

# Header & Metrics
st.title("Appalachian Basin Oil & Gas Aggregator")
st.caption("Daily synchronized registry across OH, PA, NY, WV, and KY state databases")

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
else:
    st.warning("Data sync in progress. Trigger the GitHub action or wait for the initial daily run.")

import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import io

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Clinical Trial Safety Monitor",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# SNOWFLAKE CONFIGURATION (CLOUD + LOCAL)
# ============================================

# Try to get config from Streamlit secrets (cloud) OR fallback to local
try:
    # For Streamlit Cloud deployment
    SNOWFLAKE_CONFIG = {
        "account": st.secrets["SNOWFLAKE_ACCOUNT"],
        "user": st.secrets["SNOWFLAKE_USER"],
        "password": st.secrets["SNOWFLAKE_PASSWORD"],
        "warehouse": st.secrets["SNOWFLAKE_WAREHOUSE"],
        "database": st.secrets["SNOWFLAKE_DATABASE"],
        "schema_raw": st.secrets["SNOWFLAKE_SCHEMA"]
    }
    st.success("✅ Connected to Snowflake via Cloud Secrets")
except Exception as e:
    # For local development (fallback to config file)
    try:
        from snowflake_config import SNOWFLAKE_CONFIG as local_config
        SNOWFLAKE_CONFIG = local_config
        st.success("✅ Connected to Snowflake via Local Config")
    except Exception as e:
        st.error("❌ No Snowflake configuration found. Please set up secrets or snowflake_config.py")
        st.stop()

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4A627A;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("## 🩺 Safety Monitor")
    st.markdown("---")
    
    st.markdown("### 📊 Data Source")
    data_source = st.radio(
        "Select data source",
        ["Snowflake Database", "Local CSV File"],
        help="Snowflake contains the full 2,598 adverse events from ClinicalTrials.gov"
    )
    
    st.markdown("---")
    st.markdown("### 🔍 Filters")
    
    trial_filter_placeholder = st.empty()
    
    seriousness_filter = st.selectbox(
        "Adverse Event Severity",
        ["All Events", "Serious Only", "Non-Serious Only"]
    )
    
    st.markdown("---")
    st.caption(f"🩺 Clinical Trial Safety Monitor v3.0\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ============================================
# MAIN HEADER
# ============================================
st.markdown('<p class="main-header">🩺 Clinical Trial Adverse Event Safety Monitor</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Real-time pharmacovigilance platform for cancer clinical trials | Powered by ClinicalTrials.gov API + Snowflake</p>', unsafe_allow_html=True)

# ============================================
# DATA LOADING FUNCTIONS
# ============================================

@st.cache_data(ttl=3600)
def load_data_from_snowflake():
    """Load data from Snowflake"""
    try:
        conn = snowflake.connector.connect(
            account=SNOWFLAKE_CONFIG["account"],
            user=SNOWFLAKE_CONFIG["user"],
            password=SNOWFLAKE_CONFIG["password"],
            warehouse=SNOWFLAKE_CONFIG["warehouse"],
            database=SNOWFLAKE_CONFIG["database"],
            schema=SNOWFLAKE_CONFIG["schema_raw"]
        )
        
        query = """
            SELECT 
                TRIAL_ID,
                AE_TERM,
                AE_TYPE,
                ORGAN_SYSTEM,
                EVENT_COUNT,
                SOURCE_SYSTEM,
                REPORT_DATE
            FROM ADVERSE_EVENTS 
            ORDER BY REPORT_DATE DESC
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Rename columns for consistency
        df.rename(columns={
            'TRIAL_ID': 'trial_id',
            'AE_TERM': 'ae_term',
            'AE_TYPE': 'ae_type',
            'ORGAN_SYSTEM': 'organ_system',
            'EVENT_COUNT': 'count',
            'SOURCE_SYSTEM': 'source_system',
            'REPORT_DATE': 'report_date'
        }, inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Snowflake connection error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_data_from_csv():
    """Load data from local CSV file"""
    try:
        df = pd.read_csv('fetched_ae_data.csv')
        return df
    except Exception as e:
        st.error(f"CSV load error: {e}")
        return pd.DataFrame()

# ============================================
# LOAD DATA
# ============================================
if data_source == "Snowflake Database":
    df = load_data_from_snowflake()
    if df.empty:
        st.warning("⚠️ No data in Snowflake. Please run load_to_snowflake_final.py first, or switch to 'Local CSV File'.")
        st.stop()
else:
    df = load_data_from_csv()
    if df.empty:
        st.warning("⚠️ No CSV data found. Please run fetch_ae_data.py first.")
        st.stop()

# ============================================
# APPLY FILTERS
# ============================================
if not df.empty:
    # Trial filter
    available_trials = df['trial_id'].unique().tolist()
    selected_trials = trial_filter_placeholder.multiselect(
        "Select Trials to Analyze",
        options=available_trials,
        default=available_trials[:min(4, len(available_trials))]
    )
    
    if selected_trials:
        df = df[df['trial_id'].isin(selected_trials)]
    
    # Seriousness filter
    if seriousness_filter == "Serious Only":
        df = df[df['ae_type'].astype(str).str.contains('Serious', case=False, na=False)]
    elif seriousness_filter == "Non-Serious Only":
        df = df[~df['ae_type'].astype(str).str.contains('Serious', case=False, na=False)]

# ============================================
# METRICS ROW
# ============================================
if not df.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; font-size:0.9rem;">Total AEs</h3>
            <p style="margin:0; font-size:2rem; font-weight:bold;">{len(df):,}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        serious_count = len(df[df['ae_type'].astype(str).str.contains('Serious', case=False, na=False)])
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h3 style="margin:0; font-size:0.9rem;">Serious AEs</h3>
            <p style="margin:0; font-size:2rem; font-weight:bold;">{serious_count:,}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        unique_trials = df['trial_id'].nunique()
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h3 style="margin:0; font-size:0.9rem;">Active Trials</h3>
            <p style="margin:0; font-size:2rem; font-weight:bold;">{unique_trials}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <h3 style="margin:0; font-size:0.9rem;">Data Source</h3>
            <p style="margin:0; font-size:1rem; font-weight:bold;">ClinicalTrials.gov</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

# ============================================
# TABBED INTERFACE
# ============================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", 
    "🔬 Signal Detection", 
    "📈 Trial Comparison",
    "📋 Data Explorer",
    "📄 Safety Report"
])

# ============================================
# TAB 1: DASHBOARD
# ============================================
with tab1:
    if not df.empty:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("📊 Top 15 Adverse Events")
            top_ae = df['ae_term'].value_counts().head(15)
            fig = px.bar(
                x=top_ae.values,
                y=top_ae.index,
                orientation='h',
                labels={'x': 'Number of Reports', 'y': 'Adverse Event Term'},
                color=top_ae.values,
                color_continuous_scale='Viridis',
                height=500
            )
            fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("⚠️ Serious vs Non-Serious")
            serious_counts = df['ae_type'].astype(str).apply(
                lambda x: 'Serious' if 'Serious' in x else 'Non-Serious'
            ).value_counts()
            fig2 = px.pie(
                values=serious_counts.values,
                names=serious_counts.index,
                title="Proportion of Serious Events",
                color_discrete_sequence=['#ff6b6b', '#4ecdc4'],
                hole=0.4
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
            
            st.markdown("---")
            st.subheader("🏥 Event Type Distribution")
            event_types = df['ae_type'].value_counts().head(5)
            fig3 = px.bar(
                x=event_types.index,
                y=event_types.values,
                labels={'x': 'Event Type', 'y': 'Count'},
                color=event_types.values,
                color_continuous_scale='Teal'
            )
            fig3.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No data available. Please check your filters or data source.")

# ============================================
# TAB 2: SIGNAL DETECTION
# ============================================
with tab2:
    st.subheader("🔬 Statistical Signal Detection")
    st.markdown("Disproportionality analysis for adverse event signal detection")
    
    if not df.empty:
        ae_counts = df['ae_term'].value_counts()
        total_events = len(df)
        expected_rate = total_events / len(ae_counts) if len(ae_counts) > 0 else 1
        
        signal_df = pd.DataFrame({
            'AE_Term': ae_counts.index,
            'Observed_Count': ae_counts.values,
            'Expected_Rate': round(expected_rate, 2),
            'Reporting_Ratio': round(ae_counts.values / expected_rate, 2)
        })
        
        signal_df['Signal'] = signal_df['Reporting_Ratio'] > 2
        signal_df['Alert_Level'] = np.where(
            signal_df['Reporting_Ratio'] > 5, '🔴 High',
            np.where(signal_df['Reporting_Ratio'] > 2, '🟡 Medium', '🟢 Low')
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Signal Detection Results")
            signals_to_show = signal_df[signal_df['Signal']].head(20)
            if not signals_to_show.empty:
                st.dataframe(signals_to_show, use_container_width=True)
            else:
                st.success("✅ No unusual safety signals detected")
        
        with col2:
            st.markdown("### 📈 Signal Volcano Plot")
            fig = px.scatter(
                signal_df,
                x=np.log1p(signal_df['Observed_Count']),
                y=np.log1p(signal_df['Reporting_Ratio']),
                color=signal_df['Alert_Level'],
                hover_data=['AE_Term'],
                title="Signal Detection Plot",
                labels={'x': 'Log(Observed Count)', 'y': 'Log(Reporting Ratio)'},
                color_discrete_map={'🔴 High': 'red', '🟡 Medium': 'orange', '🟢 Low': 'blue'}
            )
            fig.add_hline(y=np.log1p(2), line_dash="dash", line_color="red", 
                         annotation_text="Signal Threshold (RR=2)")
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # High priority alerts
        high_signals = signal_df[signal_df['Reporting_Ratio'] > 5]
        if not high_signals.empty:
            st.markdown("### 🚨 High Priority Safety Signals")
            for _, row in high_signals.head(5).iterrows():
                st.warning(f"**{row['AE_Term']}** - Reporting Ratio: {row['Reporting_Ratio']:.2f} (Observed: {row['Observed_Count']} events)")

# ============================================
# TAB 3: TRIAL COMPARISON
# ============================================
with tab3:
    st.subheader("🏥 Cross-Trial Adverse Event Comparison")
    
    if not df.empty:
        trial_ae_matrix = pd.crosstab(df['ae_term'], df['trial_id'])
        top_ae_list = df['ae_term'].value_counts().head(10).index.tolist()
        comparison_df = trial_ae_matrix.loc[top_ae_list]
        
        st.markdown("### Top 10 AEs Across Selected Trials")
        fig = px.imshow(
            comparison_df,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Reds",
            title="Adverse Event Frequency Heatmap by Trial",
            labels={'x': 'Trial ID', 'y': 'Adverse Event', 'color': 'Count'}
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Trial Summary Statistics")
        trial_summary = df.groupby('trial_id').agg({
            'ae_term': 'count',
        }).rename(columns={'ae_term': 'Total_AEs'})
        
        serious_by_trial = df[df['ae_type'].astype(str).str.contains('Serious', case=False, na=False)].groupby('trial_id').size()
        trial_summary['Serious_AEs'] = serious_by_trial
        trial_summary['Serious_Percent'] = (trial_summary['Serious_AEs'] / trial_summary['Total_AEs'] * 100).round(1)
        trial_summary = trial_summary.fillna(0)
        
        st.dataframe(trial_summary, use_container_width=True)

# ============================================
# TAB 4: DATA EXPLORER
# ============================================
with tab4:
    st.subheader("📋 Interactive Data Explorer")
    
    if not df.empty:
        display_cols = st.multiselect(
            "Select columns to display",
            options=df.columns.tolist(),
            default=['trial_id', 'ae_term', 'ae_type', 'organ_system', 'count']
        )
        
        search_term = st.text_input("🔍 Search adverse events", placeholder="nausea, fatigue, vomiting...")
        
        filtered_df = df.copy()
        if search_term:
            filtered_df = filtered_df[filtered_df['ae_term'].astype(str).str.contains(search_term, case=False, na=False)]
        
        page_size = st.selectbox("Rows per page", [10, 25, 50, 100, 200])
        total_pages = max(1, (len(filtered_df) + page_size - 1) // page_size)
        page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
        
        start_idx = (page_number - 1) * page_size
        end_idx = start_idx + page_size
        
        st.dataframe(filtered_df[display_cols].iloc[start_idx:end_idx], use_container_width=True, height=400)
        st.caption(f"Showing {len(filtered_df.iloc[start_idx:end_idx])} of {len(filtered_df)} records | Page {page_number} of {total_pages}")

# ============================================
# TAB 5: SAFETY REPORT
# ============================================
with tab5:
    st.subheader("📄 Automated Safety Report")
    
    if not df.empty:
        if st.button("📊 Generate Safety Report", type="primary", use_container_width=True):
            with st.spinner("Generating safety report..."):
                report_data = {
                    "Report_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Total_Adverse_Events": int(len(df)),
                    "Unique_Trials": int(df['trial_id'].nunique()),
                    "Serious_AEs": int(len(df[df['ae_type'].astype(str).str.contains('Serious', case=False, na=False)])),
                    "Top_AE": str(df['ae_term'].mode()[0]) if not df.empty else "N/A",
                    "Data_Source": "ClinicalTrials.gov API",
                    "Filter_Applied": seriousness_filter
                }
                
                st.markdown("## 📊 Safety Monitoring Report Summary")
                st.json(report_data)
                
                output = io.BytesIO()
                df.to_csv(output, index=False)
                st.download_button(
                    label="📥 Download Full Report as CSV",
                    data=output.getvalue(),
                    file_name=f"safety_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                st.success("✅ Report generated successfully!")
    else:
        st.info("No data available to generate report.")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.8rem;'>"
    "🩺 Clinical Trial Safety Monitor | Powered by Streamlit + Snowflake + PySpark<br>"
    "Data sourced from ClinicalTrials.gov API v2 | Real adverse events from 4 cancer trials"
    "</div>",
    unsafe_allow_html=True
)
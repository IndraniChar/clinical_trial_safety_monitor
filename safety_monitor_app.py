import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import io
from datetime import datetime
import numpy as np

# ============================================
# SNOWFLAKE CONFIGURATION (SUPPORTS BOTH LOCAL + CLOUD)
# ============================================

# Try to get config from Streamlit secrets (cloud) OR local config file
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
    st.success("✅ Using Streamlit Cloud secrets for Snowflake")
except:
    # For local development (fallback to config file)
    try:
        from snowflake_config import SNOWFLAKE_CONFIG as local_config
        SNOWFLAKE_CONFIG = local_config
        st.success("✅ Using local snowflake_config.py for Snowflake")
    except:
        st.error("❌ No Snowflake configuration found. Please set up secrets (cloud) or snowflake_config.py (local).")
        st.stop()

# Page config
st.set_page_config(
    page_title="Clinical Trial Safety Monitor",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
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
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 600;
    }
    hr {
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR - Navigation & Controls
# ============================================
with st.sidebar:
    st.markdown("## 🩺 Safety Monitor")
    st.markdown("---")
    
    # Data source selection
    st.markdown("### 📊 Data Source")
    data_source = st.radio(
        "Select data source",
        ["Snowflake Database", "Local CSV File"],
        help="Choose where to load adverse event data from"
    )
    
    st.markdown("---")
    
    # Filters
    st.markdown("### 🔍 Filters")
    trial_filter_placeholder = st.empty()
    seriousness_filter = st.selectbox(
        "Adverse Event Severity",
        ["All Events", "Serious Only", "Non-Serious Only"]
    )
    
    st.markdown("---")
    st.caption(f"🩺 Clinical Trial Safety Monitor v2.0\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ============================================
# MAIN CONTENT AREA
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
        query = "SELECT * FROM ADVERSE_EVENTS ORDER BY REPORT_DATE DESC"
        df = pd.read_sql(query, conn)
        conn.close()
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
    except:
        return pd.DataFrame()

# Load data based on selection
if data_source == "Snowflake Database":
    df = load_data_from_snowflake()
    if df.empty:
        st.warning("No data in Snowflake. Please load data first using load_data.py")
        st.stop()
else:  # Local CSV File
    df = load_data_from_csv()
    if df.empty:
        st.warning("No CSV data found. Please run fetch_ae_data.py first.")
        st.stop()

# Apply filters
if not df.empty:
    # Trial filter
    available_trials = df['trial_id'].unique().tolist() if 'trial_id' in df.columns else []
    selected_trials = trial_filter_placeholder.multiselect(
        "Select Trials to Analyze",
        options=available_trials,
        default=available_trials[:min(4, len(available_trials))] if available_trials else []
    )
    
    if selected_trials and 'trial_id' in df.columns:
        df = df[df['trial_id'].isin(selected_trials)]
    
    # Seriousness filter
    if seriousness_filter == "Serious Only" and 'ae_type' in df.columns:
        df = df[df['ae_type'].str.contains('Serious', case=False, na=False)]
    elif seriousness_filter == "Non-Serious Only" and 'ae_type' in df.columns:
        df = df[~df['ae_type'].str.contains('Serious', case=False, na=False)]

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
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total AEs", f"{len(df):,}")
        with col2:
            serious_count = len(df[df['ae_type'].str.contains('Serious', case=False, na=False)]) if 'ae_type' in df.columns else 0
            st.metric("Serious AEs", f"{serious_count:,}")
        with col3:
            unique_trials = df['trial_id'].nunique() if 'trial_id' in df.columns else 0
            st.metric("Active Trials", unique_trials)
        with col4:
            st.metric("Data Source", "ClinicalTrials.gov")
        
        st.markdown("---")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("📊 Top 15 Adverse Events")
            if 'ae_term' in df.columns:
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
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("⚠️ Serious vs Non-Serious")
            if 'ae_type' in df.columns:
                serious_counts = df['ae_type'].apply(lambda x: 'Serious' if 'Serious' in str(x) else 'Non-Serious').value_counts()
                fig2 = px.pie(
                    values=serious_counts.values,
                    names=serious_counts.index,
                    hole=0.4,
                    color_discrete_sequence=['#ff6b6b', '#4ecdc4']
                )
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data available.")

# ============================================
# TAB 2: SIGNAL DETECTION
# ============================================
with tab2:
    st.subheader("🔬 Statistical Signal Detection")
    
    if not df.empty and 'ae_term' in df.columns:
        ae_counts = df['ae_term'].value_counts()
        total_events = len(df)
        expected = total_events / len(ae_counts)
        
        signal_df = pd.DataFrame({
            'AE_Term': ae_counts.index,
            'Observed': ae_counts.values,
            'Reporting_Ratio': ae_counts.values / expected
        })
        signal_df = signal_df[signal_df['Reporting_Ratio'] > 2].head(20)
        
        if not signal_df.empty:
            st.warning(f"🚨 {len(signal_df)} potential safety signals detected")
            st.dataframe(signal_df, use_container_width=True)
        else:
            st.success("✅ No unusual safety signals detected")

# ============================================
# TAB 3: TRIAL COMPARISON
# ============================================
with tab3:
    st.subheader("🏥 Cross-Trial Comparison")
    
    if not df.empty and 'trial_id' in df.columns and 'ae_term' in df.columns:
        trial_ae_matrix = pd.crosstab(df['ae_term'], df['trial_id'])
        top_ae_list = df['ae_term'].value_counts().head(10).index.tolist()
        comparison_df = trial_ae_matrix.loc[top_ae_list]
        
        fig = px.imshow(
            comparison_df,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Reds",
            title="Adverse Event Frequency Heatmap by Trial"
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

# ============================================
# TAB 4: DATA EXPLORER
# ============================================
with tab4:
    st.subheader("📋 Data Explorer")
    
    if not df.empty:
        search_term = st.text_input("🔍 Search adverse events", placeholder="nausea, fatigue")
        filtered_df = df.copy()
        if search_term and 'ae_term' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['ae_term'].str.contains(search_term, case=False)]
        
        st.dataframe(filtered_df.head(100), use_container_width=True)

# ============================================
# TAB 5: SAFETY REPORT
# ============================================
with tab5:
    st.subheader("📄 Safety Report")
    
    if not df.empty:
        if st.button("Generate Report"):
            report_data = {
                "Report_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Total_Adverse_Events": len(df),
                "Unique_Trials": df['trial_id'].nunique() if 'trial_id' in df.columns else 0,
                "Serious_AEs": len(df[df['ae_type'].str.contains('Serious', case=False)]) if 'ae_type' in df.columns else 0
            }
            st.json(report_data)
            
            output = io.BytesIO()
            df.to_csv(output, index=False)
            st.download_button("Download CSV", data=output.getvalue(), file_name="safety_report.csv")

# Footer
st.markdown("---")
st.caption("🩺 Clinical Trial Safety Monitor | Powered by Streamlit + Snowflake")
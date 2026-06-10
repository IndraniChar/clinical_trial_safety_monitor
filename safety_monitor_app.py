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
from snowflake_config import SNOWFLAKE_CONFIG

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
    .info-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1E3A5F;
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
    st.image("https://img.icons8.com/color/96/clinical-trial.png", width=80)
    st.markdown("## 🩺 Safety Monitor")
    st.markdown("---")
    
    # Data source selection
    st.markdown("### 📊 Data Source")
    data_source = st.radio(
        "Select data source",
        ["ClinicalTrials.gov API", "Upload Your Own Data", "Snowflake Database"],
        help="Choose where to load adverse event data from"
    )
    
    st.markdown("---")
    
    # Filters
    st.markdown("### 🔍 Filters")
    
    # Trial selection (will be populated after data load)
    trial_filter_placeholder = st.empty()
    
    # Seriousness filter
    seriousness_filter = st.selectbox(
        "Adverse Event Severity",
        ["All Events", "Serious Only", "Non-Serious Only"]
    )
    
    # Date range
    st.markdown("### 📅 Date Range")
    date_range = st.date_input(
        "Select date range",
        value=()
    )
    
    st.markdown("---")
    
    # Report generation
    st.markdown("### 📄 Export")
    if st.button("📥 Generate Safety Report", use_container_width=True):
        st.info("Report generation will be available after data load")
    
    st.markdown("---")
    st.caption(f"🩺 Clinical Trial Safety Monitor v2.0\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ============================================
# MAIN CONTENT AREA
# ============================================

st.markdown('<p class="main-header">🩺 Clinical Trial Adverse Event Safety Monitor</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Real-time pharmacovigilance platform for cancer clinical trials | Powered by ClinicalTrials.gov API + Snowflake</p>', unsafe_allow_html=True)

# ============================================
# DATA LOADING FUNCTION
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
def load_data_from_api():
    """Fetch fresh data from API"""
    with st.spinner("Fetching latest adverse event data from ClinicalTrials.gov..."):
        # Try to load existing CSV first
        try:
            df = pd.read_csv('fetched_ae_data.csv')
            st.success(f"✅ Loaded {len(df)} adverse events from cached data")
            return df
        except:
            st.error("No cached data found. Run fetch_ae_data.py first.")
            return pd.DataFrame()

# Load data based on selection
if data_source == "Snowflake Database":
    df = load_data_from_snowflake()
    if df.empty:
        st.warning("No data in Snowflake. Please load data first using load_data.py")
        st.stop()
elif data_source == "Upload Your Own Data":
    uploaded_file = st.file_uploader("Upload CSV file with adverse event data", type=['csv'])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Loaded {len(df)} records from uploaded file")
    else:
        st.info("Please upload a CSV file containing adverse event data")
        st.stop()
else:  # API
    df = load_data_from_api()
    if df.empty:
        st.warning("No data available. Run fetch_ae_data.py first.")
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
# TABBED INTERFACE (Like your R/Shiny app)
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
        # Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3 style="margin:0; font-size:0.9rem;">Total AEs</h3>
                <p style="margin:0; font-size:2rem; font-weight:bold;">{}</p>
            </div>
            """.format(len(df)), unsafe_allow_html=True)
        
        with col2:
            serious_count = len(df[df['ae_type'].str.contains('Serious', case=False, na=False)]) if 'ae_type' in df.columns else 0
            st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <h3 style="margin:0; font-size:0.9rem;">Serious AEs</h3>
                <p style="margin:0; font-size:2rem; font-weight:bold;">{}</p>
            </div>
            """.format(serious_count), unsafe_allow_html=True)
        
        with col3:
            unique_trials = df['trial_id'].nunique() if 'trial_id' in df.columns else 0
            st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <h3 style="margin:0; font-size:0.9rem;">Active Trials</h3>
                <p style="margin:0; font-size:2rem; font-weight:bold;">{}</p>
            </div>
            """.format(unique_trials), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                <h3 style="margin:0; font-size:0.9rem;">Data Source</h3>
                <p style="margin:0; font-size:1rem; font-weight:bold;">ClinicalTrials.gov</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Top AEs Chart
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
                fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("⚠️ Serious vs Non-Serious")
            if 'ae_type' in df.columns:
                serious_counts = df['ae_type'].apply(lambda x: 'Serious' if 'Serious' in str(x) else 'Non-Serious').value_counts()
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
            if 'ae_type' in df.columns:
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
        st.info("No data available. Please check your data source.")

# ============================================
# TAB 2: SIGNAL DETECTION
# ============================================
with tab2:
    st.subheader("🔬 Statistical Signal Detection")
    st.markdown("Disproportionality analysis for adverse event signal detection")
    
    if not df.empty and 'ae_term' in df.columns:
        # Calculate reporting ratios
        ae_counts = df['ae_term'].value_counts()
        total_events = len(df)
        
        signal_df = pd.DataFrame({
            'AE_Term': ae_counts.index,
            'Observed_Count': ae_counts.values,
            'Expected_Rate': total_events / len(ae_counts),
            'Reporting_Ratio': ae_counts.values / (total_events / len(ae_counts))
        })
        
        # Flag signals (Reporting Ratio > 2)
        signal_df['Signal'] = signal_df['Reporting_Ratio'] > 2
        signal_df['Alert_Level'] = np.where(
            signal_df['Reporting_Ratio'] > 5, 'High',
            np.where(signal_df['Reporting_Ratio'] > 2, 'Medium', 'Low')
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Signal Detection Results")
            st.dataframe(
                signal_df[signal_df['Signal']].head(20),
                use_container_width=True,
                column_config={
                    "AE_Term": "Adverse Event",
                    "Observed_Count": "Observed",
                    "Reporting_Ratio": st.column_config.NumberColumn("Ratio", format="%.2f"),
                    "Alert_Level": st.column_config.Column("Alert")
                }
            )
        
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
                color_discrete_map={'High': 'red', 'Medium': 'orange', 'Low': 'blue'}
            )
            fig.add_hline(y=np.log1p(2), line_dash="dash", line_color="red")
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # High priority alerts
        high_signals = signal_df[signal_df['Alert_Level'] == 'High']
        if not high_signals.empty:
            st.markdown("### 🚨 High Priority Safety Signals")
            for _, row in high_signals.head(5).iterrows():
                st.warning(f"**{row['AE_Term']}** - Reporting Ratio: {row['Reporting_Ratio']:.2f} (Observed: {row['Observed_Count']} events)")

# ============================================
# TAB 3: TRIAL COMPARISON
# ============================================
with tab3:
    st.subheader("🏥 Cross-Trial Adverse Event Comparison")
    
    if not df.empty and 'trial_id' in df.columns and 'ae_term' in df.columns:
        # Create comparison matrix
        trial_ae_matrix = pd.crosstab(df['ae_term'], df['trial_id'])
        
        # Top AEs across trials
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
        
        # Trial summary
        st.markdown("### Trial Summary Statistics")
        trial_summary = df.groupby('trial_id').agg({
            'ae_term': 'count',
        }).rename(columns={'ae_term': 'Total_AEs'})
        
        if 'ae_type' in df.columns:
            serious_by_trial = df[df['ae_type'].str.contains('Serious', case=False, na=False)].groupby('trial_id').size()
            trial_summary['Serious_AEs'] = serious_by_trial
            trial_summary['Serious_Percent'] = (trial_summary['Serious_AEs'] / trial_summary['Total_AEs'] * 100).round(1)
        
        st.dataframe(trial_summary, use_container_width=True)

# ============================================
# TAB 4: DATA EXPLORER
# ============================================
with tab4:
    st.subheader("📋 Interactive Data Explorer")
    
    if not df.empty:
        # Column selector
        available_cols = df.columns.tolist()
        display_cols = st.multiselect(
            "Select columns to display",
            options=available_cols,
            default=available_cols[:min(5, len(available_cols))]
        )
        
        # Search filter
        search_term = st.text_input("🔍 Search adverse events", placeholder="nausea, fatigue, etc.")
        
        filtered_df = df.copy()
        if search_term and 'ae_term' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['ae_term'].str.contains(search_term, case=False, na=False)]
        
        # Pagination
        page_size = st.selectbox("Rows per page", [10, 25, 50, 100])
        page_number = st.number_input("Page", min_value=1, value=1)
        
        start_idx = (page_number - 1) * page_size
        end_idx = start_idx + page_size
        
        st.dataframe(
            filtered_df[display_cols].iloc[start_idx:end_idx],
            use_container_width=True,
            height=400
        )
        
        st.caption(f"Showing {len(filtered_df.iloc[start_idx:end_idx])} of {len(filtered_df)} records")

# ============================================
# TAB 5: SAFETY REPORT
# ============================================
with tab5:
    st.subheader("📄 Automated Safety Report")
    
    if not df.empty:
        if st.button("Generate PDF Report", type="primary"):
            with st.spinner("Generating safety report..."):
                # Create summary statistics
                report_data = {
                    "Report_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Total_Adverse_Events": len(df),
                    "Unique_Trials": df['trial_id'].nunique() if 'trial_id' in df.columns else 0,
                    "Serious_AEs": len(df[df['ae_type'].str.contains('Serious', case=False, na=False)]) if 'ae_type' in df.columns else 0,
                    "Top_AE": df['ae_term'].mode()[0] if 'ae_term' in df.columns else "N/A",
                    "Data_Source": "ClinicalTrials.gov API"
                }
                
                st.markdown("## 📊 Safety Monitoring Report")
                st.json(report_data)
                
                # Create downloadable CSV
                output = io.BytesIO()
                df.to_csv(output, index=False)
                st.download_button(
                    label="📥 Download Report as CSV",
                    data=output.getvalue(),
                    file_name=f"safety_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
                st.success("✅ Report generated successfully!")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🩺 Clinical Trial Safety Monitor | Powered by Streamlit + Snowflake + PySpark<br>"
    "Data sourced from ClinicalTrials.gov API v2"
    "</div>",
    unsafe_allow_html=True
)
import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
from snowflake_config import SNOWFLAKE_CONFIG

st.set_page_config(page_title="Cancer Trial AE Monitor", layout="wide")
st.title("🔬 Real-Time Adverse Event Monitor")

@st.cache_data(ttl=300)
def load_data():
    conn = snowflake.connector.connect(
        account=SNOWFLAKE_CONFIG["account"],
        user=SNOWFLAKE_CONFIG["user"],
        password=SNOWFLAKE_CONFIG["password"],
        warehouse=SNOWFLAKE_CONFIG["warehouse"],
        database=SNOWFLAKE_CONFIG["database"],
        schema=SNOWFLAKE_CONFIG["schema_raw"]
    )
    df = pd.read_sql("SELECT * FROM ADVERSE_EVENTS ORDER BY REPORT_DATE DESC", conn)
    conn.close()
    return df

df = load_data()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total AEs", len(df))
with col2:
    st.metric("Serious AEs", len(df[df['SERIOUS'] == True]) if not df.empty else 0)
with col3:
    st.metric("Unique Trials", df['TRIAL_ID'].nunique() if not df.empty else 0)

if not df.empty and len(df) > 0:
    fig = px.bar(df['AE_TERM'].value_counts().head(10), 
                 title="Top 10 Adverse Events")
    st.plotly_chart(fig)
    st.dataframe(df[['TRIAL_ID', 'AE_TERM', 'AE_SEVERITY']].head(20))
else:
    st.warning("No data yet. Run the pipeline first!")
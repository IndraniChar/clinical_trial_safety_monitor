import snowflake.connector
import pandas as pd
import os
from snowflake_config import SNOWFLAKE_CONFIG

if not os.path.exists('fetched_ae_data.csv'):
    print("❌ No data file. Run fetch_ae_data.py first!")
    exit(1)

df = pd.read_csv('fetched_ae_data.csv')
print(f"📊 Loading {len(df)} records to Snowflake...")

conn = snowflake.connector.connect(
    account=SNOWFLAKE_CONFIG["account"],
    user=SNOWFLAKE_CONFIG["user"],
    password=SNOWFLAKE_CONFIG["password"],
    warehouse=SNOWFLAKE_CONFIG["warehouse"],
    database=SNOWFLAKE_CONFIG["database"],
    schema=SNOWFLAKE_CONFIG["schema_raw"]
)

cursor = conn.cursor()

for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO ADVERSE_EVENTS 
        (trial_id, ae_term, ae_severity, serious, meddra_code, source_system)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        row['trial_id'],
        row['ae_term'],
        row['ae_severity'],
        bool(row['serious']),
        row['meddra_code'],
        row['source_system']
    ))

conn.commit()
print(f"✅ Loaded {len(df)} records to Snowflake!")

cursor.execute("SELECT COUNT(*) FROM ADVERSE_EVENTS")
count = cursor.fetchone()[0]
print(f"📊 Total in Snowflake: {count}")

cursor.close()
conn.close()
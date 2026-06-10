import snowflake.connector
import pandas as pd
from snowflake_config import SNOWFLAKE_CONFIG

# Load the data
df = pd.read_csv('fetched_ae_data.csv')
print(f"📊 Loading {len(df)} records to Snowflake...")

# Fill empty values
df = df.fillna('Unknown')

# Connect to Snowflake
conn = snowflake.connector.connect(
    account=SNOWFLAKE_CONFIG["account"],
    user=SNOWFLAKE_CONFIG["user"],
    password=SNOWFLAKE_CONFIG["password"],
    warehouse=SNOWFLAKE_CONFIG["warehouse"],
    database=SNOWFLAKE_CONFIG["database"],
    schema=SNOWFLAKE_CONFIG["schema_raw"]
)

cursor = conn.cursor()

# Clear existing data (optional - remove if you want to keep old data)
cursor.execute("DELETE FROM ADVERSE_EVENTS")

# Insert records in batches
batch_size = 100
inserted = 0

for i in range(0, len(df), batch_size):
    batch = df.iloc[i:i+batch_size]
    for _, row in batch.iterrows():
        try:
            cursor.execute("""
                INSERT INTO ADVERSE_EVENTS 
                (trial_id, ae_term, ae_severity, serious, meddra_code, source_system)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                str(row['trial_id']),
                str(row['ae_term'])[:500],
                str(row['ae_type'])[:100],
                True if 'serious' in str(row['ae_type']).lower() else False,
                str(row.get('organ_system', 'Unknown'))[:20],
                str(row['source_system'])
            ))
            inserted += 1
        except Exception as e:
            print(f"Error on row: {e}")
    
    print(f"  Inserted {inserted} of {len(df)} records")

conn.commit()
print(f"\n✅ Successfully loaded {inserted} records to Snowflake!")

# Verify
cursor.execute("SELECT COUNT(*) FROM ADVERSE_EVENTS")
count = cursor.fetchone()[0]
print(f"📊 Total records now in Snowflake: {count}")

cursor.close()
conn.close()
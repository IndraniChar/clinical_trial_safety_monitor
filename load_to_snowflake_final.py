import snowflake.connector
import pandas as pd
from datetime import datetime

# ============================================
# YOUR SNOWFLAKE CREDENTIALS (FILL THESE IN)
# ============================================
SNOWFLAKE_CONFIG = {
    "account": "if79614.ap-southeast-7.aws",
    "user": "IndraniChar",          # ← Your Snowflake username
    "password": "Fantameow@041101",  # ← Your Snowflake password
    "warehouse": "CLINICAL_WH",
    "database": "CLINICAL_TRIAL_DB",
    "schema_raw": "RAW_AE_DATA"
}

# ============================================
# LOAD CSV DATA
# ============================================
print("📊 Loading CSV data...")
df = pd.read_csv('fetched_ae_data.csv')
print(f"✅ Loaded {len(df)} records from fetched_ae_data.csv")

# Clean the data
df = df.fillna('Unknown')
print(f"📋 Columns: {df.columns.tolist()}")

# ============================================
# CONNECT TO SNOWFLAKE
# ============================================
print("\n🔗 Connecting to Snowflake...")
conn = snowflake.connector.connect(
    account=SNOWFLAKE_CONFIG["account"],
    user=SNOWFLAKE_CONFIG["user"],
    password=SNOWFLAKE_CONFIG["password"],
    warehouse=SNOWFLAKE_CONFIG["warehouse"],
    database=SNOWFLAKE_CONFIG["database"],
    schema=SNOWFLAKE_CONFIG["schema_raw"]
)

cursor = conn.cursor()
print("✅ Connected to Snowflake!")

# ============================================
# CREATE TABLE (if not exists)
# ============================================
print("\n📋 Creating table if not exists...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS ADVERSE_EVENTS (
        event_id NUMBER AUTOINCREMENT,
        trial_id VARCHAR(50),
        ae_term VARCHAR(500),
        ae_type VARCHAR(100),
        organ_system VARCHAR(200),
        event_count NUMBER,
        source_system VARCHAR(50),
        report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    )
""")

# ============================================
# CLEAR OLD DATA (optional - comment out if you want to keep)
# ============================================
cursor.execute("TRUNCATE TABLE ADVERSE_EVENTS")
print("✅ Cleared existing data")

# ============================================
# INSERT RECORDS IN BATCHES
# ============================================
print(f"\n💾 Loading {len(df)} records to Snowflake...")

batch_size = 100
inserted = 0

for i in range(0, len(df), batch_size):
    batch = df.iloc[i:i+batch_size]
    for _, row in batch.iterrows():
        try:
            cursor.execute("""
                INSERT INTO ADVERSE_EVENTS 
                (trial_id, ae_term, ae_type, organ_system, event_count, source_system)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                str(row['trial_id']),
                str(row['ae_term'])[:500],
                str(row['ae_type'])[:100],
                str(row.get('organ_system', 'Unknown'))[:200],
                int(row.get('count', 0)),
                str(row['source_system'])
            ))
            inserted += 1
        except Exception as e:
            print(f"  ⚠️ Error on row {i}: {e}")
    
    print(f"  ✅ Inserted {inserted} of {len(df)} records")

conn.commit()
print(f"\n🎉 SUCCESS! Loaded {inserted} records to Snowflake!")

# ============================================
# VERIFY
# ============================================
cursor.execute("SELECT COUNT(*) FROM ADVERSE_EVENTS")
count = cursor.fetchone()[0]
print(f"📊 Total records now in Snowflake: {count}")

# Show sample
cursor.execute("SELECT trial_id, ae_term, ae_type FROM ADVERSE_EVENTS LIMIT 5")
sample = cursor.fetchall()
print("\n📋 Sample data in Snowflake:")
for row in sample:
    print(f"   {row[0]} | {row[1][:40]} | {row[2]}")

cursor.close()
conn.close()
print("\n✅ Done!")
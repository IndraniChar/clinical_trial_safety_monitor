import snowflake.connector
from snowflake_config import SNOWFLAKE_CONFIG

def test_connection():
    try:
        conn = snowflake.connector.connect(
            account=SNOWFLAKE_CONFIG["account"],
            user=SNOWFLAKE_CONFIG["user"],
            password=SNOWFLAKE_CONFIG["password"],
            warehouse=SNOWFLAKE_CONFIG["warehouse"],
            database=SNOWFLAKE_CONFIG["database"],
            schema=SNOWFLAKE_CONFIG["schema_raw"]
        )
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to Snowflake! Version: {version}")
        
        cursor.execute("SELECT COUNT(*) FROM ADVERSE_EVENTS")
        count = cursor.fetchone()[0]
        print(f"📊 Current AE records: {count}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
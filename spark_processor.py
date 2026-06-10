from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, desc
import pandas as pd
import os

# Check if data exists
if not os.path.exists('fetched_ae_data.csv'):
    print("❌ No data file found. Run fetch_ae_data.py first!")
    exit(1)

# Initialize Spark
spark = SparkSession.builder \
    .appName("ClinicalTrial_AE_Monitor") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()

print("✅ Spark session created")

# Load data
df_pandas = pd.read_csv('fetched_ae_data.csv')
df_spark = spark.createDataFrame(df_pandas)

print(f"📊 Loaded {df_spark.count()} AE records into Spark")

# Analyze
print("\n🔍 Top adverse events:")
top_ae = df_spark.groupBy("ae_term") \
    .agg(count("*").alias("frequency")) \
    .orderBy(desc("frequency"))

top_ae.show(10)

print("\n📋 AE counts by trial:")
trial_counts = df_spark.groupBy("trial_id") \
    .agg(count("*").alias("ae_count")) \
    .orderBy(desc("ae_count"))

trial_counts.show()

spark.stop()
print("\n✅ Spark processing complete")
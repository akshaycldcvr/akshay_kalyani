import os
import pandas as pd
from sqlalchemy import create_engine, text

# --- Configuration (Hardcoded except for password) ---
DB_USER = "postgres"  # Replace with your DB username if different
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = "35.192.179.98"  # Replace with your RDS endpoint or Cloud SQL IP
TARGET_DB_NAME = "data_valid"  # The database where data will be pushed

# Fail fast if password environment variable is missing
if not DB_PASSWORD:
    raise ValueError(
        "Error: DB_PASSWORD environment variable is not set in the terminal."
    )

# 1. Connect to the default 'postgres' database first to create 'data_valid' if needed
default_engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/postgres"
)

try:
    with default_engine.connect().execution_options(
        isolation_level="AUTOCOMMIT"
    ) as conn:
        # Check if database exists, create if it doesn't
        result = conn.execute(
            text(
                f"SELECT 1 FROM pg_database WHERE datname = '{TARGET_DB_NAME}'"
            )
        )
        if not result.fetchone():
            conn.execute(text(f"CREATE DATABASE {TARGET_DB_NAME};"))
            print(f"Database '{TARGET_DB_NAME}' created successfully.")
        else:
            print(f"Database '{TARGET_DB_NAME}' already exists.")
except Exception as e:
    print(f"Database creation check failed: {e}")
    exit(1)

# 2. Connect to the target 'data_valid' database
target_engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{TARGET_DB_NAME}"
)

# 3. Read the CSV data (Ensure 'large_customers.csv' is in the same directory)
csv_filename = "large_customers.csv"
if not os.path.exists(csv_filename):
    raise FileNotFoundError(
        f"Error: Could not find '{csv_filename}' in the current directory."
    )

df = pd.read_csv(csv_filename)

# 4. Bulk insert into the 'customers' table (replaces table if it already exists)
df.to_sql("customers", con=target_engine, if_exists="replace", index=False)

print(
    f"Successfully uploaded {len(df)} rows into 'customers' table inside database '{TARGET_DB_NAME}'!"
)
import pandas as pd
import pyodbc

# SQL Server connection details
server = "udevlment.brobot.com,7359"
database = "MLAISPEECHBOT"
username = "MLAIBOT"
password = "########"

# Connection string for SQL Server
conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

# Load the Excel file
excel_path = "../data/GarageReport2.xlsx"
df = pd.read_excel(excel_path)

# Clean column names (remove extra spaces)
df.columns = [col.strip() for col in df.columns]

# Define table name
table_name = "FinalGarageMaster"

# Define column types for SQL Server (Assuming all as NVARCHAR(MAX))
columns_definition = ", ".join([f"[{col}] NVARCHAR(MAX)" for col in df.columns])
create_table_query = f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table_name}') BEGIN CREATE TABLE {table_name} ({columns_definition}) END"

conn = None
try:
    # Connect to SQL Server
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Create table if it does not exist
    cursor.execute(create_table_query)
    conn.commit()

    # Insert data into the table
    db_columns = ", ".join([f"[{col}]" for col in df.columns])
    placeholders = ", ".join(["?" for _ in df.columns])
    query = f"INSERT INTO {table_name} ({db_columns}) VALUES ({placeholders})"

    for _, row in df.iterrows():
        cursor.execute(query, tuple(row))

    # Commit changes
    conn.commit()
    print("Data uploaded successfully.")
except pyodbc.Error as e:
    print("SQL Server error:", e)
finally:
    if conn:
        conn.close()

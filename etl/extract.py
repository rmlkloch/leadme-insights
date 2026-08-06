import os
import sqlite3
from pathlib import Path
import pandas as pd

# Define default database path relative to this script's directory (etl/ -> root/data/leadme.db)
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "leadme.db"


def get_readonly_connection(db_path: Path):
    """
    Establishes a secure, read-only connection to the SQLite database.
    Raises FileNotFoundError if the database file does not exist.
    """
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database file not found at: {db_path.resolve()}\n"
            "Please ensure 'leadme.db' is placed inside the 'data/' directory."
        )

    # Convert path to URI format for read-only SQLite connection
    # uri=True allows mode=ro parameter which prevents accidental writes/locks
    db_uri = f"file:{db_path.as_posix()}?mode=ro"
    conn = sqlite3.connect(db_uri, uri=True)
    return conn


def extract_raw_data(db_path: Path = DEFAULT_DB_PATH):
    """
    Extracts raw leads and tickets data from the SQLite database into Pandas DataFrames.

    Returns:
        tuple: (leads_df, tickets_df) containing extracted raw data.
    """
    print(f"Connecting to database at: {db_path.resolve()}")

    conn = None
    try:
        conn = get_readonly_connection(db_path)
        print("Secure read-only connection established successfully.")

        # Extract complete leads table
        print("\n--- Extracting 'leads' table ---")
        leads_df = pd.read_sql_query("SELECT * FROM leads", conn)
        print(f"Leads extracted successfully ({len(leads_df)} rows).")

        # Extract complete tickets table
        print("\n--- Extracting 'tickets' table ---")
        tickets_df = pd.read_sql_query("SELECT * FROM tickets", conn)
        print(f"Tickets extracted successfully ({len(tickets_df)} rows).")

        # Display Summary Information
        print("\n" + "=" * 50)
        print("LEADS TABLE SUMMARY (.info()):")
        print("=" * 50)
        leads_df.info()

        print("\n" + "=" * 50)
        print("LEADS TABLE HEAD (.head()):")
        print("=" * 50)
        print(leads_df.head())

        print("\n" + "=" * 50)
        print("TICKETS TABLE SUMMARY (.info()):")
        print("=" * 50)
        tickets_df.info()

        print("\n" + "=" * 50)
        print("TICKETS TABLE HEAD (.head()):")
        print("=" * 50)
        print(tickets_df.head())

        return leads_df, tickets_df

    except FileNotFoundError as e:
        print(f"\n[ERROR] File Error: {e}")
        return None, None
    except sqlite3.Error as e:
        print(f"\n[ERROR] SQLite Database Error: {e}")
        return None, None
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during extraction: {e}")
        return None, None
    finally:
        if conn:
            conn.close()
            print("\nDatabase connection closed.")


def transform_data(leads_df, tickets_df):
    """
    Transforms and cleans the raw leads and tickets data.
    - Converts dates to proper datetime objects.
    - Merges tables on lead_id (LEFT JOIN).
    - Fills missing values with defaults.
    - Renames overlapping columns.
    """
    print("\n--- Starting Data Transformation ---")
    
    # 1. Date Formatting
    if 'created_at' in leads_df.columns:
        leads_df['created_at'] = pd.to_datetime(leads_df['created_at'])
    if 'created_at' in tickets_df.columns:
        tickets_df['created_at'] = pd.to_datetime(tickets_df['created_at'])
        
    # 2. Table Merging (LEFT JOIN)
    # Merge leads and tickets on lead_id
    master_df = pd.merge(
        leads_df, 
        tickets_df, 
        on='lead_id', 
        how='left', 
        suffixes=('_lead', '_ticket')
    )
    
    # Rename overlapping created_at columns to match requirements
    master_df = master_df.rename(columns={
        'created_at_lead': 'lead_created_at',
        'created_at_ticket': 'ticket_created_at'
    })
    
    # 3. Null Handling
    # Fill missing values in ticket columns for leads without tickets
    if 'status' in master_df.columns:
        master_df['status'] = master_df['status'].fillna('No Ticket')
    if 'channel' in master_df.columns:
        master_df['channel'] = master_df['channel'].fillna('Unknown')
    if 'subject' in master_df.columns:
        master_df['subject'] = master_df['subject'].fillna('No Subject')
        
    print("Data Transformation completed successfully.")
    return master_df


def load_data(master_df):
    """
    Exports the transformed master dataset to a CSV file for Power BI.
    """
    print("\n--- Starting Data Export ---")
    
    # Define export path
    export_dir = BASE_DIR / "data" / "analytics"
    export_path = export_dir / "leadme_master_dataset.csv"
    
    # Ensure directory exists just in case
    export_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Export to CSV without the index column
        master_df.to_csv(export_path, index=False)
        print(f"Data successfully exported to data/analytics/leadme_master_dataset.csv")
        print(f"(Full path: {export_path.resolve()})")
    except Exception as e:
        print(f"[ERROR] Failed to export data: {e}")


if __name__ == "__main__":
    # Phase 1: Extraction
    leads_df, tickets_df = extract_raw_data()
    
    if leads_df is not None and tickets_df is not None:
        # Phase 2: Transformation
        master_df = transform_data(leads_df, tickets_df)
        
        # Verify the merge and data types
        print("\n" + "=" * 50)
        print("MASTER TABLE SUMMARY (.info()):")
        print("=" * 50)
        master_df.info()

        print("\n" + "=" * 50)
        print("MASTER TABLE HEAD (.head()):")
        print("=" * 50)
        print(master_df.head())
        
        # Phase 3: Automated Loading & Export
        load_data(master_df)

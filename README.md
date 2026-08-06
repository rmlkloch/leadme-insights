# LeadMe Insights - ETL Pipeline & Power BI Dashboard

## Overview
**LeadMe Insights** is a Python-based ETL (Extract, Transform, Load) pipeline designed to bridge the gap between raw chatbot data and powerful business intelligence. It securely extracts data from an existing SQLite chatbot database (`leadme.db`), cleans and merges the data using Pandas, and outputs a flattened master dataset optimized for direct ingestion into Power BI.

## Tech Stack
* **Python**: Core scripting language for the ETL pipeline.
* **Pandas**: Used for robust data transformation, cleaning, and table merging.
* **SQLite**: Lightweight database engine; queried using secure, read-only connections.
* **Power BI**: The downstream business intelligence platform for visualizing the final dataset.

## Project Structure
```text
leadme-insights/
├── data/
│   ├── leadme.db                  # (Source) The raw SQLite database
│   └── analytics/                 # (Destination) Folder for pipeline outputs
│       └── leadme_master_dataset.csv # The final generated CSV for Power BI
├── etl/
│   └── extract.py                 # The core Python ETL script
├── run_etl.bat                    # Windows batch script for task automation
└── README.md                      # Project documentation
```

## Local Setup

### 1. Prerequisites
Ensure you have Python installed on your system. You will also need the Pandas library. Install the required dependencies using pip:
```cmd
pip install pandas
```

### 2. Database Placement
Ensure your source SQLite database is named `leadme.db` and placed in the `data/` directory at the root of the project:
`data/leadme.db`

### 3. Running the Pipeline Manually
You can run the ETL script directly from your terminal to generate or refresh the dataset:
```cmd
python etl/extract.py
```
Upon successful execution, the script will output the cleaned master dataset to `data/analytics/leadme_master_dataset.csv`.

## Power BI Integration
To visualize your data:
1. Open Power BI Desktop.
2. Click **Get Data** > **Text/CSV**.
3. Navigate to this project's folder and select `data/analytics/leadme_master_dataset.csv`.
4. Click **Load** (or **Transform Data** if you wish to apply Power BI specific modeling).
5. As the Python pipeline updates the CSV file, simply click **Refresh** in Power BI to see your latest data.

## Automating the Pipeline (Windows)
You can completely automate data refreshes so your Power BI dashboards always have up-to-date data. A batch script (`run_etl.bat`) is included to facilitate this via Windows Task Scheduler.

### Setup Instructions for Windows Task Scheduler:
1. Open the **Start Menu**, search for **Task Scheduler**, and open it.
2. In the right-hand Actions pane, click **Create Basic Task...**
3. **Name**: Enter a name like "LeadMe Insights ETL Refresh".
4. **Trigger**: Choose how often you want the pipeline to run (e.g., **Daily**). For hourly runs, choose Daily, then in Advanced Settings set it to repeat every 1 hour.
5. **Action**: Select **Start a program**.
6. **Program/script**: Click **Browse...** and select the `run_etl.bat` file located in the root of this project.
7. Click **Finish**.

*Note: The `run_etl.bat` script handles navigating to the project directory automatically, which prevents common relative path errors in Task Scheduler.*

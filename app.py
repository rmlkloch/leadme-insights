import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

# 1. Page Configuration
st.set_page_config(page_title="LeadMe Intelligence Hub", layout="wide")

# Modern dark theme for plotly charts
PLOTLY_TEMPLATE = "plotly_dark"

@st.cache_data(ttl=5)
def load_data():
    """Load data from PostgreSQL and apply ETL transformations."""
    # Retrieve the database URL from Streamlit's secret manager
    db_url = st.secrets["DATABASE_URL"]
    
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    engine = create_engine(db_url)
    
    # Extraction
    try:
        leads_df = pd.read_sql("SELECT * FROM leads", engine)
    except Exception:
        leads_df = pd.DataFrame()
        
    try:
        tickets_df = pd.read_sql("SELECT * FROM tickets", engine)
    except Exception:
        tickets_df = pd.DataFrame()
        
    if leads_df.empty or 'lead_id' not in leads_df.columns:
        return pd.DataFrame()
        
    if 'lead_id' not in tickets_df.columns:
        tickets_df = pd.DataFrame(columns=['lead_id'])
    
    # Date Formatting
    if 'created_at' in leads_df.columns:
        leads_df['created_at'] = pd.to_datetime(leads_df['created_at'])
    if 'created_at' in tickets_df.columns:
        tickets_df['created_at'] = pd.to_datetime(tickets_df['created_at'])
        
    # Table Merging (LEFT JOIN)
    df = pd.merge(
        leads_df, 
        tickets_df, 
        on='lead_id', 
        how='left', 
        suffixes=('_lead', '_ticket')
    )
    
    # Rename overlapping columns to match chart expectations
    df = df.rename(columns={
        'created_at_lead': 'lead_created_at',
        'created_at_ticket': 'ticket_created_at'
    })
    
    # Null Handling
    if 'status' in df.columns:
        df['status'] = df['status'].fillna('No Ticket')
    if 'channel' in df.columns:
        df['channel'] = df['channel'].fillna('Unknown')
    if 'subject' in df.columns:
        df['subject'] = df['subject'].fillna('No Subject')
    
    # Extract necessary derived columns
    df['Query Hour'] = df['lead_created_at'].dt.hour
    df['Day of Week'] = df['lead_created_at'].dt.day_name()
    
    return df

# Load the data
try:
    df = load_data()
    if df.empty:
        st.info("No lead data captured yet.")
        st.stop()
except Exception as e:
    st.error(f"Failed to load data from database: {e}")
    st.stop()

# Header
st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>LeadMe Intelligence Hub</h1>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Top Row (KPIs)
# ------------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

# Calculate Core Metrics
total_leads = df['lead_id'].nunique()
total_tickets = df['ticket_id'].nunique()

# Conversion Rate: Leads that have at least one ticket
leads_with_tickets = df[df['ticket_id'].notna()]['lead_id'].nunique()
conversion_rate = (leads_with_tickets / total_leads * 100) if total_leads > 0 else 0

# Resolution Rate: Tickets with status 'Closed' (or 'Resolved')
resolved_tickets = df[df['status'].isin(['Closed', 'Resolved'])]['ticket_id'].nunique()
resolution_rate = (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0

with col1:
    st.metric("Total Leads", f"{total_leads}")
with col2:
    st.metric("Total Tickets", f"{total_tickets}")
with col3:
    st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
with col4:
    st.metric("Resolution Rate", f"{resolution_rate:.1f}%")

st.markdown("<hr/>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Middle Row (Charts)
# ------------------------------------------------------------------------------
col_mid1, col_mid2, col_mid3 = st.columns(3)

with col_mid1:
    st.subheader("Peak Query Times")
    hourly_leads = df.groupby('Query Hour')['lead_id'].nunique().reset_index()
    fig_hour = px.bar(
        hourly_leads, 
        x='Query Hour', 
        y='lead_id', 
        labels={'lead_id': 'Total Leads', 'Query Hour': 'Hour of Day'}, 
        template=PLOTLY_TEMPLATE
    )
    st.plotly_chart(fig_hour, width="stretch")

with col_mid2:
    st.subheader("Channel Performance")
    channel_tickets = df[df['ticket_id'].notna()].groupby('channel')['ticket_id'].nunique().reset_index()
    fig_channel = px.pie(
        channel_tickets, 
        names='channel', 
        values='ticket_id', 
        hole=0.4, 
        template=PLOTLY_TEMPLATE
    )
    st.plotly_chart(fig_channel, width="stretch")

with col_mid3:
    st.subheader("Traffic by Day of Week")
    # Order days correctly
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_leads = df.groupby('Day of Week')['lead_id'].nunique().reindex(days_order).reset_index()
    # Handle NaN values for days without traffic if needed
    daily_leads = daily_leads.dropna()
    
    fig_day = px.bar(
        daily_leads, 
        x='Day of Week', 
        y='lead_id', 
        labels={'lead_id': 'Total Leads', 'Day of Week': 'Day'}, 
        template=PLOTLY_TEMPLATE
    )
    st.plotly_chart(fig_day, width="stretch")

st.markdown("<hr/>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Bottom Row (Charts)
# ------------------------------------------------------------------------------
col_bot1, col_bot2 = st.columns(2)

with col_bot1:
    st.subheader("Knowledge Gaps (Open/Pending)")
    # Filter for Open/Pending tickets and group by subject
    open_tickets_df = df[df['status'].isin(['Open', 'Pending'])]
    subject_counts = open_tickets_df.groupby('subject')['ticket_id'].nunique().reset_index().sort_values('ticket_id', ascending=True)
    
    fig_gaps = px.bar(
        subject_counts, 
        x='ticket_id', 
        y='subject', 
        orientation='h', 
        labels={'ticket_id': 'Ticket Count', 'subject': 'Subject'}, 
        template=PLOTLY_TEMPLATE
    )
    st.plotly_chart(fig_gaps, width="stretch")

with col_bot2:
    st.subheader("The Engagement Funnel")
    funnel_data = dict(
        number=[total_leads, total_tickets, resolved_tickets],
        stage=["Total Leads", "Total Tickets", "Resolved Tickets"]
    )
    fig_funnel = px.funnel(
        funnel_data, 
        x='number', 
        y='stage', 
        template=PLOTLY_TEMPLATE
    )
    st.plotly_chart(fig_funnel, width="stretch")


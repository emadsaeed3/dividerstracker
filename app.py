"""
Launch Team Tracker - Main Application
Entry point for the Streamlit app
"""
import streamlit as st

# Page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="Launch Team Tracker",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'section' not in st.session_state:
    st.session_state.section = 'dividers'

# Load styles and components
from styles import load_css, inject_arrow_killer
from components import render_sidebar

# Apply styles
load_css()
inject_arrow_killer()

# Render sidebar and get the selected page
page = render_sidebar()

# Route to the selected page based on section
section = st.session_state.section

if section == 'dividers':
    from pages_app import dashboard, stores, vendor_stock, magnets, shipments, reports
    
    if "Dashboard" in page:
        dashboard.render()
    elif "Stores" in page:
        stores.render()
    elif "Vendor Stock" in page:
        vendor_stock.render()
    elif "Magnets" in page:
        magnets.render()
    elif "Shipments" in page:
        shipments.render()
    elif "Reports" in page:
        reports.render()

elif section == 'it':
    from pages_it import dashboard_it, rdcs, it_stock, it_shipments, it_reports
    
    if "Dashboard" in page:
        dashboard_it.render()
    elif "RDCs" in page:
        rdcs.render()
    elif "IT Stock" in page:
        it_stock.render()
    elif "Shipments" in page:
        it_shipments.render()
    elif "Reports" in page:
        it_reports.render()

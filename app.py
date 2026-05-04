"""
Dividers Tracker - Main Application
Entry point for the Streamlit app
"""
import streamlit as st

# Page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="Dividers Tracker",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Load styles and components
from styles import load_css, inject_arrow_killer
from components import render_sidebar
from pages_app import dashboard, stores, vendor_stock, magnets, shipments, reports

# Apply styles
load_css()
inject_arrow_killer()

# Render sidebar and get the selected page
page = render_sidebar()

# Route to the selected page
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

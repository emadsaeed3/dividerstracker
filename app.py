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
    st.session_state.section = None

# Load styles and components
from styles import load_css, inject_arrow_killer
from components import render_sidebar, get_logo_base64

# Apply styles
load_css()
inject_arrow_killer()

# Render sidebar and get the selected page
page = render_sidebar()

# Welcome screen if no section selected
if st.session_state.section is None:
    st.markdown("""
    <div style="text-align:center; padding:40px 20px 30px 20px;">
        <div style="font-size:3rem; margin-bottom:15px;">🚀</div>
        <div style="font-size:2.2rem; margin-bottom:10px; font-weight:800;">Welcome to Launch Team Tracker</div>
        <div style="font-size:1rem; opacity:0.75; margin-bottom:30px;">Choose a section to get started</div>
    </div>
    """, unsafe_allow_html=True)

    _, cc1, cc2, _ = st.columns([1, 2, 2, 1])

    with cc1:
        if st.button(
            "📦\n\n**Dividers**\n\nTrack dividers, magnets,\nstores & shipments",
            key="welcome_dividers",
            use_container_width=True
        ):
            st.session_state.section = 'dividers'
            st.rerun()

    with cc2:
        if st.button(
            "💻\n\n**4M IT Equipment**\n\nManage IT equipment\nfor all RDCs",
            key="welcome_it",
            use_container_width=True
        ):
            st.session_state.section = 'it'
            st.rerun()

else:
    # Route based on section
    section = st.session_state.section

    if section == 'dividers':
        from pages_app import (
            dashboard, stores, vendor_stock, magnets,
            shipments, action_items, progress_report, reports
        )

        if page is None or "Dashboard" in page:
            dashboard.render()
        elif "Stores" in page:
            stores.render()
        elif "Vendor Stock" in page:
            vendor_stock.render()
        elif "Magnets" in page:
            magnets.render()
        elif "Shipments" in page:
            shipments.render()
        elif "Action Items" in page:
            action_items.render()
        elif "Progress Report" in page:
            progress_report.render()
        elif "Reports" in page:
            reports.render()

    elif section == 'it':
        from pages_it import dashboard_it, rdcs, it_stock, it_shipments, it_reports

        if page is None or "Dashboard" in page:
            dashboard_it.render()
        elif "RDCs" in page:
            rdcs.render()
        elif "IT Stock" in page:
            it_stock.render()
        elif "Shipments" in page:
            it_shipments.render()
        elif "Reports" in page:
            it_reports.render()

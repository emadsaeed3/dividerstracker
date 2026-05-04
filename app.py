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
    logo_b64 = get_logo_base64()
    logo_html = ""
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width:220px; margin-bottom:20px;" />'
    
    st.markdown(f"""
    <div style="text-align:center; padding:60px 20px;">
        {logo_html}
        <h1 style="font-size:2.5rem; margin-bottom:10px;">Welcome to Launch Team Tracker</h1>
        <p style="font-size:1.1rem; opacity:0.75; margin-bottom:40px;">
            Select a section from the sidebar to get started
        </p>
        <div style="display:flex; justify-content:center; gap:30px; flex-wrap:wrap; margin-top:30px;">
            <div style="background: linear-gradient(135deg, rgba(52,152,219,0.1) 0%, rgba(52,152,219,0.05) 100%);
                        border: 2px solid rgba(52,152,219,0.3); padding:30px 40px; border-radius:16px; 
                        min-width:260px; box-shadow:0 4px 20px rgba(52,152,219,0.15);">
                <div style="font-size:3rem;">📦</div>
                <h3 style="margin:10px 0;">Dividers</h3>
                <p style="opacity:0.7; font-size:0.9rem;">Track dividers, magnets, stores and shipments</p>
            </div>
            <div style="background: linear-gradient(135deg, rgba(155,89,182,0.1) 0%, rgba(155,89,182,0.05) 100%);
                        border: 2px solid rgba(155,89,182,0.3); padding:30px 40px; border-radius:16px;
                        min-width:260px; box-shadow:0 4px 20px rgba(155,89,182,0.15);">
                <div style="font-size:3rem;">💻</div>
                <h3 style="margin:10px 0;">4M IT Equipment</h3>
                <p style="opacity:0.7; font-size:0.9rem;">Manage IT equipment for all RDCs</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Route based on section
    section = st.session_state.section
    
    if section == 'dividers':
        from pages_app import dashboard, stores, vendor_stock, magnets, shipments, reports
        
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

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

# Extra CSS for welcome cards
st.markdown("""
<style>
.welcome-container {
    text-align: center;
    padding: 30px 20px;
}
.welcome-logo {
    max-width: 140px;
    height: auto;
    margin-bottom: 20px;
}
.welcome-title {
    font-size: 2.2rem;
    margin-bottom: 10px;
    font-weight: 800;
}
.welcome-subtitle {
    font-size: 1rem;
    opacity: 0.75;
    margin-bottom: 30px;
}

/* Style the welcome section buttons */
.welcome-buttons button {
    height: 180px !important;
    font-size: 1.1rem !important;
    border-radius: 16px !important;
    font-weight: 700 !important;
    transition: all 0.3s ease !important;
}
.welcome-buttons button:hover {
    transform: translateY(-6px) !important;
    box-shadow: 0 12px 35px rgba(52, 152, 219, 0.4) !important;
}
</style>
""", unsafe_allow_html=True)

# Render sidebar and get the selected page
page = render_sidebar()

# Welcome screen if no section selected
if st.session_state.section is None:
    logo_b64 = get_logo_base64()
    logo_html = ""
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="welcome-logo" />'
    
    st.markdown(f"""
    <div class="welcome-container">
        {logo_html}
        <div class="welcome-title">Welcome to Launch Team Tracker</div>
        <div class="welcome-subtitle">Choose a section to get started</div>
    </div>
    """, unsafe_allow_html=True)

    # Clickable buttons
    st.markdown('<div class="welcome-buttons">', unsafe_allow_html=True)
    
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
    
    st.markdown('</div>', unsafe_allow_html=True)

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

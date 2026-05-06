"""Styles module - All CSS and theming"""
import streamlit as st
import streamlit.components.v1 as components


def get_theme_colors():
    """Get colors based on dark/light mode"""
    dark = st.session_state.get('dark_mode', False)

    if dark:
        return {
            'bg_primary': '#1a1d24',
            'bg_secondary': '#252932',
            'bg_tertiary': '#2d3139',
            'text_primary': '#e4e6eb',
            'text_secondary': '#b0b3b8',
            'text_muted': '#8a8d93',
            'sidebar_bg': 'linear-gradient(180deg, #0d1117 0%, #161b22 100%)',
            'border_color': '#3a3f4b',
            'input_bg': '#2d3139',
            'input_border': '#3a3f4b',
            'card_shadow': '0 4px 20px rgba(0,0,0,0.4)',
            'hover_shadow': '0 12px 35px rgba(0,0,0,0.6)',
            'alert_bg': 'rgba(255,255,255,0.03)',
        }
    else:
        return {
            'bg_primary': '#f5f7fa',
            'bg_secondary': '#ffffff',
            'bg_tertiary': '#f8f9fa',
            'text_primary': '#2c3e50',
            'text_secondary': '#7f8c8d',
            'text_muted': '#95a5a6',
            'sidebar_bg': 'linear-gradient(180deg, #1a2a3a 0%, #2c3e50 100%)',
            'border_color': '#ecf0f1',
            'input_bg': '#ffffff',
            'input_border': '#e0e4e8',
            'card_shadow': '0 4px 20px rgba(0,0,0,0.08)',
            'hover_shadow': '0 12px 35px rgba(0,0,0,0.15)',
            'alert_bg': 'rgba(0,0,0,0.02)',
        }


def get_plotly_theme():
    """Get Plotly theme based on dark/light mode"""
    if st.session_state.get('dark_mode', False):
        return dict(
            paper_bgcolor='#252932',
            plot_bgcolor='#252932',
            font=dict(color='#e4e6eb')
        )
    return dict(
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(color='#2c3e50')
    )


def load_css():
    """Load all CSS styles"""
    c = get_theme_colors()
    dark = st.session_state.get('dark_mode', False)

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    @import url('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css');
    
    * {{
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
    }}
    
    .stApp {{
        background: {c['bg_primary']};
    }}
    
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }}
    
    .stApp, .stApp p, .stApp label, .stApp span, .stMarkdown,
    .stApp div, .stApp li {{
        color: {c['text_primary']};
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}
    
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    button[kind="header"],
    button[kind="headerNoPadding"] {{
        display: none !important;
        visibility: hidden !important;
    }}
    
    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {{
        background: {c['sidebar_bg']};
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background: {c['sidebar_bg']};
        padding-top: 1rem;
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}
    [data-testid="stSidebar"] .stMarkdown h1 {{
        color: white !important;
        font-size: 1.4rem !important;
        padding-bottom: 0 !important;
        border: none !important;
        margin-bottom: 0 !important;
    }}
    [data-testid="stSidebar"] .stMarkdown h1::after {{
        display: none !important;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] {{
        gap: 8px;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] > label {{
        background: rgba(255,255,255,0.06);
        padding: 12px 16px !important;
        border-radius: 10px;
        margin: 0 !important;
        transition: all 0.3s ease;
        cursor: pointer;
        border-left: 3px solid transparent;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] > label:hover {{
        background: rgba(52, 152, 219, 0.2);
        border-left: 3px solid #3498db;
        transform: translateX(4px);
    }}
    [data-testid="stSidebar"] [role="radiogroup"] > label[data-checked="true"] {{
        background: linear-gradient(90deg, rgba(52, 152, 219, 0.3) 0%, rgba(52, 152, 219, 0.1) 100%);
        border-left: 3px solid #3498db;
    }}
    [data-testid="stSidebar"] button {{
        background: rgba(255,255,255,0.08) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 10px !important;
        transition: all 0.3s ease;
    }}
    [data-testid="stSidebar"] button:hover {{
        background: rgba(52, 152, 219, 0.3) !important;
        border-color: #3498db !important;
    }}
    [data-testid="stSidebar"] button[kind="primary"] {{
        background: linear-gradient(90deg, rgba(52, 152, 219, 0.4) 0%, rgba(52, 152, 219, 0.2) 100%) !important;
        border-color: #3498db !important;
    }}
    
    /* ===== HEADINGS ===== */
    h1 {{
        color: {c['text_primary']} !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
        position: relative;
        padding-bottom: 14px;
        margin-bottom: 28px !important;
        letter-spacing: -0.5px;
    }}
    h1::after {{
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 70px;
        height: 4px;
        background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
        border-radius: 10px;
    }}
    h2, h3, h4, h5, h6 {{
        color: {c['text_primary']} !important;
        font-weight: 700 !important;
    }}
    
    .section-title {{
        font-size: 1.3rem;
        font-weight: 700;
        color: {c['text_primary']};
        margin: 25px 0 15px 0;
        padding-left: 12px;
        border-left: 4px solid #3498db;
    }}
    
    /* ===== METRICS ===== */
    [data-testid="stMetric"] {{
        background: {c['bg_secondary']};
        padding: 22px;
        border-radius: 14px;
        box-shadow: {c['card_shadow']};
        border: 1px solid {c['border_color']};
        transition: all 0.3s ease;
        overflow: hidden;
        position: relative;
    }}
    [data-testid="stMetric"]:hover {{
        transform: translateY(-6px);
        box-shadow: {c['hover_shadow']};
    }}
    [data-testid="stMetric"]::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
    }}
    [data-testid="stMetricLabel"] {{
        color: {c['text_secondary']} !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }}
    [data-testid="stMetricValue"] {{
        color: {c['text_primary']} !important;
        font-weight: 800 !important;
        font-size: 38px !important;
        line-height: 1.2 !important;
    }}
    [data-testid="stMetricDelta"] {{
        color: {c['text_secondary']} !important;
    }}
    
    /* ===== BUTTONS ===== */
    .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
        border: none;
        padding: 11px 24px;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        letter-spacing: 0.3px;
        font-size: 0.95rem;
    }}
    .stButton > button {{
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        color: white !important;
        box-shadow: 0 4px 14px rgba(52, 152, 219, 0.35);
    }}
    .stButton > button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(52, 152, 219, 0.5);
    }}
    .stFormSubmitButton > button {{
        background: linear-gradient(135deg, #27ae60 0%, #229954 100%) !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(39, 174, 96, 0.35);
    }}
    .stFormSubmitButton > button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(39, 174, 96, 0.5);
    }}
    .stDownloadButton > button {{
        background: linear-gradient(135deg, #9b59b6 0%, #6c3483 100%) !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(155, 89, 182, 0.35);
    }}
    .stDownloadButton > button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(155, 89, 182, 0.5);
    }}
    
        /* ===== INPUTS ===== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stDateInput > div > div > input {{
        background: {c['input_bg']} !important;
        color: {c['text_primary']} !important;
        border-radius: 10px !important;
        border: 1.5px solid {c['input_border']} !important;
        padding: 11px 15px !important;
        font-size: 0.95rem !important;
    }}
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stDateInput > div > div > input:focus {{
        border-color: #3498db !important;
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15) !important;
    }}
    
    /* Placeholder text */
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder,
    .stNumberInput input::placeholder {{
        color: {c['text_muted']} !important;
        opacity: 0.7 !important;
    }}
    
    /* Text area specific */
    .stTextArea > div > div {{
        background: {c['input_bg']} !important;
    }}
    .stTextArea textarea {{
        background: {c['input_bg']} !important;
        color: {c['text_primary']} !important;
    }}
    
    /* Number input +/- buttons */
    .stNumberInput button {{
        background: {c['bg_tertiary']} !important;
        color: {c['text_primary']} !important;
        border-color: {c['input_border']} !important;
    }}
    .stNumberInput button:hover {{
        background: {c['border_color']} !important;
    }}
    .stNumberInput button svg {{
        fill: {c['text_primary']} !important;
    }}
    
    /* Date Input wrapper */
    .stDateInput > div > div {{
        background: {c['input_bg']} !important;
        border: 1.5px solid {c['input_border']} !important;
        border-radius: 10px !important;
    }}
    .stDateInput input {{
        background: {c['input_bg']} !important;
        color: {c['text_primary']} !important;
    }}
    
    /* Selectbox */
    .stSelectbox > div > div {{
        background: {c['input_bg']} !important;
        border-radius: 10px !important;
        border: 1.5px solid {c['input_border']} !important;
        color: {c['text_primary']} !important;
    }}
    .stSelectbox [data-baseweb="select"] > div {{
        background: {c['input_bg']} !important;
        color: {c['text_primary']} !important;
    }}
    .stSelectbox [data-baseweb="select"] span {{
        color: {c['text_primary']} !important;
    }}
    
    /* Selectbox dropdown menu (when opened) */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"] {{
        background: {c['bg_secondary']} !important;
        color: {c['text_primary']} !important;
        border: 1px solid {c['border_color']} !important;
    }}
    [role="option"],
    [data-baseweb="menu"] li,
    [data-baseweb="menu"] [role="option"] {{
        background: {c['bg_secondary']} !important;
        color: {c['text_primary']} !important;
    }}
    [role="option"]:hover,
    [data-baseweb="menu"] li:hover {{
        background: {c['bg_tertiary']} !important;
        color: {c['text_primary']} !important;
    }}
    [aria-selected="true"][role="option"] {{
        background: rgba(52, 152, 219, 0.2) !important;
        color: {c['text_primary']} !important;
    }}
    
    /* Date picker calendar */
    [data-baseweb="calendar"] {{
        background: {c['bg_secondary']} !important;
        color: {c['text_primary']} !important;
        border: 1px solid {c['border_color']} !important;
    }}
    [data-baseweb="calendar"] * {{
        color: {c['text_primary']} !important;
    }}
    [data-baseweb="calendar"] button {{
        background: transparent !important;
        color: {c['text_primary']} !important;
    }}
    [data-baseweb="calendar"] button:hover {{
        background: {c['bg_tertiary']} !important;
    }}
    [data-baseweb="calendar"] [aria-selected="true"] {{
        background: #3498db !important;
        color: white !important;
    }}
    [data-baseweb="popover"] [data-baseweb="calendar"] {{
        background: {c['bg_secondary']} !important;
    }}
    
    /* Calendar header (month/year) */
    [data-baseweb="calendar"] [data-baseweb="calendar-header"] {{
        background: {c['bg_secondary']} !important;
        color: {c['text_primary']} !important;
    }}
    
    /* Date input popup */
    div[data-baseweb="popover"] > div {{
        background: {c['bg_secondary']} !important;
        color: {c['text_primary']} !important;
    }}
    
    /* Checkboxes */
    .stCheckbox label {{
        color: {c['text_primary']} !important;
    }}
    .stCheckbox label span {{
        color: {c['text_primary']} !important;
    }}
    .stCheckbox [data-baseweb="checkbox"] > div {{
        background: {c['input_bg']} !important;
        border-color: {c['input_border']} !important;
    }}
    
    /* Radio */
    .stRadio label {{
        color: {c['text_primary']} !important;
    }}
    .stRadio label span {{
        color: {c['text_primary']} !important;
    }}
    
    /* Form labels */
    label[data-testid="stWidgetLabel"],
    label[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] div {{
        color: {c['text_primary']} !important;
    }}
    
    /* Slider (if used) */
    .stSlider [data-baseweb="slider"] {{
        background: {c['input_bg']} !important;
    }}
    
    /* File uploader */
    [data-testid="stFileUploader"] section {{
        background: {c['input_bg']} !important;
        border: 2px dashed {c['input_border']} !important;
        color: {c['text_primary']} !important;
    }}
    [data-testid="stFileUploader"] section button {{
        background: {c['bg_tertiary']} !important;
        color: {c['text_primary']} !important;
    }}
    
    /* ===== EXPANDERS ===== */
    [data-testid="stExpander"] {{
        background: {c['bg_secondary']};
        border: 1px solid {c['border_color']};
        border-radius: 12px;
        box-shadow: {c['card_shadow']};
        margin-bottom: 14px;
        overflow: hidden;
    }}
    [data-testid="stExpander"] summary {{
        color: {c['text_primary']} !important;
    }}
    [data-testid="stExpander"] summary p {{
        color: {c['text_primary']} !important;
    }}
    .streamlit-expanderHeader {{
        font-weight: 600 !important;
        color: {c['text_primary']} !important;
        padding: 14px 18px !important;
        font-size: 1rem !important;
    }}
    [data-testid="stExpander"] div[data-testid="stExpanderDetails"] {{
        background: {c['bg_secondary']};
    }}
    
    /* ===== FORMS ===== */
    [data-testid="stForm"] {{
        background: {c['bg_secondary']};
        padding: 28px;
        border-radius: 14px;
        border: 1px solid {c['border_color']};
        box-shadow: {c['card_shadow']};
    }}
    
    /* ===== DATAFRAMES / TABLES ===== */
    [data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
        box-shadow: {c['card_shadow']};
        border: 1px solid {c['border_color']};
        background: {c['bg_secondary']};
    }}
    [data-testid="stDataFrame"] thead tr th {{
        background: linear-gradient(90deg, #2c3e50 0%, #34495e 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.8rem !important;
    }}
    [data-testid="stDataFrame"] tbody tr td {{
        color: {c['text_primary']} !important;
        background: {c['bg_secondary']};
    }}
    [data-testid="stDataFrame"] tbody tr:hover td {{
        background: {c['bg_tertiary']} !important;
    }}
    
    /* ===== ALERTS ===== */
    [data-testid="stAlert"] {{
        border-radius: 12px !important;
        padding: 16px 22px !important;
        font-weight: 500 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        border-left: 5px solid !important;
    }}
    [data-testid="stAlert"] div {{
        color: {c['text_primary']} !important;
    }}
    
    /* ===== STAT CARDS ===== */
    .stat-card {{
        background: {c['bg_secondary']};
        padding: 24px;
        border-radius: 14px;
        box-shadow: {c['card_shadow']};
        border: 1px solid {c['border_color']};
        margin-bottom: 16px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }}
    .stat-card:hover {{
        transform: translateY(-6px);
        box-shadow: {c['hover_shadow']};
    }}
    .stat-card .icon-bg {{
        position: absolute;
        top: 12px;
        right: 16px;
        font-size: 3.5rem;
        opacity: 0.12;
    }}
    .stat-card .stat-label {{
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: {c['text_secondary']};
        font-weight: 700;
        margin-bottom: 8px;
    }}
    .stat-card .stat-value {{
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.1;
        color: {c['text_primary']};
    }}
    
    .card-30d {{
        border-left: 5px solid #3498db;
        background: linear-gradient(135deg, {c['bg_secondary']} 0%, rgba(52, 152, 219, 0.08) 100%);
    }}
    .card-30d .icon-bg {{ color: #3498db; }}
    .card-30d .stat-value {{ color: #3498db; }}
    
    .card-40d {{
        border-left: 5px solid #e67e22;
        background: linear-gradient(135deg, {c['bg_secondary']} 0%, rgba(230, 126, 34, 0.08) 100%);
    }}
    .card-40d .icon-bg {{ color: #e67e22; }}
    .card-40d .stat-value {{ color: #e67e22; }}
    
    .card-60d {{
        border-left: 5px solid #9b59b6;
        background: linear-gradient(135deg, {c['bg_secondary']} 0%, rgba(155, 89, 182, 0.08) 100%);
    }}
    .card-60d .icon-bg {{ color: #9b59b6; }}
    .card-60d .stat-value {{ color: #9b59b6; }}
    
    .card-stores {{
        border-left: 5px solid #3498db;
    }}
    .card-stores .icon-bg {{ color: #3498db; }}
    .card-stores .stat-value {{ color: {c['text_primary']}; }}
    
    .card-shipments {{
        border-left: 5px solid #27ae60;
    }}
    .card-shipments .icon-bg {{ color: #27ae60; }}
    .card-shipments .stat-value {{ color: {c['text_primary']}; }}
    
    /* ===== BADGES ===== */
    .badge-stock {{
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        margin-top: 12px;
    }}
    .badge-danger {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; }}
    .badge-warning {{ background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); color: white; }}
    .badge-success {{ background: linear-gradient(135deg, #27ae60 0%, #229954 100%); color: white; }}
    
    .progress-container {{
        background: {c['border_color']};
        border-radius: 20px;
        overflow: hidden;
        height: 10px;
        margin-top: 12px;
    }}
    .progress-fill {{
        height: 100%;
        border-radius: 20px;
        transition: width 0.8s ease;
    }}
    
    .threshold-chip {{
        display: inline-block;
        background: linear-gradient(135deg, #7f8c8d 0%, #636e72 100%);
        color: white;
        padding: 8px 18px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }}
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: {c['bg_secondary']};
        padding: 6px;
        border-radius: 12px;
        border: 1px solid {c['border_color']};
    }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        color: {c['text_primary']} !important;
        border-radius: 8px;
        padding: 8px 16px;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%) !important;
        color: white !important;
    }}
    
    /* ===== CAPTION ===== */
    [data-testid="stCaptionContainer"] {{
        color: {c['text_secondary']} !important;
    }}
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
    ::-webkit-scrollbar-track {{ background: {c['bg_primary']}; }}
    ::-webkit-scrollbar-thumb {{ 
        background: linear-gradient(180deg, #3498db 0%, #2980b9 100%);
        border-radius: 10px;
    }}
    
    hr {{
        border: none;
        height: 1px;
        background: {c['border_color']};
        margin: 24px 0;
    }}
    
    /* ===== DIALOGS / MODALS ===== */
    [data-testid="stDialog"] {{
        background: {c['bg_secondary']};
        color: {c['text_primary']};
    }}
    
    /* ===== CODE BLOCKS ===== */
    code {{
        background: {c['bg_tertiary']} !important;
        color: {c['text_primary']} !important;
        padding: 2px 6px;
        border-radius: 4px;
    }}
    
    /* Ensure all text is readable */
    .stMarkdown strong, .stMarkdown b {{
        color: {c['text_primary']} !important;
    }}
    </style>
    
    <script>
    function removeArrowText() {{
        const walker = document.createTreeWalker(
            document.body, NodeFilter.SHOW_TEXT, null, false
        );
        const nodesToRemove = [];
        let node;
        while (node = walker.nextNode()) {{
            const text = node.nodeValue;
            if (text && (
                text.includes('_arrow_right') || 
                text.includes('_arrow_left') ||
                text.includes('keyboard_double_arrow') ||
                text.includes('keyboard_arrow')
            )) {{
                nodesToRemove.push(node);
            }}
        }}
        nodesToRemove.forEach(n => n.nodeValue = '');
    }}
    removeArrowText();
    setInterval(removeArrowText, 100);
    const observer = new MutationObserver(removeArrowText);
    observer.observe(document.body, {{ childList: true, subtree: true, characterData: true }});
    </script>
    """
    st.markdown(css, unsafe_allow_html=True)


def inject_arrow_killer():
    components.html("""
    <script>
    function killArrowText() {
        const parentDoc = window.parent.document;
        const walker = parentDoc.createTreeWalker(
            parentDoc.body, NodeFilter.SHOW_TEXT, null, false
        );
        let node;
        const toRemove = [];
        while (node = walker.nextNode()) {
            if (node.nodeValue && (
                node.nodeValue.includes('_arrow') ||
                node.nodeValue.includes('keyboard_') ||
                node.nodeValue.includes('arrow_right') ||
                node.nodeValue.includes('arrow_left')
            )) {
                toRemove.push(node);
            }
        }
        toRemove.forEach(n => n.nodeValue = '');
    }
    killArrowText();
    setInterval(killArrowText, 100);
    const obs = new MutationObserver(killArrowText);
    obs.observe(window.parent.document.body, {
        childList: true, subtree: true, characterData: true
    });
    </script>
    """, height=0)

def get_app_styles(cal_palette, font_size):
    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    
    html, body, [class*="css"], .stApp, .stMarkdown p, label p, button p {{
        font-size: {font_size} !important; 
    }}
    
    .stApp {{
        background-color: {cal_palette["bg_body"]};
        color: {cal_palette["text_main"]};
        animation: fadeIn 0.4s ease-in-out;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(4px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    header[data-testid="stHeader"] {{ display: none !important; }}
    #MainMenu, footer {{ visibility: hidden !important; }}
    
    .block-container {{
        padding-top: 0.2rem !important;
        padding-bottom: 1rem !important;
        max-width: 99% !important;
    }}
    
    div.element-container {{
        margin-bottom: -0.3rem !important;
    }}

    label[data-testid="stWidgetLabel"] p, label p, .stMarkdown p {{
        color: {cal_palette["text_main"]} !important;
        font-weight: 700 !important;
        margin-bottom: 2px !important;
    }}

    .brand-container {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 0;
        white-space: nowrap;
    }}
    .brand-title {{
        font-size: 1.35rem;
        font-weight: 800;
        color: {cal_palette["text_main"]};
    }}

    div[data-baseweb="input"],
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"],
    div[data-baseweb="base-input"] > div,
    [data-testid="stTextInput"] div,
    [data-testid="stDateInput"] div,
    [data-testid="stNumberInput"] div {{
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border-radius: 8px !important;
        border: 1.5px solid #CBD5E1 !important;
    }}
    
    input[type="text"], input[type="password"], input[type="number"], input {{
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 700 !important;
        font-size: {font_size} !important;
    }}
    
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="base-input"]:focus-within {{
        border-color: {cal_palette["accent"]} !important;
        box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2) !important;
    }}

    div[data-testid="stFileUploader"] > section {{
        background-color: #FFFFFF !important;
        border: 1.5px dashed #94A3B8 !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }}
    div[data-testid="stFileUploader"] * {{
        color: #0F172A !important;
    }}

    div[data-testid="stPopoverBody"] {{
        background-color: #FFFFFF !important;
        border: 1.5px solid #94A3B8 !important;
        border-radius: 10px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15) !important;
    }}
    div[data-testid="stPopoverBody"] * {{
        color: #0F172A !important;
        font-size: {font_size} !important;
    }}

    [data-testid="stExpander"] summary {{
        background-color: {cal_palette["card_bg"]} !important; 
        border: 1px solid {cal_palette["border"]} !important;
        border-radius: 10px !important;
        box-shadow: {cal_palette["shadow"]} !important;
        padding: 0.5rem 0.9rem !important;
    }}
    [data-testid="stExpander"] summary p, 
    [data-testid="stExpander"] summary span {{
        color: {cal_palette["card_text"]} !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }}

    button[kind="secondary"] {{
        background-color: {cal_palette["card_bg"]} !important;
        border: 1.5px solid {cal_palette["border"]} !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 0.45rem 0.9rem !important;
        box-shadow: {cal_palette["shadow"]} !important;
    }}
    button[kind="secondary"] p, button[kind="secondary"] div, button[kind="secondary"] span {{
        color: {cal_palette["card_text"]} !important;
        font-weight: 700 !important;
        font-size: {font_size} !important;
    }}

    button[kind="primary"] {{
        background: linear-gradient(135deg, {cal_palette["accent"]} 0%, #004D99 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 0.45rem 0.9rem !important;
        box-shadow: 0 4px 14px rgba(0, 102, 204, 0.3) !important;
    }}
    button[kind="primary"] p, button[kind="primary"] div, button[kind="primary"] span {{
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: {font_size} !important;
    }}
    
    .shift-staff-tile {{
        background-color: {cal_palette["card_bg"]};
        color: {cal_palette["card_text"]};
        padding: 12px 16px;
        border-radius: 12px;
        border: 1px solid {cal_palette["border"]};
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 14px;
        box-shadow: {cal_palette["shadow"]};
    }}
    .avatar-img {{
        width: 56px; height: 56px; border-radius: 50%; object-fit: cover; border: 2.5px solid {cal_palette["accent"]};
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }}
    .shift-header-box {{
        background: {cal_palette["bg_surface"]};
        padding: 10px 14px;
        border-radius: 10px;
        border: 1px solid {cal_palette["border"]};
        border-left: 5px solid {cal_palette["accent"]};
        margin-bottom: 8px;
        box-shadow: {cal_palette["shadow"]};
    }}
    .shift-title {{
        font-size: 1.1rem;
        font-weight: 800;
        color: {cal_palette["text_main"]};
        margin: 0;
    }}
    .shift-time {{
        font-size: 0.85rem;
        font-weight: 700;
        color: {cal_palette["accent"]};
        margin-top: 2px;
    }}
    .banner-wrapper {{
        width: 100%; border-radius: 12px; overflow: hidden;
        border: 1px solid {cal_palette["border"]}; margin-bottom: 0.8rem;
        box-shadow: {cal_palette["shadow"]};
    }}
    .banner-default {{
        width: 100%; min-height: 90px;
        background: linear-gradient(135deg, #0A192F 0%, #004D99 50%, {cal_palette["accent"]} 100%);
        display: flex; flex-direction: column; justify-content: center; padding: 14px 22px; color: #FFFFFF;
    }}
</style>
"""
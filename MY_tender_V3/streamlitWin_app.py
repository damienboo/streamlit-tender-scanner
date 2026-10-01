import streamlit as st
import pandas as pd
import time
import os
import re
import database
import asyncio
import sys
import io
import concurrent.futures

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def filter_exact_matches(tenders, keyword_string):
    if not tenders: return []
    search_terms = [k.strip().lower() for k in keyword_string.split(",")]
    valid_tenders = []
    for tender in tenders:
        title = tender.get('Title', tender.get('Tender Title', '')).lower()
        is_valid = False
        for term in search_terms:
            pattern = rf"(^|[^a-z0-9]){re.escape(term)}([^a-z0-9]|$)"
            if re.search(pattern, title):
                is_valid = True
                break
        if is_valid:
            valid_tenders.append(tender)
    return valid_tenders

st.set_page_config(page_title="MY-Tender Tracker", layout="wide", page_icon="🏢")

st.markdown("""
<style>
    .top-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;}
    .title-area h1 { margin: 0; font-family: 'Arial', sans-serif; font-size: 28px; font-weight: 700; }
    .title-area p { margin: 0; font-size: 14px; opacity: 0.7; }
    
    .header-tags span { background-color: #e2e8f0; color: #334155 !important; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-right: 8px; letter-spacing: 0.5px; }
    .header-tags .tag-blue { background-color: #dbeafe; color: #1e40af !important; }
    
    .tender-card {
        background-color: white !important; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: box-shadow 0.2s; height: 100%; display: flex; flex-direction: column;
    }
    .tender-card:hover { box-shadow: 0 4px 6px rgba(0,0,0,0.08); border-color: #cbd5e1; }
    
    .card-header { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 11px; font-weight: 700; }
    .category-tag { background-color: #eff6ff !important; color: #1d4ed8 !important; padding: 4px 8px; border-radius: 4px; }
    .budget-tag { color: #16a34a !important; text-align: right; }
    
    .card-title { font-size: 16px; font-weight: 700; color: #0f172a !important; margin: 0 0 12px 0; line-height: 1.4; }
    .card-agency { color: #475569 !important; font-size: 13px; margin-bottom: 12px; display: flex; align-items: center; gap: 6px; font-weight: 600;}
    
    .card-footer { 
        display: flex; justify-content: space-between; align-items: center; 
        border-top: 1px dashed #e2e8f0; padding-top: 16px; margin-top: auto; margin-bottom: 16px;
    }
    .status-col { display: flex; flex-direction: column; gap: 4px; }
    .status-label { font-size: 10px; color: #94a3b8 !important; font-weight: 600; text-transform: uppercase; }
    .status-value-open { color: #16a34a !important; font-size: 13px; font-weight: 600; }
    .status-value-date { color: #dc2626 !important; font-size: 13px; font-weight: 600; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { font-weight: bold; font-size: 16px; }
</style>  
""", unsafe_allow_html=True)

from scrapers.eperolehan import scrape_live_eperolehan
from scrapers.selangor import scrape_selangor
from scrapers.johor import scrape_johor
from scrapers.kedah import scrape_kedah
from scrapers.melaka import scrape_melaka
from scrapers.pahang import scrape_pahang
from scrapers.kelantan import scrape_kelantan
from scrapers.negerisembilan import scrape_negeri_sembilan
from scrapers.penang import scrape_penang
from scrapers.perak import scrape_perak
from scrapers.perlis import scrape_perlis
from scrapers.terengganu import scrape_terengganu
from scrapers.sabah import scrape_sabah
from scrapers.sarawak import scrape_sarawak

def render_tender_cards(data, search_term, scope_name):
    if data and len(data) > 0:
        df = pd.DataFrame(data)
        
        m1, m2 = st.columns(2)
        m1.metric(f"Opportunities Discovered ({scope_name})", len(data))
        m2.metric("Search Scope", scope_name)
        st.divider()
        
        cols = st.columns(2)
        for index, item in enumerate(data):
            col = cols[index % 2]
            with col:
                title = item.get('Title', item.get('Tender Title', 'Untitled Notice'))
                agency = item.get('Agency', 'Unknown Agency')
                closing = item.get('Closing Date', 'TBA')
                source = item.get('Source', scope_name)
                link_url = item.get('Link', '#') 
                
                card_html = f"""
                <div class="tender-card">
                    <div class="card-header">
                        <span class="category-tag">{source}</span>
                        <span class="budget-tag">Active Notice</span>
                    </div>
                    <h3 class="card-title">{title}</h3>
                    <div class="card-agency">🏛️ {agency}</div>
                    <div class="card-footer">
                        <div class="status-col">
                            <span class="status-label">STATUS</span>
                            <span class="status-value-open">● OPEN</span>
                        </div>
                        <div class="status-col">
                            <span class="status-label">CLOSING DATE</span>
                            <span class="status-value-date">🕒 {closing}</span>
                        </div>
                    </div>
                    <a href="{link_url}" target="_blank" style="display: block; text-align: center; background-color: #2563eb; color: white; padding: 8px; border-radius: 4px; text-decoration: none; margin-top: 10px; font-weight: bold;">
                        🔗 View Official Tender
                    </a>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
        
        st.divider()
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(f"📥 Download {scope_name} Report", csv, f"Tender_Results_{scope_name}_{search_term}.csv", "text/csv")
    else:
        st.warning(f"No open {scope_name} tenders found matching '{search_term}' today.")

def expand_keywords(user_input):
    bilingual_dict = {
        "network": "rangkaian",
        "rangkaian": "network",
        "server": "pelayan",
        "pelayan": "server",
        "computer": "komputer",
        "komputer": "computer",
        "software": "perisian",
        "perisian": "software",
        "hardware": "perkakasan",
        "perkakasan": "hardware",
        "maintenance": "penyelenggaraan",
        "penyelenggaraan": "maintenance",
        "service": "perkhidmatan",
        "perkhidmatan": "service",
        "supply": "bekalan",
        "bekalan": "supply",
        "switch": "suis",
        "suis": "switch",
        "router": "penghala",
        "penghala": "router",
        "ict": "tmk", 
        "tmk": "ict"
    }
    
    expanded_terms = set()
    input_terms = [k.strip().lower() for k in user_input.split(",")]
    
    for term in input_terms:
        expanded_terms.add(term) 
        if term in bilingual_dict:
            expanded_terms.add(bilingual_dict[term]) 
            
    return ", ".join(expanded_terms)

st.markdown("""
<div class="top-header">
    <div class="title-area">
        <h1>MY-Tender Tracker</h1>
        <p>MALAYSIAN PROCUREMENT INTELLIGENCE</p>
    </div>
    <div style="text-align: right; opacity: 0.7;">
        <span style="font-size: 12px; font-weight: 500; color: #94a3b8;">Prototype Developed By</span><br>
        <strong style="font-size: 15px; color: #f8fafc; letter-spacing: 0.5px;">Damien (Intern)</strong>
    </div>
</div>
<div class="header-tags" style="margin-bottom: 20px;">
    <span class="tag-blue">PARALLEL SCRAPING ENGINE (WINDOWS)</span>
    <span>NO API LIMITS</span>
</div>
<h2 style="font-size: 22px; color: #ffffff; margin-bottom: 5px;">Enterprise & Public Tech Intelligence</h2>
<p style="color: #64748b; font-size: 14px; margin-bottom: 25px;">Monitoring live tenders directly from government portals.</p>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🏛️ Federal Tenders", "🏢 State Tenders", "📂 Local Database (History)"])

with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        fed_keyword = st.text_input("Enter Keyword:", value="Perkhidmatan", key="fed_search")
    with col2:
        st.write("")
        st.write("")
        run_fed = st.button("🚀 Scan Federal", width="stretch")

    if run_fed:
        if not fed_keyword:
            st.warning("Please enter a keyword")
        else:
            with st.spinner("Connecting to ePerolehan database..."):
                try:
                    data = scrape_live_eperolehan(fed_keyword)
                    data = filter_exact_matches(data, fed_keyword)
                    
                    new_tenders_found = False
                    for tender in data:
                        is_new = database.insert_tender(tender)
                        if is_new:
                            new_tenders_found = True
                            agency = tender.get('Agency', 'Unknown Agency')
                            c_date = tender.get('Closing Date', 'Unknown Date')
                            st.toast(f"🚨 New Federal tender by {agency} closing on {c_date}", icon="🏛️")
                            time.sleep(0.5) 
                    
                    if not new_tenders_found and len(data) > 0:
                        st.toast("No new Federal tenders found in this run.", icon="ℹ️")
                    
                    render_tender_cards(data, fed_keyword, "Federal")
                except Exception as e:
                    st.error(f"System Error: {e}")

with tab2:
    col3, col4 = st.columns([3, 1])
    with col3:
        state_keyword = st.text_input("Enter Keyword:", value="Perkhidmatan", key="state_search")
    with col4:
        st.write("")
        st.write("")
        run_state = st.button("🚀 Scan States (Parallel)", width="stretch")

    if run_state:
        if not state_keyword:
            st.warning("Please enter a keyword")
        else:
            expanded_keyword = expand_keywords(state_keyword)
            st.info(f"🧠 Auto-expanded search terms: **{expanded_keyword}**")
            
            state_results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.info("🚀 Launching Parallel Scanning Engine (High Speed Mode)...")

            state_scrapers = [
                ("Selangor", scrape_selangor), ("Kedah", scrape_kedah), 
                ("Johor", scrape_johor), ("Kelantan", scrape_kelantan),
                ("Melaka", scrape_melaka), ("Negeri Sembilan", scrape_negeri_sembilan),
                ("Pahang", scrape_pahang), ("Penang", scrape_penang), 
                ("Perak", scrape_perak), ("Perlis", scrape_perlis), 
                ("Terengganu", scrape_terengganu), ("Sabah", scrape_sabah), 
                ("Sarawak", scrape_sarawak)
            ]

            # 🔥 THE THREAD POOL ENGINE (High Speed Mode) 🔥
            with concurrent.futures.ThreadPoolExecutor(max_workers=13) as executor:
                future_to_state = {executor.submit(func, expanded_keyword): name for name, func in state_scrapers}
                
                completed = 0
                for future in concurrent.futures.as_completed(future_to_state):
                    state_name = future_to_state[future]
                    try:
                        data = future.result()
                        if data:
                            state_results.extend(data)
                        
                        completed += 1
                        progress = int((completed / 13) * 100)
                        progress_bar.progress(progress)
                        status_text.info(f"✅ {state_name} completed! ({completed}/13)")
                    except Exception as e:
                        st.error(f"{state_name} Error: {e}")
                        completed += 1
                        progress = int((completed / 13) * 100)
                        progress_bar.progress(progress)
            
            status_text.success("✅ State Scanning Complete!")
            
            state_results = filter_exact_matches(state_results, expanded_keyword)
            
            new_tenders_found = False
            for tender in state_results:
                is_new = database.insert_tender(tender)
                
                if is_new:
                    new_tenders_found = True
                    agency = tender.get('Agency', 'Unknown Agency')
                    c_date = tender.get('Closing Date', 'Unknown Date')
                    st.toast(f"🚨 New tender by {agency} closing on {c_date}", icon="🏢")
                    time.sleep(0.5) 
            
            if not new_tenders_found and len(state_results) > 0:
                st.toast("No new state tenders found in this run.", icon="ℹ️")
                
            render_tender_cards(state_results, expanded_keyword, "State")

with tab3:
    st.markdown("### 📂 Discovered Tenders Database")
    st.write("This shows every tender your background monitor has ever saved to the SQL database.")
    
    history_data = database.fetch_all_tenders()
    
    if history_data:
        df_history = pd.DataFrame(history_data)
        
        filter_option = st.radio(
            "Filter Database View:", 
            ["🏢 All Tenders", "🏛️ Federal Only", "🏬 State Only"], 
            horizontal=True
        )
        
        if filter_option == "🏛️ Federal Only":
            df_display = df_history[df_history['Source'].str.contains("Federal", case=False, na=False)]
        elif filter_option == "🏬 State Only":
            df_display = df_history[~df_history['Source'].str.contains("Federal", case=False, na=False)]
        else:
            df_display = df_history
            
        st.dataframe(df_display, width="stretch", hide_index=True)
        
        excel_buffer = io.BytesIO()
        
        team_accounts = {
            "Aznizan": ["Health", "Kesihatan", "MOH", "NRES", "PETRA", "DBKL", "Kuala Lumpur", "Insolvensi"],
            "Fifiy": ["JKR", "Kerja Raya", "Transport", "Pengangkutan", "DOSM", "AGC", "Pertanian", "MAFS"],
            "Fiza": ["University Malaya", "UM", "UPSI", "Pendidikan Sultan Idris", "FELDA"],
            "Razi": ["UPM", "UMK", "UMT", "Sultan Zainal Abidin", "UNISZA", "Pahang", "Perlis"],
            "Ashraf": ["MOSTI", "MINDEF", "Pertahanan", "TM", "Telekom", "Tenaga Nasional"],
            "Faiz": ["Immigration", "Imigresen", "Pendaftaran", "KDN", "Kewangan", "MOF"]
        }
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_display.to_excel(writer, sheet_name="ALL", index=False)
            
            for member, keywords in team_accounts.items():
                pattern = '|'.join([rf"\b{k}\b" for k in keywords])
                member_df = df_display[df_display['Agency'].str.contains(pattern, case=False, na=False, regex=True)]
                
                if not member_df.empty:
                    member_df.to_excel(writer, sheet_name=member, index=False)
                    
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📥 Download Key Accounts Report (Excel)", 
            data=excel_data, 
            file_name="Tender_Key_Accounts_Delegation.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No tenders have been saved to the SQL database yet.")
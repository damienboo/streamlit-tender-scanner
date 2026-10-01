import sqlite3
import os
import csv
import pandas as pd

DB_FILE = "tender_data.db"

def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS official_tenders (
            title TEXT,
            agency TEXT,
            closing_date TEXT,
            source TEXT,
            link TEXT,
            UNIQUE(title, agency)
        )
    ''')
    conn.commit()
    conn.close()

def fetch_all_tenders():
    if not os.path.exists(DB_FILE):
        initialize_database()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT title as Title, agency as Agency, closing_date as 'Closing Date', source as Source, link as Link FROM official_tenders")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def insert_tender(tender):
    initialize_database()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    is_new = False
    try:
        cursor.execute('''
            INSERT INTO official_tenders (title, agency, closing_date, source, link)
            VALUES (?, ?, ?, ?, ?)
        ''', (tender.get('Title', 'Unknown'), tender.get('Agency', 'Unknown'), tender.get('Closing Date', 'Unknown'), tender.get('Source', 'Unknown'), tender.get('Link', '')))
        conn.commit()
        is_new = True
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return is_new

def export_to_excel_team_report():
    """Exports the SQL database to a multi-tab Excel file for the team."""
    tenders = fetch_all_tenders()
    if not tenders:
        return None
        
    df = pd.DataFrame(tenders)
    excel_filename = "Tender_Team_Delegation.xlsx"
    
    team_accounts = {
        "Aznizan": ["Health", "Kesihatan", "MOH", "NRES", "PETRA", "DBKL", "Kuala Lumpur", "Insolvensi"],
        "Fifiy": ["JKR", "Kerja Raya", "Transport", "Pengangkutan", "DOSM", "AGC", "Pertanian", "MAFS"],
        "Fiza": ["University Malaya", "UM", "UPSI", "Pendidikan Sultan Idris", "FELDA"],
        "Razi": ["UPM", "UMK", "UMT", "Sultan Zainal Abidin", "UNISZA", "Pahang", "Perlis"],
        "Ashraf": ["MOSTI", "MINDEF", "Pertahanan", "TM", "Telekom", "Tenaga Nasional"],
        "Faiz": ["Immigration", "Imigresen", "Pendaftaran", "KDN", "Kewangan", "MOF"]
    }

    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="ALL", index=False)
        
        for member, keywords in team_accounts.items():
            pattern = '|'.join([rf"\b{k}\b" for k in keywords])
            member_df = df[df['Agency'].str.contains(pattern, case=False, na=False, regex=True)]
            if not member_df.empty:
                member_df.to_excel(writer, sheet_name=member, index=False)
                
    return excel_filename
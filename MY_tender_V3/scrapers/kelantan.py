from playwright.sync_api import sync_playwright
import re

def scrape_kelantan(keyword):
    results = []
    print(f"Starting scrape for Kelantan PTG (Keywords: '{keyword}')...")
    
    search_terms = [k.strip().lower() for k in keyword.split(",")]
    seen_titles = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            url = "https://ptg.kelantan.gov.my/index.php/ms/penerbitan/iklan-dan-tender"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            try:
                page.wait_for_selector("tr.docman_item", timeout=15000)
            except Exception:
                print(f"ℹ️ No tender documents found or table empty for Kelantan.")
                return results
                
            rows = page.query_selector_all("tr.docman_item")
            
            for term in search_terms:
                print(f"🔍 Filtering Kelantan PTG for: '{term}'")
                
                for row in rows:
                    title_el = row.query_selector('span[itemprop="name"]')
                    date_el = row.query_selector('time[itemprop="datePublished"]')
                    
                    if not title_el: 
                        continue
                        
                    clean_title = title_el.text_content().strip()
                    title_lower = clean_title.lower()
                    
                    if term in title_lower and clean_title not in seen_titles:
                        seen_titles.add(clean_title)
                        
                        published_date = date_el.text_content().strip() if date_el else "Unknown"
                        display_date = f"Iklan: {published_date} (Sila Rujuk PDF)"
                        
                        link_el = row.query_selector("a")
                        if link_el:
                            href = link_el.get_attribute("href")
                            if href:
                                if href.startswith("http"):
                                    pdf_link = href
                                else:
                                    slash = "" if href.startswith("/") else "/"
                                    pdf_link = f"https://ptg.kelantan.gov.my{slash}{href}"
                            else:
                                pdf_link = url
                        else:
                            pdf_link = url
                            
                        results.append({
                            "Title": clean_title,
                            "Agency": "Pejabat Pengarah Tanah Dan Galian (PTG) Kelantan",
                            "Closing Date": display_date,
                            "Source": "Kelantan (PTG)",
                            "Link": pdf_link 
                        })
                        print(f"✅ [ADDED] {clean_title[:60]}...")

        except Exception as e: 
            print(f"Kelantan PTG Scraping Error: {e}")
            
        finally: 
            browser.close()
            
    return results
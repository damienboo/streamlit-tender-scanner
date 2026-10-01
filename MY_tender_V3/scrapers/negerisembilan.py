from playwright.sync_api import sync_playwright
import re

def scrape_negeri_sembilan(keyword):
    results = []
    print(f"Starting scrape for Negeri Sembilan (Keywords: '{keyword}')...")
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
            url = "https://jknns.moh.gov.my/sebutharga"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            try:
                limit_select = page.locator("select#limit")
                if limit_select.count() > 0:
                    current_val = limit_select.evaluate("el => el.value")
                    if current_val != "0":
                        print("⏳ Forcing table to display 'All' results on one page...")
                        limit_select.select_option("0")
                        page.wait_for_timeout(3000) 
            except Exception:
                pass
            
            try:
                page.wait_for_selector(".pd-cdesc table tbody tr", timeout=20000)
            except Exception:
                print(f"ℹ️ No active tenders found or page empty for Negeri Sembilan.")
                return results
            
            rows = page.query_selector_all(".pd-cdesc table tbody tr")
            print(f"Found {len(rows)} tender rows in Negeri Sembilan portal.")
            
            for term in search_terms:
                print(f"🔍 Filtering Negeri Sembilan for: '{term}'")
                
                for row in rows:
                    cols = row.query_selector_all("td")
                    
                    if len(cols) >= 3:
                        raw_text = cols[1].inner_text().strip()
                        if not raw_text:
                            continue
                            
                        title_part = re.split(r'Tarikh\s+Iklan|Tarikh', raw_text, flags=re.IGNORECASE)[0].strip()
                        clean_title = " ".join(title_part.split())
                        title_lower = clean_title.lower()
                        
                        if "berjaya" in title_lower or "batal" in title_lower:
                            continue 
                        
                        if term in title_lower and clean_title not in seen_titles:
                            seen_titles.add(clean_title)
                            
                            date_match = re.search(r'Tarikh Tutup\s*:\s*([^\n]+)', raw_text, re.IGNORECASE)
                            closing_date = date_match.group(1).strip() if date_match else "Sila Rujuk Dokumen"
                            
                            pdf_link = url 
                            link_el = cols[2].query_selector("a") 
                            if link_el:
                                extracted_href = link_el.get_attribute("href")
                                if extracted_href:
                                    if extracted_href.startswith("http"):
                                        pdf_link = extracted_href
                                    else:
                                        slash = "" if extracted_href.startswith("/") else "/"
                                        pdf_link = f"https://jknns.moh.gov.my{slash}{extracted_href}"
                            
                            results.append({
                                "Title": clean_title,
                                "Agency": "Jabatan Kesihatan Negeri Sembilan (JKNNS)",
                                "Closing Date": closing_date,
                                "Source": "Negeri Sembilan",
                                "Link": pdf_link 
                            })
                            print(f"✅ [ADDED] {clean_title[:60]}...")
                            
        except Exception as e: 
            print(f"Negeri Sembilan Scraping Error: {e}")
            
        finally: 
            browser.close()
            
    return results
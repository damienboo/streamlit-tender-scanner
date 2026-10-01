from playwright.sync_api import sync_playwright
import time
import re

def scrape_perak(keyword):
    results = []
    print(f"Starting scrape for Perak S3PK (Keywords: '{keyword}')...")
    search_terms = [k.strip().lower() for k in keyword.split(",")]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            page.goto("https://s3pk.perak.gov.my/IklanList.aspx", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("table.gv", timeout=20000)
            page_num = 1
            
            while True:
                print(f"📄 Scanning Perak Page {page_num}...")
                rows = page.query_selector_all("table.gv tr.gvr, table.gv tr.gva")
                
                for row in rows:
                    cols = row.query_selector_all("td")
                    if len(cols) >= 5:
                        raw_title = cols[1].inner_text().strip()
                        closing_date = cols[4].inner_text().strip()
                        agency_text = "Kerajaan Negeri Perak" 
                        clean_title = raw_title.replace('\n', ' | ')
                        
                        text_lower = (clean_title + " " + agency_text).lower()
                        match_found = any(re.search(rf'\b{re.escape(term)}\b', text_lower) for term in search_terms)
                        
                        if match_found:
                            detail_link = "https://s3pk.perak.gov.my/IklanList.aspx"
                            link_el = cols[1].query_selector("a")
                            
                            if link_el:
                                href = link_el.get_attribute("href")
                                onclick = link_el.get_attribute("onclick")
                                
                                if href and href != "#" and not href.startswith("javascript"):
                                    slash = "" if href.startswith("/") else "/"
                                    detail_link = f"https://s3pk.perak.gov.my{slash}{href}"
                                    
                                elif onclick:
                                    match = re.search(r"['\"]([^'\"]+)['\"]", onclick)
                                    if match:
                                        extracted = match.group(1)
                                        slash = "" if extracted.startswith("/") else "/"
                                        detail_link = f"https://s3pk.perak.gov.my{slash}{extracted}"
                            
                            results.append({
                                "Title": clean_title,
                                "Agency": agency_text,
                                "Closing Date": closing_date,
                                "Source": "Perak (S3PK)",
                                "Link": detail_link
                            })
                
                pager = page.locator("span#MainContent_DataPager1")
                if pager.count() == 0: break 
                current_span = pager.locator("> span").first
                if current_span.count() == 0: break
                    
                next_val = str(int(current_span.inner_text().strip()) + 1)
                next_link = pager.locator(f"a:text-is('{next_val}')")
                
                if next_link.count() > 0:
                    print(f"⏳ Clicking to go to Perak Page {next_val}...")
                    next_link.first.click(no_wait_after=True)
                    time.sleep(4) 
                    page_num += 1
                else:
                    print(f"✅ Reached end of Perak list at Page {page_num}.")
                    break
        except Exception as e: print(f"Perak Scraping Error: {e}")
        finally: browser.close()
    return results
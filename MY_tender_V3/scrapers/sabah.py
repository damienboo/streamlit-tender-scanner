from playwright.sync_api import sync_playwright
import time
import re

def scrape_sabah(keyword):
    results = []
    print(f"Starting scrape for Sabah JKR (Keywords: '{keyword}')...")
    search_terms = [k.strip().lower() for k in keyword.split(",")]
    seen_titles = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            url = "http://jkr.sabah.gov.my/tender/"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page_num = 1
            
            while True:
                print(f"📄 Scanning Sabah Page {page_num}...")
                page.wait_for_selector("table.ninja_footable", timeout=30000)
                page.wait_for_selector("table.ninja_footable tbody tr", timeout=30000)
                
                rows = page.query_selector_all("table.ninja_footable tbody tr")
                for row in rows:
                    cols = row.query_selector_all("td")
                    if len(cols) >= 5:
                        title_el = cols[2].query_selector("a")
                        date_el = cols[3].query_selector("a")
                        
                        if title_el:
                            clean_title = title_el.inner_text().strip().replace('\n', ' ')
                            text_lower = clean_title.lower()
                            
                            match_found = any(re.search(rf'\b{re.escape(term)}\b', text_lower) for term in search_terms)
                                    
                            if match_found and clean_title not in seen_titles:
                                seen_titles.add(clean_title)
                                closing_date = date_el.inner_text().strip() if date_el else "TBA"
                                raw_agency = cols[4].inner_text().strip()
                                
                                href = title_el.get_attribute("href")
                                if href:
                                    if href.startswith("http"):
                                        detail_link = href
                                    else:
                                        slash = "" if href.startswith("/") else "/"
                                        detail_link = f"http://jkr.sabah.gov.my{slash}{href}"
                                else:
                                    detail_link = "http://jkr.sabah.gov.my/tender/"
                                
                                results.append({
                                    "Title": clean_title,
                                    "Agency": f"JKR Sabah ({raw_agency})" if raw_agency else "JKR Sabah",
                                    "Closing Date": closing_date,
                                    "Source": "Sabah (JKR)",
                                    "Link": detail_link
                                })
                
                next_button = page.locator("li.footable-page-nav[data-page='next']:not(.disabled) a")
                if next_button.count() > 0:
                    next_button.first.click(no_wait_after=True)
                    time.sleep(4)
                    page_num += 1
                else:
                    print(f"✅ Reached end of Sabah list at Page {page_num}.")
                    break
        except Exception as e: print(f"Sabah Scraping Error: {e}")
        finally: browser.close()
    return results
from playwright.sync_api import sync_playwright
import time
import re

def scrape_sarawak(keyword):
    results = []
    print(f"Starting scrape for Sarawak eTender (Keyword: '{keyword}')...")
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
            url = "https://etendernotice.sarawak.gov.my/etender/public/public_tender_list.jsp"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            current_index = 0
            page_num = 1
            while True:
                print(f"📄 Scanning Sarawak Page {page_num}...")
                page.wait_for_selector("table.content", timeout=15000)
                rows = page.query_selector_all("table.content tr:not(.panel)")
                for row in rows:
                    cols = row.query_selector_all("td")
                    if len(cols) == 5:
                        closing_date = cols[2].inner_text().strip().replace('\n', ' ')
                        agency_text = cols[3].inner_text().strip()
                        title_el = cols[4].query_selector("a")
                        raw_title = cols[4].inner_text().strip()
                        clean_title = raw_title.replace('\n', ' | ')
                        text_lower = clean_title.lower()
                        match_found = any(term in text_lower for term in search_terms)
                        if match_found and clean_title not in seen_titles:
                            seen_titles.add(clean_title)
                            detail_link = url
                            if title_el:
                                href = title_el.get_attribute("href")
                                if href and "javascript:MedWindow" in href:
                                    match = re.search(r"['\"]([^'\"]+)['\"]", href)
                                    if match:
                                        extracted = match.group(1)
                                        detail_link = f"https://etendernotice.sarawak.gov.my/etender/public/{extracted.lstrip('/')}"
                            results.append({
                                "Title": clean_title,
                                "Agency": agency_text,
                                "Closing Date": closing_date,
                                "Source": "Sarawak (eTender)",
                                "Link": detail_link
                            })
                            print(f"      ✅ [ADDED] {clean_title[:50]}...")
                next_index = current_index + 5
                next_link = page.locator(f"a[href*='current_index={next_index}']")
                if next_link.count() > 0:
                    print(f"⏳ Clicking Next Page (Index {next_index})...")
                    next_link.first.click(no_wait_after=True)
                    time.sleep(5)
                    current_index = next_index
                    page_num += 1
                else:
                    print(f"✅ Reached end of Sarawak list at Page {page_num}.")
                    break
        except Exception as e:
            print(f"Sarawak Scraping Error: {e}")
        finally:
            browser.close()
    return results
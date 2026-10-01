from playwright.sync_api import sync_playwright
import time
import re

def scrape_terengganu(keyword):
    results = []
    print(f"Starting scrape for Terengganu MBKT (Keywords: '{keyword}')...")
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
            print("📄 Checking main active tenders table...")
            url = "https://mbkt.terengganu.gov.my/ms/perniagaan/tender-sebutharga"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            try:
                page.wait_for_selector("table tbody tr", timeout=15000)
                rows = page.query_selector_all("table tbody tr")
                print(f"Found {len(rows)} table rows in MBKT main portal.")

                for row in rows:
                    cols = row.query_selector_all("td")

                    if len(cols) >= 4:
                        raw_title = cols[1].inner_text().strip()
                        clean_title = raw_title.replace('\n', ' ')
                        text_lower = clean_title.lower()

                        match_found = any(re.search(rf'\b{re.escape(term)}\b', text_lower) for term in search_terms)
                        
                        if match_found and clean_title and clean_title not in seen_titles:
                            seen_titles.add(clean_title)
                            
                            closing_date = cols[2].inner_text().strip()
                            if not closing_date:
                                closing_date = "Sila Rujuk Dokumen"

                            detail_link = url 
                            link_el = cols[3].query_selector("a")
                            
                            if link_el:
                                href = link_el.get_attribute("href")
                                if href:
                                    if href.startswith("http"):
                                        detail_link = href
                                    else:
                                        slash = "" if href.startswith("/") else "/"
                                        detail_link = f"https://mbkt.terengganu.gov.my{slash}{href}"

                            results.append({
                                "Title": clean_title,
                                "Agency": "Majlis Bandaraya Kuala Terengganu (MBKT)",
                                "Closing Date": closing_date,
                                "Source": "Terengganu (MBKT)",
                                "Link": detail_link 
                            })
                            print(f"      ✅ [ADDED] {clean_title[:60]}...")

            except Exception as e:
                print(f"ℹ️ Main table not found or empty: {e}")

            print(f"✅ Finished Terengganu MBKT.")

        except Exception as e:
            print(f"Terengganu Scraping Error: {e}")
        finally:
            browser.close()

    return results
from playwright.sync_api import sync_playwright
import re

def scrape_pahang(keyword):
    results = []
    print(f"Starting scrape for Pahang (Keywords: '{keyword}')...")
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
            url = "https://perolehan.pahang.gov.my/"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print("⏳ Looking for active tender links...")
            tender_links = page.locator("a[href*='iklan.php']")
            try:
                tender_links.first.wait_for(state="attached", timeout=15000)
            except Exception:
                print("ℹ️ No active tender links found on Pahang homepage.")
                return results
            count = tender_links.count()
            print(f"📄 Found {count} active tender links. Scanning...")
            for i in range(count):
                link_el = tender_links.nth(i)
                title_text = link_el.text_content().strip()
                if not title_text: continue
                clean_title = " ".join(title_text.split())
                title_lower = clean_title.lower()
                match_found = any(term in title_lower for term in search_terms)
                if match_found and clean_title not in seen_titles:
                    seen_titles.add(clean_title)
                    href = link_el.get_attribute("href")
                    onclick = link_el.get_attribute("onclick")
                    detail_link = url
                    if href and href != "#" and not href.startswith("javascript"):
                        slash = "" if href.startswith("/") else "/"
                        detail_link = f"https://perolehan.pahang.gov.my{slash}{href}"
                    elif onclick:
                        match = re.search(r"['\"]([^'\"]+)['\"]", onclick)
                        if match:
                            extracted = match.group(1)
                            slash = "" if extracted.startswith("/") else "/"
                            detail_link = f"https://perolehan.pahang.gov.my{slash}{extracted}"
                    closing_date = "Sila Rujuk Dokumen"
                    if detail_link != url:
                        try:
                            detail_page = context.new_page()
                            detail_page.goto(detail_link, wait_until="domcontentloaded", timeout=30000)
                            body_text = detail_page.locator("body").text_content()
                            date_match = re.search(r'pada\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4}(?:\s*\([^)]+\))?)', body_text)
                            if date_match:
                                closing_date = date_match.group(1).strip()
                            detail_page.close()
                        except Exception as e:
                            print(f"      ⚠️ Could not fetch deep details: {e}")
                    results.append({
                        "Title": clean_title,
                        "Agency": "Pejabat Setiausaha Kerajaan Pahang",
                        "Closing Date": closing_date,
                        "Source": "Pahang",
                        "Link": detail_link
                    })
                    print(f"      ✅ [ADDED] {clean_title[:60]}... (Tutup: {closing_date})")
        except Exception as e:
            print(f"Pahang Scraping Error: {e}")
        finally:
            browser.close()
    return results
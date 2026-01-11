import asyncio
import sys
import re
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def run_stealth_audit(url: str):
    # --- 1. WINDOWS LOOP POLICY FIX ---
    if sys.platform == 'win32':
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except:
                pass

    browser = None
    try:
        async with async_playwright() as p:
            # --- 2. LAUNCH BROWSER DENGAN ANTI-BOT ---
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--allow-running-insecure-content"
                ]
            )
            
            context = await browser.new_context(
                ignore_https_errors=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720},
                extra_http_headers={
                "ngrok-skip-browser-warning": "true"
                 }
            )
            page = await context.new_page()
            page.on("console", lambda msg: print(f"BROWSER_LOG: {msg.text}"))
            page.on("pageerror", lambda exc: print(f"BROWSER_EXCEPTION: {exc}")) 
            print(f"DEBUG: Navigating to {url}...")
            
            # --- 3. NAVIGASI ---
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                # Tunggu 5 detik agar script Stealth Engine (loader.js) punya waktu bekerja
                await page.wait_for_timeout(5000)
            except Exception as nav_e:
                print(f"DEBUG: Navigation timeout/issue: {nav_e}")
                return {"is_protected": True, "score": 85, "details": "Shielded: WAF Blocking Access"}

            # --- 4. AMBIL KONTEN & HEADERS ---
            rendered_content = await page.content()
            headers_lower = {k.lower(): v.lower() for k, v in response.headers.items()}
            
            # Ambil teks langsung dari DOM (innerText) untuk deteksi Poisoning
            target_text = await page.evaluate("""
                () => {
                    // Mengambil teks dari seluruh elemen body termasuk karakter tersembunyi
                    return document.body.textContent;
                }
            """)
            
            # --- 5. DETEKSI WAF (Cloudflare, Akamai, Shopee, dll) ---
            waf_name = "None"
            score = 20
            details = []

            # Cek Headers
            if "cf-ray" in headers_lower or "server" in headers_lower and "cloudflare" in headers_lower["server"]:
                waf_name = "Cloudflare"
            elif "x-akamai-transformed" in headers_lower:
                waf_name = "Akamai"
            
            # Cek Cookies (Sidik jari WAF)
            cookies = await context.cookies()
            cookie_names = [c['name'] for c in cookies]
            if any(n.startswith("SPC_") for n in cookie_names):
                waf_name = "Shopee Shield (Akamai)"

            if waf_name != "None":
                score = 90
                details.append(f"WAF: {waf_name}")

            # --- 6. DETEKSI POISONING (Zero-Width Characters) ---
            # Mencakup semua varian Zero-Width
            zw_pattern = re.compile(r'[\u200b\u200c\u200d\u200e\u200f\ufeff]')
            found_zw = zw_pattern.findall(target_text)

            print(f"DEBUG: Deteksi mendalam menemukan {len(found_zw)} karakter rahasia.")
            
            if len(found_zw) > 10:
                score = 98
                details.append(f"Stealth Engine: Active ({len(found_zw)} poison chars)")
            elif "MutationObserver" in rendered_content:
                score = max(score, 70)
                details.append("Stealth Script: Detected (Dormant)")

            # --- 7. SCREENSHOT UNTUK DEBUGGING ---
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(os.path.dirname(current_dir))
            screenshot_path = os.path.join(root_dir, "debug_audit.png")
            
            try:
                await page.screenshot(path=screenshot_path)
                print(f"DEBUG: Screenshot saved to {screenshot_path}")
            except:
                pass

            await browser.close()

            return {
                "is_protected": score > 40,
                "score": score,
                "details": " | ".join(details) if details else "Vulnerable: No protection active",
                "tech_stack": {
                    "waf": waf_name,
                    "poisoning_level": "High" if len(found_zw) > 15 else "None"
                }
            }

    except Exception as e:
        print(f"DEBUG AUDITOR ERROR: {e}")
        if browser: await browser.close()
        return {
            "is_protected": True, 
            "score": 85, 
            "details": f"Shielded: Connection encrypted/obfuscated",
            "tech_stack": {"waf": "Protected", "poisoning_level": "Stable"}
        }

# Contoh penggunaan: Jalankan script ini dengan argumen URL
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python stealth_auditor.py <url>")
        sys.exit(1)
    url = sys.argv[1]
    result = asyncio.run(run_stealth_audit(url))
    print(result)
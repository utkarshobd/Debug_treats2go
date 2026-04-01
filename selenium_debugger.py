"""
Selenium-based Comprehensive Navbar Debugger for treats2go.in
Uses real Chrome browser to bypass anti-bot protection (403 Forbidden)
Updated: improved stale element handling and click test reliability

Requirements:
    pip install selenium webdriver-manager
"""
import time
import random
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://treats2go.in"
TARGET_ITEMS = ["home", "shop", "personal care", "contact"]
ISSUES = []

def log_issue(severity, component, problem, detail, fix):
    ISSUES.append({
        "severity": severity,
        "component": component,
        "problem": problem,
        "detail": detail,
        "fix": fix
    })

def random_delay(a=1.5, b=4.0):
    d = random.uniform(a, b)
    print(f"  [DELAY] {d:.2f}s ...")
    time.sleep(d)

def make_driver():
    """Create stealth Chrome driver"""
    opts = Options()
    # Headless mode - set to False if you want to see the browser
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    
    # Remove webdriver flag
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

print("="*70)
print("SELENIUM NAVBAR DEBUGGER — treats2go.in")
print("="*70)
print()

driver = make_driver()
wait = WebDriverWait(driver, 15)

try:
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 1: Load homepage
    # ═══════════════════════════════════════════════════════════════════════
    print("="*70)
    print("STEP 1: Loading Homepage")
    print("="*70)
    
    driver.get(BASE_URL)
    random_delay(3, 5)  # Wait for JS to render
    
    title = driver.title
    current_url = driver.current_url
    print(f"  [OK] Page loaded: {current_url}")
    print(f"  [OK] Title: {title}")
    
    # Get full page source after JS execution
    page_source = driver.page_source
    print(f"  [OK] Page source size: {len(page_source)} chars")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 2: Detect navbar
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("="*70)
    print("STEP 2: Navbar Container Detection")
    print("="*70)
    
    navbar = None
    navbar_selectors = ["nav", "header", "#site-navigation", ".navbar", 
                        "#masthead", ".site-header", ".main-navigation"]
    
    for sel in navbar_selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            navbar = el
            print(f"  [OK] Navbar found via selector: '{sel}'")
            print(f"       Tag: {el.tag_name}")
            print(f"       ID: {el.get_attribute('id') or 'none'}")
            print(f"       Class: {el.get_attribute('class') or 'none'}")
            break
        except NoSuchElementException:
            continue
    
    if not navbar:
        print("  [ISSUE] No navbar container found!")
        log_issue("CRITICAL", "Navbar", "Navbar container missing",
                  "None of the common navbar selectors matched",
                  "Inspect page source to find actual navbar container selector")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 3: Bootstrap version detection
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("="*70)
    print("STEP 3: Bootstrap CSS & JS Detection")
    print("="*70)
    
    bs_version = None
    
    # Check via JS
    bs_ver_js = driver.execute_script("""
        if (typeof bootstrap !== 'undefined') return bootstrap.Tooltip.VERSION || 'found_no_version';
        return null;
    """)
    
    if bs_ver_js:
        print(f"  [OK] Bootstrap JS object found, version: {bs_ver_js}")
        bs_version = 5 if bs_ver_js.startswith("5") else 4
    else:
        print("  [WARN] Bootstrap JS object not found in window scope")
        log_issue("HIGH", "Bootstrap JS", 
                  "Bootstrap JS not initialized or not in global scope",
                  "window.bootstrap is undefined",
                  "Ensure bootstrap.bundle.min.js is loaded and not deferred incorrectly")
    
    # Check CSS links
    css_links = driver.execute_script("""
        return Array.from(document.querySelectorAll('link[rel=stylesheet]'))
            .map(l => l.href)
            .filter(h => h.toLowerCase().includes('bootstrap'));
    """)
    
    if css_links:
        for link in css_links:
            print(f"  [OK] Bootstrap CSS: {link}")
            if "5." in link or "bootstrap@5" in link:
                bs_version = 5
            elif "4." in link or "bootstrap@4" in link:
                bs_version = 4
    else:
        print("  [ISSUE] No Bootstrap CSS link found!")
        log_issue("HIGH", "Bootstrap CSS", "Bootstrap CSS not loaded",
                  "No <link> with 'bootstrap' in href found",
                  "Add Bootstrap 5 CDN link in <head>")
    
    # Check JS scripts
    js_scripts = driver.execute_script("""
        return Array.from(document.querySelectorAll('script[src]'))
            .map(s => s.src)
            .filter(s => s.toLowerCase().includes('bootstrap'));
    """)
    
    if js_scripts:
        for src in js_scripts:
            print(f"  [OK] Bootstrap JS: {src}")
            if "bundle" not in src.lower():
                print(f"       [WARN] Not using bootstrap.bundle — Popper.js may be missing!")
                log_issue("HIGH", "Bootstrap JS", "bootstrap.bundle not used",
                          f"src={src}",
                          "Use bootstrap.bundle.min.js which includes Popper.js (required for dropdowns)")
    else:
        print("  [ISSUE] No Bootstrap JS script found!")
        log_issue("HIGH", "Bootstrap JS", "Bootstrap JS not loaded",
                  "No <script src> with 'bootstrap' found",
                  "Add bootstrap.bundle.min.js before </body>")
    
    bs_version = bs_version or 5
    print(f"  Bootstrap version: {bs_version}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 4: jQuery check
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("="*70)
    print("STEP 4: jQuery Check")
    print("="*70)
    
    jquery_present = driver.execute_script("return typeof jQuery !== 'undefined'")
    jquery_version = driver.execute_script("return typeof jQuery !== 'undefined' ? jQuery.fn.jquery : null")
    
    if jquery_present:
        print(f"  [OK] jQuery present, version: {jquery_version}")
    else:
        print("  [WARN] jQuery not found in global scope")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 5: Target menu items
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("="*70)
    print("STEP 5: Target Menu Items")
    print("="*70)
    
    found_items = {}
    
    for item in TARGET_ITEMS:
        # Try multiple strategies to find menu items
        found = False
        
        # Strategy 1: nav links
        try:
            links = driver.find_elements(By.CSS_SELECTOR, "nav a, header a, .navbar a, #site-navigation a")
            for link in links:
                text = link.text.strip().lower()
                if item in text:
                    href = link.get_attribute("href") or "N/A"
                    found_items[item] = {"element": link, "href": href, "text": link.text.strip()}
                    print(f"  [OK] '{item}' found: '{link.text.strip()}' -> {href}")
                    found = True
                    break
        except Exception:
            pass
        
        # Strategy 2: all links
        if not found:
            try:
                all_links = driver.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    text = link.text.strip().lower()
                    if item in text and link.is_displayed():
                        href = link.get_attribute("href") or "N/A"
                        found_items[item] = {"element": link, "href": href, "text": link.text.strip()}
                        print(f"  [OK] '{item}' found (full page): '{link.text.strip()}' -> {href}")
                        found = True
                        break
            except Exception:
                pass
        
        if not found:
            print(f"  [ISSUE] '{item}' NOT found in page!")
            log_issue("HIGH", f"Menu: {item}", f"'{item}' link missing",
                      "Link not found in rendered page",
                      "Add menu item in WordPress Appearance > Menus")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 6: HTTP status check
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("="*70)
    print("STEP 6: HTTP Status Check for Target Links")
    print("="*70)
    
    import requests as req_lib
    
    for item, data in found_items.items():
        href = data["href"]
        if not href or href == "N/A" or href.startswith("javascript"):
            print(f"  [ISSUE] {item}: Invalid href '{href}'")
            log_issue("MEDIUM", f"Link: {item}", "Invalid or missing href",
                      f"href='{href}'", "Set a valid URL for this menu item")
            continue
        
        random_delay(1, 2)
        try:
            r = req_lib.head(href, timeout=10, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"})
            status = r.status_code
            if status == 200:
                print(f"  [OK] {item}: HTTP {status} -> {href}")
            elif status in (301, 302):
                print(f"  [WARN] {item}: HTTP {status} redirect -> {href}")
                log_issue("LOW", f"Link: {item}", f"Redirect HTTP {status}",
                          href, "Verify final destination URL")
            else:
                print(f"  [ISSUE] {item}: HTTP {status} -> {href}")
                log_issue("HIGH", f"Link: {item}", f"Bad HTTP status {status}",
                          href, "Fix URL or page")
        except Exception as e:
            print(f"  [ERROR] {item}: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 7: Dropdown deep analysis
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("="*70)
    print("STEP 7: Dropdown Deep Analysis")
    print("="*70)
    
    dropdown_containers = driver.find_elements(By.CSS_SELECTOR, ".dropdown, li.dropdown, .nav-item.dropdown")
    print(f"  Total dropdown containers found: {len(dropdown_containers)}")
    
    if not dropdown_containers:
        print("  [ISSUE] No dropdown elements found!")
        log_issue("HIGH", "Dropdowns", "No dropdown elements in rendered HTML",
                  "No element with class 'dropdown' found after JS execution",
                  "Check WordPress menu walker — it may not be adding Bootstrap dropdown classes")
    
    total_dropdowns = len(dropdown_containers)
    for idx in range(total_dropdowns):
        # Re-fetch to avoid stale element after DOM changes from click
        dropdown_containers = driver.find_elements(By.CSS_SELECTOR, ".dropdown, li.dropdown, .nav-item.dropdown")
        if idx >= len(dropdown_containers):
            break
        container = dropdown_containers[idx]
        tag = container.tag_name
        classes = container.get_attribute("class") or ""
        print(f"\n  --- Dropdown #{idx+1}: <{tag} class='{classes}'>")

        
        # Find toggle link
        try:
            toggle = container.find_element(By.CSS_SELECTOR, "a.dropdown-toggle, button.dropdown-toggle")
        except NoSuchElementException:
            print("    [ISSUE] No .dropdown-toggle element found!")
            log_issue("HIGH", f"Dropdown #{idx}", "Missing dropdown-toggle",
                      f"No a.dropdown-toggle or button.dropdown-toggle inside container",
                      "Add class='dropdown-toggle' to the menu item anchor tag")
            continue
        
        toggle_text = toggle.text.strip()
        toggle_href = toggle.get_attribute("href") or "N/A"
        toggle_class = toggle.get_attribute("class") or ""
        
        print(f"    Text              : '{toggle_text}'")
        print(f"    href              : {toggle_href}")
        print(f"    class             : {toggle_class}")
        
        # ── All critical attributes ──────────────────────────────────────
        data_bs_toggle = toggle.get_attribute("data-bs-toggle")
        data_toggle    = toggle.get_attribute("data-toggle")
        aria_expanded  = toggle.get_attribute("aria-expanded")
        aria_haspopup  = toggle.get_attribute("aria-haspopup")
        role           = toggle.get_attribute("role")
        tabindex       = toggle.get_attribute("tabindex")
        el_id          = toggle.get_attribute("id")
        
        print(f"    data-bs-toggle    : {data_bs_toggle!r}")
        print(f"    data-toggle       : {data_toggle!r}  (Bootstrap 4 attr)")
        print(f"    aria-expanded     : {aria_expanded!r}")
        print(f"    aria-haspopup     : {aria_haspopup!r}")
        print(f"    role              : {role!r}")
        print(f"    tabindex          : {tabindex!r}")
        print(f"    id                : {el_id!r}")
        
        # ── Bootstrap version specific check ────────────────────────────
        if bs_version == 5:
            if data_bs_toggle != "dropdown":
                print(f"    [CRITICAL ISSUE] data-bs-toggle='dropdown' MISSING!")
                print(f"                     Bootstrap 5 REQUIRES this attribute for dropdowns to work.")
                print(f"                     Without it, clicking the toggle does NOTHING.")
                log_issue("CRITICAL", f"Dropdown toggle: '{toggle_text}'",
                          "Missing data-bs-toggle='dropdown'",
                          f"Bootstrap 5 requires data-bs-toggle='dropdown'. "
                          f"Currently: data-bs-toggle={data_bs_toggle!r}",
                          f"Add data-bs-toggle=\"dropdown\" to the <a> tag for '{toggle_text}'. "
                          f"Edit theme header.php or menu walker, or add custom JS fix.")
            else:
                print(f"    [OK] data-bs-toggle='dropdown' present")
            
            if data_toggle == "dropdown":
                print(f"    [WARN] data-toggle='dropdown' (Bootstrap 4 attr) also present — redundant but harmless")
        
        elif bs_version == 4:
            if data_toggle != "dropdown":
                print(f"    [CRITICAL ISSUE] data-toggle='dropdown' MISSING!")
                log_issue("CRITICAL", f"Dropdown toggle: '{toggle_text}'",
                          "Missing data-toggle='dropdown'",
                          f"Bootstrap 4 requires data-toggle='dropdown'. "
                          f"Currently: data-toggle={data_toggle!r}",
                          f"Add data-toggle=\"dropdown\" to the <a> tag for '{toggle_text}'")
            else:
                print(f"    [OK] data-toggle='dropdown' present")
        
        # ── Accessibility checks ─────────────────────────────────────────
        if not aria_expanded:
            print(f"    [WARN] aria-expanded missing (accessibility issue)")
            log_issue("LOW", f"Dropdown: '{toggle_text}'", "Missing aria-expanded",
                      "Accessibility attribute absent",
                      "Add aria-expanded='false' to toggle element")
        
        if not aria_haspopup:
            print(f"    [WARN] aria-haspopup missing (accessibility issue)")
            log_issue("LOW", f"Dropdown: '{toggle_text}'", "Missing aria-haspopup",
                      "Accessibility attribute absent",
                      "Add aria-haspopup='true' to toggle element")
        
        # ── Dropdown menu check ──────────────────────────────────────────
        try:
            menu = container.find_element(By.CSS_SELECTOR, ".dropdown-menu, ul.sub-menu")
            menu_class = menu.get_attribute("class") or ""
            menu_style = menu.get_attribute("style") or ""
            menu_visible = menu.is_displayed()
            
            print(f"    dropdown-menu     : <{menu.tag_name} class='{menu_class}'>")
            print(f"    menu visible      : {menu_visible}")
            print(f"    menu style        : {menu_style!r}")
            
            # Check for display:none
            if "display: none" in menu_style or "display:none" in menu_style:
                print(f"    [ISSUE] Inline display:none on dropdown-menu!")
                log_issue("HIGH", f"Dropdown menu: '{toggle_text}'",
                          "Inline display:none on .dropdown-menu",
                          f"style='{menu_style}'",
                          "Remove inline display:none — Bootstrap JS controls visibility")
            
            # Check computed visibility via JS
            is_hidden = driver.execute_script(
                "return window.getComputedStyle(arguments[0]).display === 'none'", menu)
            if is_hidden:
                print(f"    [INFO] Menu is hidden (expected when not hovered/clicked)")
            
            # Sub-items
            sub_items = menu.find_elements(By.TAG_NAME, "li")
            print(f"    sub-items         : {len(sub_items)}")
            for li in sub_items:
                a = li.find_elements(By.TAG_NAME, "a")
                if a:
                    print(f"      - '{a[0].text.strip()}' -> {a[0].get_attribute('href') or 'N/A'}")
            
            if len(sub_items) == 0:
                print(f"    [ISSUE] Empty dropdown menu!")
                log_issue("MEDIUM", f"Dropdown: '{toggle_text}'", "Empty dropdown menu",
                          "No <li> items in .dropdown-menu",
                          "Add sub-menu items in WordPress Appearance > Menus")
        
        except NoSuchElementException:
            print(f"    [ISSUE] No .dropdown-menu or .sub-menu found!")
            log_issue("HIGH", f"Dropdown: '{toggle_text}'", "Missing .dropdown-menu",
                      "No .dropdown-menu or .sub-menu inside dropdown container",
                      "Add <ul class='dropdown-menu'> inside the dropdown li")
        
        # ── Click test ───────────────────────────────────────────────────
        print(f"    --- Click test for '{toggle_text}' ---")
        try:
            # Re-fetch toggle to avoid stale reference after previous click
            dropdown_containers = driver.find_elements(By.CSS_SELECTOR, ".dropdown, li.dropdown, .nav-item.dropdown")
            container = dropdown_containers[idx]
            toggle = container.find_element(By.CSS_SELECTOR, "a.dropdown-toggle, button.dropdown-toggle")
            
            driver.execute_script("arguments[0].scrollIntoView(true);", toggle)
            random_delay(0.5, 1.0)
            driver.execute_script("arguments[0].click();", toggle)
            random_delay(0.8, 1.5)
            
            # Re-fetch container and menu after click
            dropdown_containers = driver.find_elements(By.CSS_SELECTOR, ".dropdown, li.dropdown, .nav-item.dropdown")
            container = dropdown_containers[idx]
            
            try:
                menu_after = container.find_element(By.CSS_SELECTOR, ".dropdown-menu, ul.sub-menu")
                is_open = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).display !== 'none'", menu_after)
                has_show = "show" in (menu_after.get_attribute("class") or "")
                
                print(f"    After click - menu display != none : {is_open}")
                print(f"    After click - has 'show' class     : {has_show}")
                
                if not is_open and not has_show:
                    print(f"    [CRITICAL ISSUE] Dropdown did NOT open after click!")
                    log_issue("CRITICAL", f"Dropdown click: '{toggle_text}'",
                              "Dropdown does not open on click",
                              "After clicking toggle, menu remains hidden. "
                              "Bootstrap JS is not handling the click event.",
                              "1. Add data-toggle='dropdown' (BS4) to toggle element. "
                              "2. Ensure bootstrap.bundle.min.js is loaded. "
                              "3. Check for JS errors in browser console.")
                else:
                    print(f"    [OK] Dropdown opened successfully on click!")
                
                # Close it
                driver.execute_script("arguments[0].click();", toggle)
                random_delay(0.5, 1.0)
                
            except NoSuchElementException:
                print(f"    [ISSUE] Cannot verify dropdown state after click")
        
        except Exception as e:
            print(f"    [WARN] Click test error: {type(e).__name__}: {str(e)[:120]}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 8: CSS conflict scan
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("="*70)
    print("STEP 8: CSS Conflict Scan")
    print("="*70)
    
    # Check for CSS that might hide dropdowns
    css_issues = driver.execute_script("""
        var issues = [];
        var dropdownMenus = document.querySelectorAll('.dropdown-menu, .sub-menu');
        dropdownMenus.forEach(function(el) {
            var style = window.getComputedStyle(el);
            var inline = el.getAttribute('style') || '';
            if (inline.includes('display:none') || inline.includes('display: none')) {
                issues.push('Inline display:none on: ' + el.className);
            }
            var zIndex = parseInt(style.zIndex);
            if (!isNaN(zIndex) && zIndex < 100) {
                issues.push('Low z-index (' + zIndex + ') on: ' + el.className);
            }
            var overflow = style.overflow;
            var parent = el.parentElement;
            while (parent) {
                var pStyle = window.getComputedStyle(parent);
                if (pStyle.overflow === 'hidden') {
                    issues.push('Parent has overflow:hidden — may clip dropdown. Parent: ' + parent.className);
                    break;
                }
                parent = parent.parentElement;
            }
        });
        return issues;
    """)
    
    if css_issues:
        for issue in css_issues:
            print(f"  [WARN] {issue}")
            log_issue("MEDIUM", "CSS Conflict", issue, "Detected via computed styles",
                      "Review and fix the CSS conflict")
    else:
        print("  [OK] No CSS conflicts detected on dropdown menus")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 9: JavaScript console errors
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("="*70)
    print("STEP 9: JavaScript Console Errors")
    print("="*70)
    
    # Get browser logs
    try:
        logs = driver.get_log("browser")
        errors = [l for l in logs if l["level"] in ("SEVERE", "WARNING")]
        
        if errors:
            print(f"  Found {len(errors)} console errors/warnings:")
            for log_entry in errors:
                level = log_entry["level"]
                msg = log_entry["message"]
                print(f"  [{level}] {msg}")
                if level == "SEVERE":
                    log_issue("HIGH", "JS Console", f"Console error: {msg[:80]}",
                              msg, "Fix JavaScript error — may prevent Bootstrap from initializing")
        else:
            print("  [OK] No console errors found")
    except Exception as e:
        print(f"  [WARN] Could not retrieve console logs: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 10: Inline style blocks — dropdown overrides
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("="*70)
    print("STEP 10: Inline <style> Blocks — Dropdown Overrides")
    print("="*70)
    
    dropdown_css_rules = driver.execute_script("""
        var rules = [];
        for (var i = 0; i < document.styleSheets.length; i++) {
            try {
                var sheet = document.styleSheets[i];
                if (!sheet.href) {  // inline styles only
                    var cssRules = sheet.cssRules || sheet.rules;
                    for (var j = 0; j < cssRules.length; j++) {
                        var rule = cssRules[j].cssText || '';
                        if (rule.toLowerCase().includes('dropdown')) {
                            rules.push(rule.substring(0, 200));
                        }
                    }
                }
            } catch(e) {}
        }
        return rules;
    """)
    
    if dropdown_css_rules:
        print(f"  [WARN] {len(dropdown_css_rules)} dropdown CSS rules in inline <style> blocks:")
        for rule in dropdown_css_rules:
            print(f"    {rule}")
        log_issue("MEDIUM", "Inline CSS", "Dropdown CSS overrides in <style> blocks",
                  f"{len(dropdown_css_rules)} rules found",
                  "Review these rules — they may override Bootstrap dropdown visibility")
    else:
        print("  [OK] No dropdown overrides in inline <style> blocks")

finally:
    driver.quit()

# ═══════════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════════════════════════════════
print()
print("="*70)
print("FINAL REPORT — ALL ISSUES FOUND")
print("="*70)

if not ISSUES:
    print("  No issues found!")
else:
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    ISSUES.sort(key=lambda x: order.get(x["severity"], 9))
    
    for i, iss in enumerate(ISSUES, 1):
        print(f"\n  Issue #{i}")
        print(f"  Severity  : {iss['severity']}")
        print(f"  Component : {iss['component']}")
        print(f"  Problem   : {iss['problem']}")
        print(f"  Detail    : {iss['detail']}")
        print(f"  Fix       : {iss['fix']}")
    
    counts = {}
    for iss in ISSUES:
        counts[iss["severity"]] = counts.get(iss["severity"], 0) + 1
    
    print()
    print("  Summary:")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if sev in counts:
            print(f"    {sev}: {counts[sev]}")

with open("report.json", "w", encoding="utf-8") as f:
    json.dump(ISSUES, f, indent=2, ensure_ascii=False)

print()
print("  Report saved: report.json")
print("="*70)

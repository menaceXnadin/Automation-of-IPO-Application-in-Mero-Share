from playwright.sync_api import sync_playwright
import json
import os
from pathlib import Path
import getpass
import time
import sys

# Fixed data directory for all credentials
DATA_DIR = Path(r"C:\Users\MenaceXnadin\Documents\merosharedata")
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = DATA_DIR / "family_members.json"
IPO_CONFIG_FILE = DATA_DIR / "ipo_config.json"

def print_progress(step, total, message, sub_message=""):
    """
    Print a progress bar with current step
    
    Args:
        step: Current step number (1-indexed)
        total: Total number of steps
        message: Main message to display
        sub_message: Optional sub-message with arrow prefix
    """
    # Calculate progress
    percentage = int((step / total) * 100)
    filled = int((step / total) * 30)  # 30 character wide bar
    bar = "█" * filled + "░" * (30 - filled)
    
    # Print progress bar
    print(f"\r[{bar}] {percentage}% ({step}/{total}) {message}", end="", flush=True)
    
    # If this is the last step or there's a sub-message, move to new line
    if sub_message:
        print(f"\n    → {sub_message}", flush=True)
    elif step == total:
        print()  # New line at the end

def load_family_members():
    """Load all family members from config file"""
    if not CONFIG_FILE.exists():
        return {"members": []}
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_family_members(config):
    """Save family members to config file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    if os.name != 'nt':
        os.chmod(CONFIG_FILE, 0o600)

def add_family_member():
    """Add a new family member"""
    print("\n=== Add Family Member ===")
    
    config = load_family_members()
    
    member_name = input("\nEnter member name (e.g., Dad, Mom, Me, Brother): ").strip()
    
    # Check if member already exists
    for member in config.get('members', []):
        if member['name'].lower() == member_name.lower():
            print(f"\n⚠ Member '{member_name}' already exists!")
            update = input("Update this member? (yes/no): ").strip().lower()
            if update != 'yes':
                return
            config['members'].remove(member)
            break
    
    print("\n--- Meroshare Credentials ---")
    print("Common DPs (or use option 6 to see all):")
    print("  139  - CREATIVE SECURITIES PRIVATE LIMITED (13300)")
    print("  146  - GLOBAL IME CAPITAL LIMITED (11200)")
    print("  175  - NMB CAPITAL LIMITED (11000)")
    print("  190  - SIDDHARTHA CAPITAL LIMITED (10900)\n")
    
    dp_value = input("Enter DP value (e.g., 139): ").strip()
    username = input("Enter username: ").strip()
    password = getpass.getpass("Enter password: ")
    pin = getpass.getpass("Enter 4-digit transaction PIN: ")
    
    print("\n--- IPO Application Settings ---")
    applied_kitta = input("Applied Kitta (default 10): ").strip() or "10"
    crn_number = input("CRN Number: ").strip()
    
    member = {
        "name": member_name,
        "dp_value": dp_value,
        "username": username,
        "password": password,
        "transaction_pin": pin,
        "applied_kitta": int(applied_kitta),
        "crn_number": crn_number
    }
    
    if 'members' not in config:
        config['members'] = []
    
    config['members'].append(member)
    save_family_members(config)
    
    print(f"\n✓ Member '{member_name}' added successfully!")
    print(f"✓ Total members: {len(config['members'])}\n")

def list_family_members():
    """List all family members"""
    config = load_family_members()
    members = config.get('members', [])
    
    if not members:
        print("\n⚠ No family members found. Add members first!\n")
        return None
    
    print("\n" + "="*60)
    print("FAMILY MEMBERS")
    print("="*60)
    for idx, member in enumerate(members, 1):
        print(f"{idx}. {member['name']}")
        print(f"   Username: {member['username']}")
        print(f"   DP: {member['dp_value']}")
        print(f"   Kitta: {member['applied_kitta']} | CRN: {member['crn_number']}")
        print()
    print("="*60)
    
    return members

def select_family_member():
    """Select a family member for IPO application"""
    members = list_family_members()
    
    if not members:
        return None
    
    while True:
        try:
            choice = input(f"\nSelect member (1-{len(members)}): ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(members):
                selected = members[idx]
                print(f"\n✓ Selected: {selected['name']}")
                return selected
            else:
                print(f"❌ Enter number between 1 and {len(members)}")
        except ValueError:
            print("❌ Invalid input")
        except KeyboardInterrupt:
            print("\n\n✗ Cancelled")
            return None

def save_credentials():
    """Legacy function - redirects to add_family_member"""
    return add_family_member()

def load_credentials():
    """Load credentials - for backward compatibility"""
    # Check for old single-member config
    old_config_file = DATA_DIR / "meroshare_config.json"
    if old_config_file.exists() and not CONFIG_FILE.exists():
        print("\n⚠ Old config format detected. Migrating to multi-member format...\n")
        with open(old_config_file, 'r') as f:
            old_config = json.load(f)
        
        # Migrate to new format
        member_name = input("Enter name for this member (e.g., Me): ").strip() or "Me"
        
        new_config = {
            "members": [{
                "name": member_name,
                "dp_value": old_config.get('dp_value', ''),
                "username": old_config.get('username', ''),
                "password": old_config.get('password', ''),
                "transaction_pin": old_config.get('transaction_pin', ''),
                "applied_kitta": 10,
                "crn_number": ""
            }]
        }
        
        save_family_members(new_config)
        print(f"✓ Migrated to new format as '{member_name}'\n")
        
        # Backup old file
        os.rename(old_config_file, old_config_file + ".backup")
    
    config = load_family_members()
    
    if not config.get('members'):
        print("\n⚠ No family members found. Let's add one!\n")
        add_family_member()
        config = load_family_members()
    
    return config

def update_credentials():
    """Legacy function - redirects to add_family_member"""
    add_family_member()

def meroshare_login(auto_load=True, headless=False):
    """
    Automated login for Meroshare with correct selectors
    
    Args:
        auto_load: Load credentials from config file
        headless: Run browser in headless mode (no GUI)
    """
    if auto_load:
        print("Loading credentials...")
        config = load_credentials()
        dp_value = config['dp_value']
        username = config['username']
        password = config['password']
    else:
        dp_value = input("Enter DP value: ")
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=100 if not headless else 0)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print_progress(1, 6, "Navigating to Meroshare...")
            page.goto("https://meroshare.cdsc.com.np/#/login", wait_until="networkidle")
            time.sleep(2)
            
            # Select2 dropdown - click to open
            print_progress(2, 6, "Opening DP dropdown...")
            page.click("span.select2-selection")
            time.sleep(1)
            
            # Select the option - Select2 creates a results list in the DOM
            print_progress(3, 6, f"Selecting DP (value: {dp_value})...")
            # Wait for dropdown results to appear
            page.wait_for_selector(".select2-results", timeout=5000)
            
            # Type in search box and select
            search_box = page.query_selector("input.select2-search__field")
            if search_box:
                print(f"    → Searching for DP value {dp_value}...")
                search_box.type(dp_value)
                time.sleep(0.5)
                
                # Click the first result or press Enter
                first_result = page.query_selector("li.select2-results__option--highlighted, li.select2-results__option[aria-selected='true']")
                if first_result:
                    first_result.click()
                else:
                    page.keyboard.press("Enter")
            else:
                # Fallback: click by text
                try:
                    results = page.query_selector_all("li.select2-results__option")
                    for result in results:
                        if dp_value in result.inner_text():
                            result.click()
                            break
                except:
                    print("    ⚠ Using fallback selection method...")
                    page.select_option("select.select2-hidden-accessible", dp_value)
            
            time.sleep(1)
            
            # Fill username - try multiple possible selectors
            print_progress(4, 6, "Filling username...")
            username_selectors = [
                "input[formcontrolname='username']",
                "input#username",
                "input[placeholder*='User']"
            ]
            for selector in username_selectors:
                try:
                    page.fill(selector, username, timeout=2000)
                    break
                except:
                    continue
            
            # Fill password
            print_progress(5, 6, "Filling password...")
            password_selectors = [
                "input[formcontrolname='password']",
                "input[type='password']"
            ]
            for selector in password_selectors:
                try:
                    page.fill(selector, password, timeout=2000)
                    break
                except:
                    continue
            
            # Click login button
            print_progress(6, 6, "Clicking login button...")
            login_button_selectors = [
                "button.btn.sign-in",
                "button[type='submit']",
                "button:has-text('Login')"
            ]
            for selector in login_button_selectors:
                try:
                    page.click(selector, timeout=2000)
                    break
                except:
                    continue
            
            # Wait for response - try to detect navigation
            print("\nWaiting for response...")
            try:
                # Wait for navigation or some change (max 8 seconds)
                page.wait_for_load_state("networkidle", timeout=8000)
            except:
                print("    (networkidle timeout - page may still be loading)")
            
            time.sleep(2)  # extra buffer for any JS to complete
            
            # Angular apps: wait for hash route to change from #/login to #/dashboard
            print("Waiting for Angular routing...")
            try:
                # Wait up to 3 seconds for URL to change away from #/login
                page.wait_for_function("window.location.hash !== '#/login'", timeout=3000)
                time.sleep(0.5)  # small buffer for final render
            except:
                print("    (route didn't change, but may still be logged in)")
            
            # Check result - multiple detection methods
            current_url = page.url
            print(f"\nCurrent URL: {current_url}")
            
            # Method 1: Check URL patterns (Angular hash routing)
            url_success = False
            if "#/login" not in current_url.lower():
                url_success = True
                print("✓ URL changed from login page")
            
            # Method 2: Check if login form is still visible
            form_gone = False
            try:
                login_form_visible = page.is_visible("input[formcontrolname='username']", timeout=1000)
                if not login_form_visible:
                    form_gone = True
                    print("✓ Login form disappeared")
            except:
                form_gone = True
                print("✓ Login form not found")
            
            # Method 3: Look for success indicators
            success_elements = [
                "a[href*='dashboard']",
                "button:has-text('Logout')",
                ".user-info, .user-profile",
                "[class*='dashboard']"
            ]
            found_success_element = False
            for selector in success_elements:
                try:
                    if page.query_selector(selector):
                        found_success_element = True
                        print(f"✓ Found success indicator: {selector}")
                        break
                except:
                    pass
            
            # Method 4: Check for error messages
            error_found = False
            try:
                errors = page.query_selector_all(".error, .alert-danger, .text-danger, [class*='error'], .invalid-feedback")
                for error in errors:
                    text = error.inner_text().strip()
                    if text and len(text) > 0:
                        print(f"⚠ Error message found: {text}")
                        error_found = True
            except:
                pass
            
            # Final verdict
            if error_found:
                print("\n✗ LOGIN FAILED - Error message detected")
                # Take screenshot for debugging
                try:
                    screenshot_path = "login_error.png"
                    page.screenshot(path=screenshot_path)
                    print(f"📸 Screenshot saved to {screenshot_path}")
                except:
                    pass
            elif url_success or form_gone or found_success_element:
                print("\n✓✓✓ LOGIN SUCCESSFUL! ✓✓✓")
                print(f"Page URL: {current_url}")
            else:
                print("\n⚠ Login status uncertain - please verify manually")
                print(f"URL contains 'login': {'login' in current_url.lower()}")
                # Take screenshot for debugging
                try:
                    screenshot_path = "login_uncertain.png"
                    page.screenshot(path=screenshot_path)
                    print(f"📸 Screenshot saved to {screenshot_path}")
                except:
                    pass
            
            # In headless mode, don't wait
            if not headless:
                print("\nBrowser will stay open for 30 seconds...")
                time.sleep(30)
            else:
                print("\n✓ Script completed in headless mode")
                time.sleep(2)
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            if not headless:
                time.sleep(5)
            
        finally:
            browser.close()

def get_portfolio(auto_load=True, headless=False):
    """
    Login and fetch portfolio holdings from Meroshare
    
    Args:
        auto_load: Load credentials from config file
        headless: Run browser in headless mode (no GUI)
    """
    if auto_load:
        print("Loading credentials...")
        config = load_credentials()
        dp_value = config['dp_value']
        username = config['username']
        password = config['password']
    else:
        dp_value = input("Enter DP value: ")
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=100 if not headless else 0)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Use the EXACT same login logic that works in meroshare_login()
            print(); print_progress(1, 7, "Navigating to Meroshare...")
            page.goto("https://meroshare.cdsc.com.np/#/login", wait_until="networkidle")
            time.sleep(2)
            
            # Select2 dropdown - click to open
            print_progress(2, 7, "Opening DP dropdown...")
            page.click("span.select2-selection")
            time.sleep(1)
            
            # Select the option - Select2 creates a results list in the DOM
            print_progress(3, 7, f"Selecting DP (value: {dp_value})...")
            # Wait for dropdown results to appear
            page.wait_for_selector(".select2-results", timeout=5000)
            
            # Type in search box and select
            search_box = page.query_selector("input.select2-search__field")
            if search_box:
                print(f"    → Searching for DP value {dp_value}...")
                search_box.type(dp_value)
                time.sleep(0.5)
                
                # Click the first result or press Enter
                first_result = page.query_selector("li.select2-results__option--highlighted, li.select2-results__option[aria-selected='true']")
                if first_result:
                    first_result.click()
                else:
                    page.keyboard.press("Enter")
            else:
                # Fallback: click by text
                try:
                    results = page.query_selector_all("li.select2-results__option")
                    for result in results:
                        if dp_value in result.inner_text():
                            result.click()
                            break
                except:
                    print("    ⚠ Using fallback selection method...")
                    page.select_option("select.select2-hidden-accessible", dp_value)
            
            time.sleep(1)
            
            # Fill username - try multiple possible selectors
            print_progress(4, 7, "Filling username...")
            username_selectors = [
                "input[formcontrolname='username']",
                "input#username",
                "input[placeholder*='User']"
            ]
            for selector in username_selectors:
                try:
                    page.fill(selector, username, timeout=2000)
                    break
                except:
                    continue
            
            # Fill password
            print_progress(5, 7, "Filling password...")
            password_selectors = [
                "input[formcontrolname='password']",
                "input[type='password']"
            ]
            for selector in password_selectors:
                try:
                    page.fill(selector, password, timeout=2000)
                    break
                except:
                    continue
            
            # Click login button
            print_progress(6, 7, "Clicking login button...")
            login_button_selectors = [
                "button.btn.sign-in",
                "button[type='submit']",
                "button:has-text('Login')"
            ]
            for selector in login_button_selectors:
                try:
                    page.click(selector, timeout=2000)
                    break
                except:
                    continue
            
            # Wait for login to complete - same as working login function
            print(); print_progress(7, 7, "Waiting for login...")
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except:
                print("    (networkidle timeout - page may still be loading)")
            
            time.sleep(2)
            
            # Wait for Angular routing
            print("Waiting for Angular routing...")
            try:
                page.wait_for_function("window.location.hash !== '#/login'", timeout=3000)
                time.sleep(0.5)
            except:
                print("    (route didn't change, but may still be logged in)")
            
            # Check if logged in
            current_url = page.url
            print(f"Current URL: {current_url}")
            
            if "#/login" not in current_url.lower() or page.query_selector("a[href*='dashboard']"):
                print("✓ Login successful!")
            else:
                print("⚠ Login may have failed, but continuing to portfolio...")
            
            # Navigate to Portfolio
            print("\n📊 Navigating to Portfolio page...")
            page.goto("https://meroshare.cdsc.com.np/#/portfolio", wait_until="networkidle")
            time.sleep(3)
            
            print("Fetching holdings...\n")
            
            # Extract portfolio data with correct selectors
            try:
                # Wait for the table to load (Angular app with _ngcontent attributes)
                print("Waiting for portfolio table to load...")
                page.wait_for_selector("table.table tbody tr", timeout=10000)
                time.sleep(2)
                
                # Get all data rows (excluding the total row)
                rows = page.query_selector_all("table.table tbody:first-of-type tr")
                
                if rows and len(rows) > 0:
                    print("\n" + "="*120)
                    print("YOUR PORTFOLIO HOLDINGS")
                    print("="*120)
                    print(f"{'#':<5} {'Scrip':<12} {'Balance':<12} {'Last Price':<12} {'Value(Last)':<15} {'LTP':<12} {'Value(LTP)':<15}")
                    print("-"*120)
                    
                    portfolio_data = []
                    total_value_last = 0
                    total_value_ltp = 0
                    
                    for row in rows:
                        cells = row.query_selector_all("td")
                        if cells and len(cells) >= 7:
                            # Extract each column
                            num = cells[0].inner_text().strip()
                            scrip = cells[1].inner_text().strip()
                            balance = cells[2].inner_text().strip()
                            last_price = cells[3].inner_text().strip()
                            value_last = cells[4].inner_text().strip()
                            ltp = cells[5].inner_text().strip()
                            value_ltp = cells[6].inner_text().strip()
                            
                            # Store as structured data
                            holding = {
                                "number": num,
                                "scrip": scrip,
                                "current_balance": balance,
                                "last_closing_price": last_price,
                                "value_as_of_last_price": value_last,
                                "last_transaction_price": ltp,
                                "value_as_of_ltp": value_ltp
                            }
                            portfolio_data.append(holding)
                            
                            # Print formatted row
                            print(f"{num:<5} {scrip:<12} {balance:<12} {last_price:<12} {value_last:<15} {ltp:<12} {value_ltp:<15}")
                    
                    # Get total row (from second tbody)
                    total_rows = page.query_selector_all("table.table tbody:last-of-type tr")
                    if total_rows and len(total_rows) > 0:
                        total_cells = total_rows[0].query_selector_all("td")
                        if total_cells and len(total_cells) >= 5:
                            total_last = total_cells[4].inner_text().strip()
                            total_ltp = total_cells[6].inner_text().strip() if len(total_cells) > 6 else ""
                            
                            print("-"*120)
                            print(f"{'TOTAL':<42} {total_last:<15} {'':<12} {total_ltp:<15}")
                    
                    print("="*120)
                    print(f"\n✓ Total holdings: {len(portfolio_data)} scrips")
                    
                    # Save to JSON with metadata
                    output_file = "portfolio_data.json"
                    output = {
                        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "total_scrips": len(portfolio_data),
                        "holdings": portfolio_data
                    }
                    with open(output_file, 'w') as f:
                        json.dump(output, f, indent=2)
                    print(f"✓ Portfolio data saved to {output_file}")
                    
                else:
                    print("⚠ No portfolio data found.")
                    screenshot_path = "portfolio_page.png"
                    page.screenshot(path=screenshot_path, full_page=True)
                    print(f"📸 Screenshot saved to {screenshot_path}")
                
            except Exception as e:
                print(f"⚠ Error extracting portfolio: {e}")
                screenshot_path = "portfolio_error.png"
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 Screenshot saved to {screenshot_path}")
            
            # Keep browser open in non-headless mode
            if not headless:
                print("\nBrowser will stay open for 30 seconds...")
                time.sleep(30)
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            if not headless:
                time.sleep(5)
        finally:
            browser.close()

def load_ipo_config():
    """Load IPO application configuration"""
    if not IPO_CONFIG_FILE.exists():
        print(f"\n⚠ IPO config file not found. Creating template...")
        default_config = {
            "applied_kitta": 10,
            "crn_number": "YOUR_CRN_NUMBER_HERE"
        }
        with open(IPO_CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"✓ Created {IPO_CONFIG_FILE}")
        print(f"⚠ Please edit {IPO_CONFIG_FILE} with your actual CRN number before applying!\n")
        return default_config
    
    with open(IPO_CONFIG_FILE, 'r') as f:
        return json.load(f)

def apply_ipo(auto_load=True, headless=False):
    """
    Complete IPO application automation with family member selection
    
    Args:
        auto_load: Load credentials from config file
        headless: Run browser in headless mode (no GUI)
    """
    if auto_load:
        # Select family member
        member = select_family_member()
        if not member:
            print("\n✗ No member selected. Exiting...")
            return
        
        dp_value = member['dp_value']
        username = member['username']
        password = member['password']
        transaction_pin = member['transaction_pin']
        applied_kitta = member['applied_kitta']
        crn_number = member['crn_number']
        member_name = member['name']
    else:
        member_name = "Manual Entry"
        dp_value = input("Enter DP value: ")
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
        transaction_pin = getpass.getpass("Enter 4-digit transaction PIN: ")
        applied_kitta = int(input("Applied Kitta: ").strip() or "10")
        crn_number = input("CRN Number: ").strip()
    
    if not crn_number:
        print(f"\n✗ CRN number is required!")
        return
    
    print(f"\n✓ Applying IPO for: {member_name}")
    print(f"✓ Kitta: {applied_kitta} | CRN: {crn_number}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=100 if not headless else 0)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # ========== PHASE 1: LOGIN ==========
            print("\n" + "="*60)
            print("PHASE 1: LOGIN")
            print("="*60)
            
            print(); print_progress(1, 6, "Navigating to Meroshare...")
            page.goto("https://meroshare.cdsc.com.np/#/login", wait_until="networkidle")
            time.sleep(2)
            
            print_progress(2, 6, "Opening DP dropdown...")
            page.click("span.select2-selection")
            time.sleep(1)
            
            print_progress(3, 6, f"Selecting DP (value: {dp_value})...")
            page.wait_for_selector(".select2-results", timeout=5000)
            
            search_box = page.query_selector("input.select2-search__field")
            if search_box:
                search_box.type(dp_value)
                time.sleep(0.5)
                first_result = page.query_selector("li.select2-results__option--highlighted, li.select2-results__option[aria-selected='true']")
                if first_result:
                    first_result.click()
                else:
                    page.keyboard.press("Enter")
            
            time.sleep(1)
            
            print_progress(4, 6, "Filling username...")
            username_selectors = [
                "input[formcontrolname='username']",
                "input#username",
                "input[placeholder*='User']"
            ]
            for selector in username_selectors:
                try:
                    page.fill(selector, username, timeout=2000)
                    break
                except:
                    continue
            
            print_progress(5, 6, "Filling password...")
            password_selectors = [
                "input[formcontrolname='password']",
                "input[type='password']"
            ]
            for selector in password_selectors:
                try:
                    page.fill(selector, password, timeout=2000)
                    break
                except:
                    continue
            
            print_progress(6, 6, "Clicking login button...")
            login_button_selectors = [
                "button.btn.sign-in",
                "button[type='submit']",
                "button:has-text('Login')"
            ]
            for selector in login_button_selectors:
                try:
                    page.click(selector, timeout=2000)
                    break
                except:
                    continue
            
            print("\nWaiting for login...")
            try:
                page.wait_for_function("window.location.hash !== '#/login'", timeout=8000)
                time.sleep(2)
            except:
                print("    (timeout, but may still be logged in)")
            
            if "#/login" not in page.url.lower():
                print("✓ Login successful!")
            else:
                print("⚠ Login may have failed")
                page.screenshot(path="login_failed.png")
                return
            
            # ========== PHASE 2: FETCH AVAILABLE IPOs ==========
            print("\n" + "="*60)
            print("PHASE 2: FETCH AVAILABLE IPOs")
            print("="*60)
            
            print("\nNavigating to ASBA page...")
            page.goto("https://meroshare.cdsc.com.np/#/asba", wait_until="networkidle")
            time.sleep(3)
            
            print("Fetching IPO list...\n")
            
            try:
                page.wait_for_selector(".company-list", timeout=10000)
                time.sleep(2)
            except Exception as e:
                print("⚠ No IPOs currently available on Meroshare")
                print("✗ Cannot proceed with IPO application\n")
                
                try:
                    no_data = page.query_selector("text=No Data Available")
                    if no_data:
                        print("→ Meroshare shows: 'No Data Available'")
                except:
                    pass
                
                page.screenshot(path="no_ipos_available.png")
                print("📸 Screenshot saved: no_ipos_available.png\n")
                
                if not headless:
                    print("Browser will stay open for 20 seconds...")
                    time.sleep(20)
                
                return
            
            company_rows = page.query_selector_all(".company-list")
            
            available_ipos = []
            for idx, row in enumerate(company_rows, 1):
                try:
                    company_name_elem = row.query_selector(".company-name span")
                    share_type_elem = row.query_selector(".share-of-type")
                    share_group_elem = row.query_selector(".isin")
                    
                    if company_name_elem and share_type_elem and share_group_elem:
                        company_name = company_name_elem.inner_text().strip()
                        share_type = share_type_elem.inner_text().strip()
                        share_group = share_group_elem.inner_text().strip()
                        
                        if "ipo" in share_type.lower() and "ordinary" in share_group.lower():
                            # Check for both Apply and Edit buttons
                            apply_button = row.query_selector("button.btn-issue")
                            
                            # Check if IPO is already applied (button shows 'Edit')
                            is_applied = False
                            button_text = ""
                            if apply_button:
                                button_text = apply_button.inner_text().strip().lower()
                                is_applied = "edit" in button_text or "view" in button_text
                            
                            if apply_button:
                                available_ipos.append({
                                    "index": len(available_ipos) + 1,
                                    "company_name": company_name,
                                    "share_type": share_type,
                                    "share_group": share_group,
                                    "element": row,
                                    "apply_button": apply_button,
                                    "is_applied": is_applied,
                                    "button_text": button_text
                                })
                except Exception as e:
                    print(f"    Error parsing row {idx}: {e}")
            
            if not available_ipos:
                print("✗ No IPOs (Ordinary Shares) available to apply!")
                page.screenshot(path="no_ipos_found.png")
                return
            
            print("="*60)
            print("AVAILABLE IPOs (Ordinary Shares)")
            print("="*60)
            for ipo in available_ipos:
                print(f"{ipo['index']}. {ipo['company_name']}")
                print(f"   Type: {ipo['share_type']} | Group: {ipo['share_group']}")
                print()
            print("="*60)
            
            if not headless:
                selection = input(f"\nEnter IPO number to apply (1-{len(available_ipos)}): ").strip()
                try:
                    selected_idx = int(selection) - 1
                    if selected_idx < 0 or selected_idx >= len(available_ipos):
                        print("✗ Invalid selection!")
                        return
                except ValueError:
                    print("✗ Invalid input!")
                    return
            else:
                selected_idx = 0
                print(f"\n→ Auto-selecting IPO #1: {available_ipos[0]['company_name']}")
            
            selected_ipo = available_ipos[selected_idx]
            print(f"\n✓ Selected: {selected_ipo['company_name']}\n")
            
            # Check if IPO is already applied
            if selected_ipo.get('is_applied', False):
                print(f"⚠ IPO already applied for this account!")
                print(f"   Button shows: '{selected_ipo.get('button_text', 'N/A').title()}'")
                print(f"   (Edit button indicates IPO was already applied)")
                page.screenshot(path="ipo_already_applied.png")
                print("📸 Screenshot saved: ipo_already_applied.png\n")
                
                if not headless:
                    print("Browser will stay open for 20 seconds...")
                    time.sleep(20)
                return
            
            print("Clicking Apply button...")
            selected_ipo['apply_button'].click()
            time.sleep(3)
            
            page.screenshot(path="ipo_form_loaded.png")
            print("✓ IPO form loaded")
            
            # ========== PHASE 3: FILL IPO APPLICATION FORM ==========
            print("\n" + "="*60)
            print("PHASE 3: FILL APPLICATION FORM")
            print("="*60)
            
            page.wait_for_selector("select#selectBank", timeout=10000)
            time.sleep(2)
            
            print(); print_progress(1, 5, "Selecting bank...")
            bank_options = page.query_selector_all("select#selectBank option")
            valid_banks = [opt for opt in bank_options if opt.get_attribute("value")]
            
            if len(valid_banks) == 1:
                bank_value = valid_banks[0].get_attribute("value")
                bank_name = valid_banks[0].inner_text().strip()
                print(f"    → Auto-selected: {bank_name}")
                page.select_option("select#selectBank", bank_value)
            elif len(valid_banks) > 1:
                print(f"    → Found {len(valid_banks)} banks, selecting first one")
                bank_value = valid_banks[0].get_attribute("value")
                page.select_option("select#selectBank", bank_value)
            else:
                print("    ✗ No banks found!")
                return
            
            time.sleep(2)
            
            print(); print_progress(2, 5, "Selecting account number...")
            page.wait_for_selector("select#accountNumber", timeout=5000)
            account_options = page.query_selector_all("select#accountNumber option")
            valid_accounts = [opt for opt in account_options if opt.get_attribute("value")]
            
            if len(valid_accounts) == 1:
                account_value = valid_accounts[0].get_attribute("value")
                account_text = valid_accounts[0].inner_text().strip()
                print(f"    → Auto-selected: {account_text}")
                page.select_option("select#accountNumber", account_value)
            elif len(valid_accounts) > 1:
                print(f"    → Found {len(valid_accounts)} accounts, selecting first one")
                account_value = valid_accounts[0].get_attribute("value")
                page.select_option("select#accountNumber", account_value)
            else:
                print("    ✗ No accounts found!")
                return
            
            time.sleep(2)
            
            print(); print_progress(3, 5, "Waiting for branch to auto-fill...")
            time.sleep(1)
            branch_value = page.input_value("input#selectBranch")
            if branch_value:
                print(f"    → Branch: {branch_value}")
            
            print(); print_progress(4, 5, f"Filling applied kitta: {applied_kitta}")
            page.fill("input#appliedKitta", str(applied_kitta))
            time.sleep(1)
            
            amount_value = page.input_value("input#amount")
            print(f"    → Amount: {amount_value}")
            
            print(); print_progress(5, 5, f"Filling CRN: {crn_number}")
            page.fill("input#crnNumber", crn_number)
            time.sleep(1)
            
            page.screenshot(path="form_filled.png")
            print("\n✓ Form filled successfully")
            
            # ========== PHASE 4: ACCEPT DISCLAIMER & PROCEED ==========
            print("\n" + "="*60)
            print("PHASE 4: ACCEPT DISCLAIMER & PROCEED")
            print("="*60)
            
            print("\nChecking disclaimer checkbox...")
            disclaimer_checkbox = page.query_selector("input#disclaimer")
            if disclaimer_checkbox:
                disclaimer_checkbox.check()
                print("✓ Disclaimer accepted")
            else:
                print("⚠ Disclaimer checkbox not found")
            
            time.sleep(1)
            
            print("\nClicking Proceed button...")
            proceed_button = page.query_selector("button.btn-primary[type='submit']")
            if proceed_button:
                proceed_button.click()
                print("✓ Clicked Proceed")
            else:
                print("✗ Proceed button not found!")
                page.screenshot(path="proceed_error.png")
                return
            
            time.sleep(3)
            
            # ========== PHASE 5: ENTER TRANSACTION PIN ==========
            print("\n" + "="*60)
            print("PHASE 5: ENTER TRANSACTION PIN")
            print("="*60)
            
            print("\nWaiting for PIN entry screen...")
            page.wait_for_selector("input#transactionPIN", timeout=10000)
            time.sleep(2)
            
            page.screenshot(path="pin_screen.png")
            print("✓ PIN entry screen loaded")
            
            print(f"\nEntering transaction PIN...")
            page.fill("input#transactionPIN", transaction_pin)
            print("✓ PIN entered")
            
            time.sleep(1)
            
            # ========== PHASE 6: FINAL SUBMISSION ==========
            print("\n" + "="*60)
            print("PHASE 6: FINAL SUBMISSION")
            print("="*60)
            
            if not headless:
                confirm = input("\n⚠ Ready to submit application? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("✗ Application cancelled by user")
                    return
            
            print("\nSubmitting application...")
            
            # Wait a bit more for the button to be fully ready
            time.sleep(2)
            
            # Try multiple methods to click the Apply button
            clicked = False
            
            # Method 1: Find button with text "Apply" (more reliable)
            try:
                apply_buttons = page.query_selector_all("button:has-text('Apply')")
                for btn in apply_buttons:
                    if btn.is_visible() and not btn.is_disabled():
                        btn.click()
                        print("✓ Submit button clicked (Method 1)")
                        clicked = True
                        break
            except Exception as e:
                print(f"    Method 1 failed: {e}")
            
            # Method 2: Find by class and type in the confirm page
            if not clicked:
                try:
                    submit_button = page.query_selector("div.confirm-page-btn button.btn-primary[type='submit']")
                    if submit_button and submit_button.is_visible():
                        submit_button.click()
                        print("✓ Submit button clicked (Method 2)")
                        clicked = True
                except Exception as e:
                    print(f"    Method 2 failed: {e}")
            
            # Method 3: Find any submit button in the confirmation section
            if not clicked:
                try:
                    submit_button = page.query_selector("button.btn-gap.btn-primary[type='submit']")
                    if submit_button and submit_button.is_visible():
                        submit_button.click()
                        print("✓ Submit button clicked (Method 3)")
                        clicked = True
                except Exception as e:
                    print(f"    Method 3 failed: {e}")
            
            # Method 4: Force click using JavaScript
            if not clicked:
                try:
                    page.evaluate("""
                        const buttons = document.querySelectorAll('button');
                        for (const btn of buttons) {
                            if (btn.textContent.includes('Apply') && btn.type === 'submit') {
                                btn.click();
                                break;
                            }
                        }
                    """)
                    print("✓ Submit button clicked (Method 4 - JavaScript)")
                    clicked = True
                except Exception as e:
                    print(f"    Method 4 failed: {e}")
            
            if not clicked:
                print("✗ Failed to click submit button!")
                page.screenshot(path="submit_error.png")
                print("📸 Screenshot saved: submit_error.png")
                print("\nPlease click the Apply button manually.")
                if not headless:
                    time.sleep(30)
                return
            
            time.sleep(5)
            
            page.screenshot(path="submission_result.png")
            print("\n✓✓✓ APPLICATION SUBMITTED! ✓✓✓")
            print(f"📸 Screenshots saved for verification")
            print(f"Current URL: {page.url}")
            
            if not headless:
                print("\nBrowser will stay open for 30 seconds...")
                time.sleep(30)
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            page.screenshot(path="error.png")
            if not headless:
                time.sleep(10)
        finally:
            browser.close()

def get_portfolio_for_member(member, headless=False):
    """Get portfolio for a specific family member"""
    print(f"\nFetching portfolio for: {member['name']}...")
    
    # Call existing get_portfolio but with member's credentials passed directly
    # We'll modify it to accept parameters
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=100 if not headless else 0)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            dp_value = member['dp_value']
            username = member['username']
            password = member['password']
            
            print(); print_progress(1, 7, "Navigating to Meroshare...")
            page.goto("https://meroshare.cdsc.com.np/#/login", wait_until="networkidle")
            time.sleep(2)
            
            print_progress(2, 7, "Opening DP dropdown...")
            page.click("span.select2-selection")
            time.sleep(1)
            
            print_progress(3, 7, f"Selecting DP...")
            page.wait_for_selector(".select2-results", timeout=5000)
            search_box = page.query_selector("input.select2-search__field")
            if search_box:
                search_box.type(dp_value)
                time.sleep(0.5)
                first_result = page.query_selector("li.select2-results__option--highlighted, li.select2-results__option[aria-selected='true']")
                if first_result:
                    first_result.click()
                else:
                    page.keyboard.press("Enter")
            time.sleep(1)
            
            print_progress(4, 7, "Filling username...")
            username_selectors = [
                "input[formcontrolname='username']",
                "input#username",
                "input[placeholder*='User']"
            ]
            for selector in username_selectors:
                try:
                    page.fill(selector, username, timeout=2000)
                    break
                except:
                    continue
            
            print_progress(5, 7, "Filling password...")
            password_selectors = [
                "input[formcontrolname='password']",
                "input[type='password']"
            ]
            for selector in password_selectors:
                try:
                    page.fill(selector, password, timeout=2000)
                    break
                except:
                    continue
            
            print_progress(6, 7, "Clicking login...")
            login_button_selectors = [
                "button.btn.sign-in",
                "button[type='submit']",
                "button:has-text('Login')"
            ]
            for selector in login_button_selectors:
                try:
                    page.click(selector, timeout=2000)
                    break
                except:
                    continue
            
            print(); print_progress(7, 7, "Waiting for login...")
            page.wait_for_load_state("networkidle", timeout=8000)
            time.sleep(2)
            
            print(f"✓ Logged in as {member['name']}")
            
            # Navigate to portfolio
            print("\n📊 Navigating to Portfolio...")
            page.goto("https://meroshare.cdsc.com.np/#/portfolio", wait_until="networkidle")
            time.sleep(3)
            
            print("Fetching holdings...\n")
            page.wait_for_selector("table.table tbody tr", timeout=10000)
            time.sleep(2)
            
            rows = page.query_selector_all("table.table tbody:first-of-type tr")
            
            if rows and len(rows) > 0:
                print("\n" + "="*120)
                print(f"PORTFOLIO: {member['name'].upper()}")
                print("="*120)
                print(f"{'#':<5} {'Scrip':<12} {'Balance':<12} {'Last Price':<12} {'Value(Last)':<15} {'LTP':<12} {'Value(LTP)':<15}")
                print("-"*120)
                
                total_value_ltp = 0.0
                
                for row in rows:
                    cells = row.query_selector_all("td")
                    if cells and len(cells) >= 7:
                        num = cells[0].inner_text().strip()
                        scrip = cells[1].inner_text().strip()
                        balance = cells[2].inner_text().strip()
                        last_price = cells[3].inner_text().strip()
                        value_last = cells[4].inner_text().strip()
                        ltp = cells[5].inner_text().strip()
                        value_ltp = cells[6].inner_text().strip()
                        
                        # Calculate total
                        try:
                            value_ltp_num = float(value_ltp.replace(',', ''))
                            total_value_ltp += value_ltp_num
                        except:
                            pass
                        
                        print(f"{num:<5} {scrip:<12} {balance:<12} {last_price:<12} {value_last:<15} {ltp:<12} {value_ltp:<15}")
                
                print("-"*120)
                print(f"{'TOTAL':<71} Rs. {total_value_ltp:,.2f}")
                print("="*120)
            
            if not headless:
                print("\nBrowser will stay open for 20 seconds...")
                time.sleep(20)
                
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            browser.close()

def test_login_for_member(member, headless=True):
    """Test login for a specific family member"""
    print(f"\nTesting login for: {member['name']}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=100 if not headless else 0)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            dp_value = member['dp_value']
            username = member['username']
            password = member['password']
            
            print(); print_progress(1, 7, "Navigating to Meroshare...")
            page.goto("https://meroshare.cdsc.com.np/#/login", wait_until="networkidle")
            time.sleep(2)
            
            print_progress(2, 7, "Opening DP dropdown...")
            page.click("span.select2-selection")
            time.sleep(1)
            
            print_progress(3, 7, f"Selecting DP (value: {dp_value})...")
            page.wait_for_selector(".select2-results", timeout=5000)
            
            search_box = page.query_selector("input.select2-search__field")
            if search_box:
                print(f"    → Searching for DP value {dp_value}...")
                search_box.type(dp_value)
                time.sleep(0.5)
                
                first_result = page.query_selector("li.select2-results__option--highlighted, li.select2-results__option[aria-selected='true']")
                if first_result:
                    first_result.click()
                else:
                    page.keyboard.press("Enter")
            else:
                try:
                    results = page.query_selector_all("li.select2-results__option")
                    for result in results:
                        if dp_value in result.inner_text():
                            result.click()
                            break
                except:
                    print("    ⚠ Using fallback selection method...")
                    page.select_option("select.select2-hidden-accessible", dp_value)
            
            time.sleep(1)
            
            print_progress(4, 7, "Filling username...")
            username_selectors = [
                "input[formcontrolname='username']",
                "input#username",
                "input[placeholder*='User']"
            ]
            for selector in username_selectors:
                try:
                    page.fill(selector, username, timeout=2000)
                    break
                except:
                    continue
            
            print_progress(5, 7, "Filling password...")
            password_selectors = [
                "input[formcontrolname='password']",
                "input[type='password']"
            ]
            for selector in password_selectors:
                try:
                    page.fill(selector, password, timeout=2000)
                    break
                except:
                    continue
            
            print_progress(6, 7, "Clicking login button...")
            login_button_selectors = [
                "button.btn.sign-in",
                "button[type='submit']",
                "button:has-text('Login')"
            ]
            for selector in login_button_selectors:
                try:
                    page.click(selector, timeout=2000)
                    break
                except:
                    continue
            
            print(); print_progress(7, 7, "Waiting for login...")
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except:
                print("    (networkidle timeout - page may still be loading)")
            
            time.sleep(2)
            
            try:
                page.wait_for_function("window.location.hash !== '#/login'", timeout=3000)
                time.sleep(0.5)
            except:
                print("    (route didn't change, but may still be logged in)")
            
            current_url = page.url
            print(f"\nCurrent URL: {current_url}")
            
            if "#/login" not in current_url.lower():
                print(f"\n✓✓✓ LOGIN SUCCESSFUL for {member['name']}! ✓✓✓")
            else:
                print(f"\n⚠ Login may have failed for {member['name']}")
                page.screenshot(path=f"login_test_{member['name']}.png")
            
            if not headless:
                print("\nBrowser will stay open for 20 seconds...")
                time.sleep(20)
                
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

def apply_ipo_for_all_members(headless=True):
    """Apply IPO for all family members - Sequential Login + Sequential Application"""
    
    # Load family members
    config = load_family_members()
    members = config.get('members', [])
    
    if not members:
        print("\n⚠ No family members found. Add members first!\n")
        return
    
    # Display members
    print("\n" + "="*60)
    print("FAMILY MEMBERS TO APPLY IPO")
    print("="*60)
    for idx, member in enumerate(members, 1):
        print(f"{idx}. {member['name']} - Kitta: {member['applied_kitta']} | CRN: {member['crn_number']}")
    print("="*60)
    
    # Confirmation
    confirm = input(f"\n⚠ Apply IPO for ALL {len(members)} members? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("✗ Operation cancelled")
        return
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=100 if not headless else 0)
        context = browser.new_context()
        
        try:
            # ========== PHASE 1: CREATE TABS & LOGIN ALL MEMBERS ==========
            print("\n" + "="*60)
            print("PHASE 1: MULTI-TAB LOGIN (ALL MEMBERS)")
            print("="*60)
            
            pages_data = []
            
            # Create tabs and login sequentially (but keep all tabs open)
            print(f"\n🚀 Opening {len(members)} tabs and logging in...\n")
            
            for idx, member in enumerate(members, 1):
                member_name = member['name']
                page = context.new_page()
                
                try:
                    print(f"[Tab {idx}] Starting login for: {member_name}")
                    
                    # Navigate
                    page.goto("https://meroshare.cdsc.com.np/#/login", wait_until="networkidle")
                    time.sleep(2)
                    
                    # Select DP
                    page.click("span.select2-selection")
                    time.sleep(1)
                    page.wait_for_selector(".select2-results", timeout=5000)
                    
                    search_box = page.query_selector("input.select2-search__field")
                    if search_box:
                        search_box.type(member['dp_value'])
                        time.sleep(0.5)
                        first_result = page.query_selector("li.select2-results__option--highlighted, li.select2-results__option[aria-selected='true']")
                        if first_result:
                            first_result.click()
                        else:
                            page.keyboard.press("Enter")
                    time.sleep(1)
                    
                    # Fill username
                    username_selectors = [
                        "input[formcontrolname='username']",
                        "input#username",
                        "input[placeholder*='User']"
                    ]
                    for selector in username_selectors:
                        try:
                            page.fill(selector, member['username'], timeout=2000)
                            break
                        except:
                            continue
                    
                    # Fill password
                    password_selectors = [
                        "input[formcontrolname='password']",
                        "input[type='password']"
                    ]
                    for selector in password_selectors:
                        try:
                            page.fill(selector, member['password'], timeout=2000)
                            break
                        except:
                            continue
                    
                    # Click login
                    login_button_selectors = [
                        "button.btn.sign-in",
                        "button[type='submit']",
                        "button:has-text('Login')"
                    ]
                    for selector in login_button_selectors:
                        try:
                            page.click(selector, timeout=2000)
                            break
                        except:
                            continue
                    
                    # Wait for login
                    try:
                        page.wait_for_function("window.location.hash !== '#/login'", timeout=8000)
                        time.sleep(2)
                    except:
                        time.sleep(2)
                    
                    # Check if logged in
                    if "#/login" not in page.url.lower():
                        print(f"✓ [Tab {idx}] Login successful: {member_name}")
                        pages_data.append({"success": True, "member": member, "page": page, "tab_index": idx})
                    else:
                        print(f"✗ [Tab {idx}] Login failed: {member_name}")
                        pages_data.append({"success": False, "member": member, "page": page, "tab_index": idx, "error": "Login failed"})
                        
                except Exception as e:
                    print(f"✗ [Tab {idx}] Error logging in {member_name}: {e}")
                    pages_data.append({"success": False, "member": member, "page": page, "tab_index": idx, "error": str(e)})
            
            # Summary of login phase
            successful_logins = [p for p in pages_data if p['success']]
            failed_logins = [p for p in pages_data if not p['success']]
            
            print("\n" + "="*60)
            print(f"LOGIN SUMMARY: {len(successful_logins)}/{len(members)} successful")
            print("="*60)
            for p in successful_logins:
                print(f"✓ {p['member']['name']}")
            if failed_logins:
                for p in failed_logins:
                    print(f"✗ {p['member']['name']} - {p.get('error', 'Unknown error')}")
            print("="*60)
            
            if not successful_logins:
                print("\n✗ No successful logins. Exiting...")
                return
            
            # Continue with successful logins only
            if failed_logins:
                proceed = input(f"\n⚠ {len(failed_logins)} login(s) failed. Continue with {len(successful_logins)} member(s)? (yes/no): ").strip().lower()
                if proceed != 'yes':
                    print("✗ Operation cancelled")
                    return
            
            # ========== PHASE 2: SEQUENTIAL IPO APPLICATION ==========
            print("\n" + "="*60)
            print("PHASE 2: IPO APPLICATION (SEQUENTIAL)")
            print("="*60)
            
            # Use first successful login to select IPO
            first_page = successful_logins[0]['page']
            
            print("\nNavigating to IPO page to select IPO...")
            first_page.goto("https://meroshare.cdsc.com.np/#/asba", wait_until="networkidle")
            time.sleep(3)
            
            print("Fetching available IPOs...\n")
            
            # Check if there are any IPOs available
            try:
                first_page.wait_for_selector(".company-list", timeout=10000)
                time.sleep(2)
            except Exception as e:
                print("⚠ No IPOs currently available on Meroshare")
                print("✗ Cannot proceed with IPO application\n")
                
                # Check if there's a "no data" message
                try:
                    no_data = first_page.query_selector("text=No Data Available")
                    if no_data:
                        print("→ Meroshare shows: 'No Data Available'")
                except:
                    pass
                
                first_page.screenshot(path="no_ipos_available.png")
                print("📸 Screenshot saved: no_ipos_available.png\n")
                
                if not headless:
                    print("Browser will stay open for 20 seconds...")
                    time.sleep(20)
                
                return
            
            company_rows = first_page.query_selector_all(".company-list")
            
            available_ipos = []
            for idx, row in enumerate(company_rows, 1):
                try:
                    company_name_elem = row.query_selector(".company-name span")
                    share_type_elem = row.query_selector(".share-of-type")
                    share_group_elem = row.query_selector(".isin")
                    
                    if company_name_elem and share_type_elem and share_group_elem:
                        company_name = company_name_elem.inner_text().strip()
                        share_type = share_type_elem.inner_text().strip()
                        share_group = share_group_elem.inner_text().strip()
                        
                        if "ipo" in share_type.lower() and "ordinary" in share_group.lower():
                            available_ipos.append({
                                "index": len(available_ipos) + 1,
                                "company_name": company_name,
                                "share_type": share_type,
                                "share_group": share_group
                            })
                except Exception as e:
                    pass
            
            if not available_ipos:
                print("✗ No IPOs available to apply!")
                return
            
            print("="*60)
            print("AVAILABLE IPOs (Ordinary Shares)")
            print("="*60)
            for ipo in available_ipos:
                print(f"{ipo['index']}. {ipo['company_name']}")
                print(f"   Type: {ipo['share_type']} | Group: {ipo['share_group']}")
                print()
            print("="*60)
            
            if not headless:
                selection = input(f"\nSelect IPO to apply for all members (1-{len(available_ipos)}): ").strip()
                try:
                    selected_idx = int(selection) - 1
                    if selected_idx < 0 or selected_idx >= len(available_ipos):
                        print("✗ Invalid selection!")
                        return
                except ValueError:
                    print("✗ Invalid input!")
                    return
            else:
                selected_idx = 0
            
            selected_ipo = available_ipos[selected_idx]
            print(f"\n✓ Selected IPO: {selected_ipo['company_name']}")
            print(f"\n⚠ Will apply this IPO for {len(successful_logins)} member(s)\n")
            
            # Apply IPO for each member sequentially
            application_results = []
            
            for page_data in successful_logins:
                member = page_data['member']
                page = page_data['page']
                tab_index = page_data['tab_index']
                member_name = member['name']
                
                print("\n" + "="*60)
                print(f"[Tab {tab_index}] APPLYING FOR: {member_name}")
                print("="*60)
                
                try:
                    # Navigate to ASBA
                    print(f"[Tab {tab_index}] Navigating to IPO page...")
                    page.goto("https://meroshare.cdsc.com.np/#/asba", wait_until="networkidle")
                    time.sleep(3)
                    
                    # Find and click the IPO
                    page.wait_for_selector(".company-list", timeout=10000)
                    time.sleep(2)
                    
                    company_rows = page.query_selector_all(".company-list")
                    ipo_found = False
                    already_applied = False
                    
                    for row in company_rows:
                        try:
                            company_name_elem = row.query_selector(".company-name span")
                            if company_name_elem and selected_ipo['company_name'] in company_name_elem.inner_text():
                                apply_button = row.query_selector("button.btn-issue")
                                if apply_button:
                                    # Check button text to see if already applied (shows 'Edit')
                                    button_text = apply_button.inner_text().strip().lower()
                                    
                                    if "edit" in button_text or "view" in button_text:
                                        print(f"[Tab {tab_index}] ⚠ IPO already applied (button shows: '{button_text.title()}')")
                                        already_applied = True
                                        ipo_found = True
                                        break
                                    else:
                                        print(f"[Tab {tab_index}] Clicking Apply button (button shows: '{button_text.title()}')...")
                                        apply_button.click()
                                        ipo_found = True
                                        break
                        except:
                            continue
                    
                    if not ipo_found:
                        raise Exception("IPO not found in the list")
                    
                    if already_applied:
                        print(f"[Tab {tab_index}] ✓ Skipping - IPO already applied for {member_name}")
                        application_results.append({"member": member_name, "success": True, "status": "already_applied"})
                        continue
                    
                    time.sleep(3)
                    
                    # Fill form
                    print(f"[Tab {tab_index}] Filling application form...")
                    page.wait_for_selector("select#selectBank", timeout=10000)
                    time.sleep(2)
                    
                    # Select bank
                    bank_options = page.query_selector_all("select#selectBank option")
                    valid_banks = [opt for opt in bank_options if opt.get_attribute("value")]
                    if valid_banks:
                        page.select_option("select#selectBank", valid_banks[0].get_attribute("value"))
                    time.sleep(2)
                    
                    # Select account
                    page.wait_for_selector("select#accountNumber", timeout=5000)
                    account_options = page.query_selector_all("select#accountNumber option")
                    valid_accounts = [opt for opt in account_options if opt.get_attribute("value")]
                    if valid_accounts:
                        page.select_option("select#accountNumber", valid_accounts[0].get_attribute("value"))
                    time.sleep(2)
                    
                    # Fill kitta
                    print(f"[Tab {tab_index}] Kitta: {member['applied_kitta']}")
                    page.fill("input#appliedKitta", str(member['applied_kitta']))
                    time.sleep(1)
                    
                    # Fill CRN
                    print(f"[Tab {tab_index}] CRN: {member['crn_number']}")
                    page.fill("input#crnNumber", member['crn_number'])
                    time.sleep(1)
                    
                    # Accept disclaimer
                    disclaimer_checkbox = page.query_selector("input#disclaimer")
                    if disclaimer_checkbox:
                        disclaimer_checkbox.check()
                    time.sleep(1)
                    
                    # Click proceed
                    print(f"[Tab {tab_index}] Clicking Proceed...")
                    proceed_button = page.query_selector("button.btn-primary[type='submit']")
                    if proceed_button:
                        proceed_button.click()
                    time.sleep(3)
                    
                    # Enter PIN
                    print(f"[Tab {tab_index}] Entering transaction PIN...")
                    page.wait_for_selector("input#transactionPIN", timeout=10000)
                    time.sleep(2)
                    page.fill("input#transactionPIN", member['transaction_pin'])
                    time.sleep(2)
                    
                    # Submit
                    print(f"[Tab {tab_index}] Submitting application...")
                    clicked = False
                    
                    # Try multiple methods to click Apply button
                    try:
                        apply_buttons = page.query_selector_all("button:has-text('Apply')")
                        for btn in apply_buttons:
                            if btn.is_visible() and not btn.is_disabled():
                                btn.click()
                                clicked = True
                                break
                    except:
                        pass
                    
                    if not clicked:
                        try:
                            submit_button = page.query_selector("div.confirm-page-btn button.btn-primary[type='submit']")
                            if submit_button and submit_button.is_visible():
                                submit_button.click()
                                clicked = True
                        except:
                            pass
                    
                    if not clicked:
                        try:
                            page.evaluate("""
                                const buttons = document.querySelectorAll('button');
                                for (const btn of buttons) {
                                    if (btn.textContent.includes('Apply') && btn.type === 'submit') {
                                        btn.click();
                                        break;
                                    }
                                }
                            """)
                            clicked = True
                        except:
                            pass
                    
                    if not clicked:
                        raise Exception("Failed to click submit button")
                    
                    time.sleep(5)
                    
                    print(f"✓ [Tab {tab_index}] Application submitted for {member_name}!")
                    application_results.append({"member": member_name, "success": True})
                    
                except Exception as e:
                    print(f"✗ [Tab {tab_index}] Failed for {member_name}: {e}")
                    application_results.append({"member": member_name, "success": False, "error": str(e)})
                    page.screenshot(path=f"error_{member_name}.png")
            
            # ========== FINAL SUMMARY ==========
            print("\n" + "="*60)
            print("FINAL SUMMARY")
            print("="*60)
            print(f"IPO: {selected_ipo['company_name']}")
            print()
            
            successful_apps = [r for r in application_results if r['success']]
            failed_apps = [r for r in application_results if not r['success']]
            already_applied_apps = [r for r in successful_apps if r.get('status') == 'already_applied']
            newly_applied_apps = [r for r in successful_apps if r.get('status') != 'already_applied']
            
            print(f"✓ SUCCESSFUL: {len(successful_apps)}/{len(application_results)}")
            if newly_applied_apps:
                print(f"\n  Newly Applied ({len(newly_applied_apps)}):")
                for r in newly_applied_apps:
                    print(f"  ✓ {r['member']}")
            
            if already_applied_apps:
                print(f"\n  Already Applied ({len(already_applied_apps)}):")
                for r in already_applied_apps:
                    print(f"  ⚠ {r['member']} (skipped)")
            
            if failed_apps:
                print(f"\n✗ FAILED: {len(failed_apps)}")
                for r in failed_apps:
                    print(f"  ✗ {r['member']} - {r.get('error', 'Unknown error')}")
            
            print("="*60)
            
            if not headless:
                print("\nBrowser will stay open for 60 seconds for verification...")
                time.sleep(60)
            
        except Exception as e:
            print(f"\n✗ Critical error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

def get_dp_list():
    """Fetch and display available DP list with values from API"""
    import requests
    
    try:
        print("\nFetching DP list from Meroshare API...")
        
        # Fetch data from API
        response = requests.get("https://webbackend.cdsc.com.np/api/meroShare/capital/")
        response.raise_for_status()
        
        dp_data = response.json()
        
        # Sort by name for better readability
        dp_data.sort(key=lambda x: x['name'])
        
        print("\n" + "="*80)
        print("AVAILABLE DEPOSITORY PARTICIPANTS (DPs)")
        print("="*80)
        print(f"{'ID':<6} {'Code':<8} {'Name'}")
        print("-"*80)
        
        for dp in dp_data:
            dp_id = dp['id']
            code = dp['code']
            name = dp['name']
            print(f"{dp_id:<6} {code:<8} {name}")
        
        print("="*80)
        print(f"Total DPs: {len(dp_data)}")
        print("\nNote: Use the ID (first column) when setting up credentials")
        print("      (e.g., 139 for CREATIVE SECURITIES, 146 for GLOBAL IME CAPITAL)\n")
        
    except requests.RequestException as e:
        print(f"✗ Error fetching DP list from API: {e}")
        print("  Please check your internet connection.\n")
    except Exception as e:
        print(f"✗ Unexpected error: {e}\n")

def main():
    """Main menu"""
    from nepse_cli import cmd_ipo, cmd_nepse, cmd_subidx, cmd_mktsum, cmd_topgl, cmd_stonk
    
    print("\n" + "="*50)
    print("    MEROSHARE FAMILY IPO AUTOMATION")
    print("="*50)
    print("\n📋 Portfolio & IPO Management:")
    print("1. Apply for IPO - Select family member")
    print("2. Add/Update family member")
    print("3. List all family members")
    print("4. Get Portfolio - Select member")
    print("5. Login (test) - Select member")
    print("6. View DP list")
    print("7. 🚀 Apply IPO for ALL family members (Multi-tab)")
    print("\n📊 Market Data:")
    print("8. View Open IPOs")
    print("9. View NEPSE Indices")
    print("10. View Sub-Indices")
    print("11. Market Summary")
    print("12. Top Gainers & Losers")
    print("13. Stock Details")
    print("\n0. Exit")
    
    choice = input("\nEnter your choice (0-13): ").strip()
    
    if choice == "1":
        apply_ipo(auto_load=True, headless=True)
    elif choice == "2":
        add_family_member()
    elif choice == "3":
        list_family_members()
        input("\nPress Enter to continue...")
    elif choice == "4":
        member = select_family_member()
        if member:
            get_portfolio_for_member(member, headless=True)
    elif choice == "5":
        member = select_family_member()
        if member:
            test_login_for_member(member, headless=True)
    elif choice == "6":
        get_dp_list()
    elif choice == "7":
        apply_ipo_for_all_members(headless=True)
    elif choice == "8":
        cmd_ipo()
        input("\nPress Enter to continue...")
    elif choice == "9":
        cmd_nepse()
        input("\nPress Enter to continue...")
    elif choice == "10":
        print("\nAvailable sub-indices: banking, development-bank, finance, hotels-and-tourism,")
        print("hydropower, investment, life-insurance, manufacturing-and-processing,")
        print("microfinance, non-life-insurance, others, trading")
        subidx_name = input("\nEnter sub-index name: ").strip()
        if subidx_name:
            cmd_subidx(subidx_name)
            input("\nPress Enter to continue...")
    elif choice == "11":
        cmd_mktsum()
        input("\nPress Enter to continue...")
    elif choice == "12":
        cmd_topgl()
        input("\nPress Enter to continue...")
    elif choice == "13":
        symbol = input("\nEnter stock symbol (e.g., NABIL): ").strip().upper()
        if symbol:
            cmd_stonk(symbol)
            input("\nPress Enter to continue...")
    elif choice == "0":
        print("Goodbye!")
        return
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()

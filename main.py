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
            
            page.wait_for_selector(".company-list", timeout=10000)
            time.sleep(2)
            
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
                            apply_button = row.query_selector("button.btn-issue")
                            if apply_button:
                                available_ipos.append({
                                    "index": len(available_ipos) + 1,
                                    "company_name": company_name,
                                    "share_type": share_type,
                                    "share_group": share_group,
                                    "element": row,
                                    "apply_button": apply_button
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
                        print(f"{num:<5} {scrip:<12} {balance:<12} {last_price:<12} {value_last:<15} {ltp:<12} {value_ltp:<15}")
                
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

def get_dp_list():
    """Fetch and display available DP list with values"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("\nFetching DP list from Meroshare...")
            page.goto("https://meroshare.cdsc.com.np/#/login", wait_until="networkidle")
            time.sleep(3)
            
            # Get all options from the hidden select
            options = page.query_selector_all("select.select2-hidden-accessible option")
            
            print("\n" + "="*70)
            print("AVAILABLE DEPOSITORY PARTICIPANTS (DPs)")
            print("="*70)
            print(f"{'Value':<8} {'Name'}")
            print("-"*70)
            
            dp_list = []
            for option in options:
                value = option.get_attribute("value")
                text = option.inner_text().strip()
                if value and value != "":
                    dp_list.append((value, text))
                    print(f"{value:<8} {text}")
            
            print("="*70)
            print(f"Total DPs: {len(dp_list)}")
            print("\nNote: Use the VALUE (first column) when setting up credentials\n")
            
        except Exception as e:
            print(f"Error fetching DP list: {e}")
        finally:
            browser.close()

def main():
    """Main menu"""
    print("\n" + "="*50)
    print("    MEROSHARE FAMILY IPO AUTOMATION")
    print("="*50)
    print("\nOptions:")
    print("1. Apply for IPO - Select family member")
    print("2. Add/Update family member")
    print("3. List all family members")
    print("4. Get Portfolio - Select member")
    print("5. Login (test) - Select member")
    print("6. View DP list")
    print("7. Exit")
    
    choice = input("\nEnter your choice (1-7): ").strip()
    
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
        print("Goodbye!")
        return
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()

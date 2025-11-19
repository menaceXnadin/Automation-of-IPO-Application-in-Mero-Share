#!/usr/bin/env python3
"""
Nepse CLI - Enhanced command line interface for Meroshare automation
"""
import argparse
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
from main import (
    apply_ipo,
    add_family_member,
    list_family_members,
    select_family_member,
    get_portfolio_for_member,
    test_login_for_member,
    get_dp_list,
    apply_ipo_for_all_members,
    load_family_members,
    main as interactive_menu
)

# ============================================
# Market Data Functions
# ============================================

def format_number(num):
    """Format large numbers with K, M, B suffixes"""
    try:
        num = float(str(num).replace(',', ''))
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.2f}K"
        else:
            return f"{num:.2f}"
    except (ValueError, AttributeError):
        return str(num)

def format_rupees(amount):
    """Format amount as rupees with proper comma placement"""
    try:
        amount = float(str(amount).replace(',', ''))
        return f"Rs. {amount:,.2f}"
    except (ValueError, AttributeError):
        return f"Rs. {amount}"

def get_ss_time():
    """Get timestamp from ShareSansar market summary"""
    try:
        response = requests.get("https://www.sharesansar.com/market-summary", timeout=10)
        soup = BeautifulSoup(response.text, "lxml")
        summary_cont = soup.find("div", id="market_symmary_data")
        if summary_cont is not None:
            msdate = summary_cont.find("h5").find("span")
            if msdate is not None:
                return msdate.text
    except:
        pass
    return "N/A"

def cmd_ipo():
    """Display all open IPOs/public offerings"""
    try:
        print("\n📊 Fetching open IPOs...\n")
        
        response = requests.get(
            "https://sharehubnepal.com/data/api/v1/public-offering",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get('success'):
            print("⚠️  Unable to fetch IPO data. API request failed.\n")
            return
        
        all_ipos = data.get('data', {}).get('content', [])
        open_ipos = [ipo for ipo in all_ipos if ipo.get('status') == 'Open']
        
        if not open_ipos:
            print("💤 No IPOs are currently open for subscription.\n")
            return
        
        print("=" * 100)
        print(f"📈 {len(open_ipos)} OPEN IPO{'S' if len(open_ipos) != 1 else ''} AVAILABLE")
        print("=" * 100)
        
        for index, ipo in enumerate(open_ipos, 1):
            symbol = ipo.get('symbol', 'N/A')
            name = ipo.get('name', 'N/A')
            sector = ipo.get('sector', 'N/A')
            units = ipo.get('units', 0)
            price = ipo.get('price', 0)
            total_amount = ipo.get('totalAmount', 0)
            opening_date = ipo.get('openingDate', 'N/A')
            closing_date = ipo.get('closingDate', 'N/A')
            extended_closing = ipo.get('extendedClosingDate', None)
            issue_manager = ipo.get('issueManager', 'N/A')
            ipo_type = ipo.get('type', 'N/A')
            ipo_for = ipo.get('for', 'N/A')
            
            try:
                opening_date_obj = datetime.fromisoformat(opening_date.replace('T', ' '))
                opening_date_str = opening_date_obj.strftime('%d %b %Y')
            except:
                opening_date_str = opening_date
            
            try:
                closing_date_obj = datetime.fromisoformat(closing_date.replace('T', ' '))
                closing_date_str = closing_date_obj.strftime('%d %b %Y')
            except:
                closing_date_str = closing_date
            
            days_left = None
            urgency_text = ""
            try:
                target_date = extended_closing if extended_closing else closing_date
                target_date_obj = datetime.fromisoformat(target_date.replace('T', ' '))
                days_left = (target_date_obj - datetime.now()).days
                
                if days_left >= 0:
                    if days_left <= 2:
                        urgency_text = f"⚠️  LAST {days_left} DAY{'S' if days_left != 1 else ''}!"
                    elif days_left <= 5:
                        urgency_text = f"⏰ {days_left} days left"
                    else:
                        urgency_text = f"📅 {days_left} days remaining"
            except:
                urgency_text = "📅 Check dates"
            
            type_emojis = {
                'Ipo': '🆕 IPO',
                'Right': '🔄 Right Share',
                'MutualFund': '💼 Mutual Fund',
                'BondOrDebenture': '💰 Bond/Debenture'
            }
            type_display = type_emojis.get(ipo_type, f'📊 {ipo_type}')
            
            print(f"\n[{index}] {symbol} — {name}")
            print("-" * 100)
            print(f"  Type: {type_display}")
            print(f"  Sector: {sector}")
            print(f"  For: {ipo_for}")
            print(f"  Units: {units:,} @ {format_rupees(price)} = {format_rupees(total_amount)}")
            print(f"  Opens: {opening_date_str} | Closes: {closing_date_str}")
            if extended_closing:
                try:
                    ext_date_obj = datetime.fromisoformat(extended_closing.replace('T', ' '))
                    print(f"  Extended: {ext_date_obj.strftime('%d %b %Y')}")
                except:
                    pass
            print(f"  Status: {urgency_text}")
            print(f"  Issue Manager: {issue_manager}")
        
        print("=" * 100)
        print(f"\n✓ Total open IPOs: {len(open_ipos)}")
        print("\n💡 Tip: Use 'nepse apply' to apply for IPO via Meroshare\n")
        
    except requests.exceptions.RequestException as e:
        print(f"🔌 Connection Error: Unable to connect to API.\n{str(e)[:100]}\n")
    except Exception as e:
        print(f"⚠️  Error: {str(e)[:200]}\n")

def cmd_nepse():
    """Display NEPSE indices data"""
    try:
        print("\n📊 Fetching NEPSE indices...\n")
        
        url = "https://www.sharesansar.com/market"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")
        
        all_tables = soup.find_all(
            "table", class_="table table-bordered table-striped table-hover"
        )
        main_indices = all_tables[0]
        main_indices_rows = main_indices.find_all("tr")[1:]
        
        print("=" * 120)
        print("NEPSE INDEX DATA")
        print("=" * 120)
        print(f"{'Index':<30} {'Close':<12} {'Change':<15} {'% Change':<12} {'Range':<25} {'Turnover':<15}")
        print("-" * 120)
        
        for tr in main_indices_rows:
            tds = tr.find_all("td")
            index_name = tds[0].text.strip()
            close_val = tds[4].text.strip()
            point_change = tds[5].text.strip()
            pct_change = tds[6].text.strip()
            low_val = tds[3].text.strip()
            high_val = tds[2].text.strip()
            turnover = tds[7].text.strip()
            
            try:
                pct_float = float(pct_change.replace('%', '').replace('+', ''))
                trend = "📈" if pct_float > 0 else "📉" if pct_float < 0 else "➡️"
            except:
                trend = "📊"
            
            range_str = f"{low_val} - {high_val}"
            change_str = f"{point_change} ({pct_change})"
            
            print(f"{index_name:<30} {close_val:<12} {change_str:<15} {trend:<12} {range_str:<25} {format_number(turnover):<15}")
        
        print("=" * 120)
        timestamp = get_ss_time()
        print(f"\nAs of: {timestamp}\n")
        
    except Exception as e:
        print(f"⚠️  Error fetching NEPSE data: {str(e)}\n")

def cmd_subidx(subindex_name):
    """Display sub-index details"""
    try:
        subindex_name = subindex_name.upper()
        
        sub_index_mapping = {
            "BANKING": "Banking SubIndex",
            "DEVBANK": "Development Bank Index",
            "FINANCE": "Finance Index",
            "HOTELS AND TOURISM": "Hotels And Tourism",
            "HYDROPOWER": "HydroPower Index",
            "INVESTMENT": "Investment",
            "LIFE INSURANCE": "Life Insurance",
            "MANUFACTURING AND PROCESSING": "Manufacturing And Processing",
            "MICROFINANCE": "Microfinance Index",
            "MUTUAL FUND": "Mutual Fund",
            "NONLIFE INSURANCE": "Non Life Insurance",
            "OTHERS": "Others Index",
            "TRADING": "Trading Index",
        }
        
        print(f"\n📊 Fetching {subindex_name} sub-index data...\n")
        
        response = requests.get("https://www.sharesansar.com/market", timeout=10)
        soup = BeautifulSoup(response.text, "lxml")
        alltable = soup.find_all(
            "table", class_="table table-bordered table-striped table-hover"
        )
        sub_indices = alltable[3]
        sub_indices_rows = sub_indices.find_all("tr")
        
        subindex_name = sub_index_mapping.get(subindex_name, subindex_name)
        
        for tr in sub_indices_rows[1:]:
            tds = tr.find_all("td")
            if tds[0].text.upper() == subindex_name.upper():
                sub_index_details = {
                    "Sub Index": tds[0].text,
                    "Open": tds[1].text,
                    "High": tds[2].text,
                    "Low": tds[3].text,
                    "Close": tds[4].text,
                    "Pt.Change": tds[5].text,
                    "% change": tds[6].text,
                    "Turnover": tds[7].text,
                }
                
                try:
                    o = round(float(sub_index_details["Open"].replace(",", "")), 2)
                    c = round(float(sub_index_details["Close"].replace(",", "")), 2)
                    trend = "📈" if c > o else "📉" if c < o else "➡️"
                except:
                    trend = "📊"
                
                print("=" * 80)
                print(f"{trend} {sub_index_details['Sub Index']}")
                print("=" * 80)
                print(f"  Close: {sub_index_details['Close']}")
                print(f"  Change: {sub_index_details['Pt.Change']} ({sub_index_details['% change']})")
                print(f"  Range: {sub_index_details['Low']} - {sub_index_details['High']}")
                print(f"  Open: {sub_index_details['Open']}")
                print(f"  Turnover: {format_number(sub_index_details['Turnover'])}")
                print("=" * 80)
                timestamp = get_ss_time()
                print(f"\nAs of: {timestamp}\n")
                return
        
        print(f"⚠️  Sub-index '{subindex_name}' not found.\n")
        print("Available sub-indices:")
        for key in sub_index_mapping.keys():
            print(f"  - {key}")
        print()
        
    except Exception as e:
        print(f"⚠️  Error fetching sub-index data: {str(e)}\n")

def cmd_mktsum():
    """Display market summary"""
    try:
        print("\n📊 Fetching market summary...\n")
        
        response = requests.get("https://www.sharesansar.com/market-summary", timeout=10)
        soup = BeautifulSoup(response.text, "lxml")
        summary_cont = soup.find("div", id="market_symmary_data")
        
        last_mktsum = ""
        if summary_cont is not None:
            msdate = summary_cont.find("h5").find("span")
            if msdate is not None:
                last_mktsum = msdate.text
        
        data_sum = soup.find_all("td")
        
        print("=" * 100)
        print("NEPSE MARKET SUMMARY")
        print("=" * 100)
        print(f"\n💰 TRADING ACTIVITY")
        print(f"  Turnover: {format_number(data_sum[1].text)}")
        print(f"  Traded Shares: {format_number(data_sum[3].text)}")
        print(f"  Transactions: {data_sum[5].text}")
        print(f"  Scrips Traded: {data_sum[7].text}")
        
        print(f"\n💎 MARKET CAPITALIZATION")
        print(f"  Total Market Cap: {format_number(data_sum[9].text)}")
        print(f"  Floated Market Cap: {format_number(data_sum[11].text)}")
        
        try:
            mc_val = float(data_sum[9].text.replace(',', ''))
            fc_val = float(data_sum[11].text.replace(',', ''))
            float_ratio = (fc_val / mc_val) * 100
            print(f"  Float Ratio: {float_ratio:.2f}%")
        except:
            pass
        
        print("\n" + "=" * 100)
        print(f"As of: {last_mktsum}\n")
        
    except Exception as e:
        print(f"⚠️  Error fetching market summary: {str(e)}\n")

def cmd_topgl():
    """Display top 10 gainers and losers"""
    try:
        print("\n📊 Fetching top gainers and losers...\n")
        
        response = requests.get("https://merolagani.com/LatestMarket.aspx", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tgtl_col = soup.find('div', class_="col-md-4 hidden-xs hidden-sm")
        tgtl_tables = tgtl_col.find_all('table')
        
        gainers = tgtl_tables[0]
        gainers_row = gainers.find_all('tr')
        
        losers = tgtl_tables[1]
        losers_row = losers.find_all('tr')
        
        print("=" * 120)
        print("📈 TOP 10 GAINERS")
        print("=" * 120)
        print(f"{'#':<5} {'Symbol':<12} {'LTP':<12} {'%Chg':<10} {'High':<12} {'Low':<12} {'Volume':<15} {'Turnover':<15}")
        print("-" * 120)
        
        for idx, tr in enumerate(gainers_row[1:], 1):
            tds = tr.find_all('td')
            if tds and len(tds) >= 8:
                medal = ["🥇", "🥈", "🥉"] + [""] * 7
                print(f"{medal[idx-1]:<5} {tds[0].text:<12} {tds[1].text:<12} {tds[2].text:<10} {tds[3].text:<12} {tds[4].text:<12} {format_number(tds[6].text):<15} {format_number(tds[7].text):<15}")
        
        print("\n" + "=" * 120)
        print("📉 TOP 10 LOSERS")
        print("=" * 120)
        print(f"{'#':<5} {'Symbol':<12} {'LTP':<12} {'%Chg':<10} {'High':<12} {'Low':<12} {'Volume':<15} {'Turnover':<15}")
        print("-" * 120)
        
        for idx, tr in enumerate(losers_row[1:], 1):
            tds = tr.find_all('td')
            if tds and len(tds) >= 8:
                print(f"{idx:<5} {tds[0].text:<12} {tds[1].text:<12} {tds[2].text:<10} {tds[3].text:<12} {tds[4].text:<12} {format_number(tds[6].text):<15} {format_number(tds[7].text):<15}")
        
        print("=" * 120)
        timestamp = get_ss_time()
        print(f"\nAs of: {timestamp}\n")
        
    except Exception as e:
        print(f"⚠️  Error fetching top gainers/losers: {str(e)}\n")

def cmd_stonk(stock_name):
    """Display stock details (information only - no charts/alerts)"""
    try:
        stock_name = stock_name.upper()
        print(f"\n📊 Fetching details for {stock_name}...\n")
        
        import cloudscraper
        scraper = cloudscraper.create_scraper()
        
        # Try NepseAlpha API first
        stock_price_data = None
        try:
            response = scraper.get('https://nepsealpha.com/live/stocks', timeout=10)
            if response.status_code == 200:
                data = response.json()
                prices = data.get('stock_live', {}).get('prices', [])
                
                for item in prices:
                    if item.get('symbol', '').upper() == stock_name:
                        stock_price_data = item
                        break
        except:
            pass
        
        # Fetch company details from ShareSansar
        company_details = {
            "sector": "N/A",
            "share_registrar": "N/A",
            "company_fullform": stock_name,
        }
        
        try:
            response2 = requests.get(
                f"https://www.sharesansar.com/company/{stock_name}", timeout=10)
            
            if response2.status_code == 200:
                soup2 = BeautifulSoup(response2.text, "lxml")
                all_rows = soup2.find_all("div", class_="row")
                
                if len(all_rows) >= 6:
                    info_row = all_rows[5]
                    second_row = info_row.find_all("div", class_="col-md-12")
                    if len(second_row) > 1:
                        shareinfo = second_row[1]
                        heading_list = shareinfo.find_all("h4")
                        
                        if len(heading_list) > 2:
                            company_details["sector"] = heading_list[1].find("span", class_="text-org").text
                            company_details["share_registrar"] = heading_list[2].find("span", class_="text-org").text
                
                company_full_form_tag = soup2.find(
                    "h1", style="color: #333;font-size: 20px;font-weight: 600;"
                )
                if company_full_form_tag is not None:
                    company_details["company_fullform"] = company_full_form_tag.text
        except:
            pass
        
        # Fallback to ShareSansar if NepseAlpha failed
        if not stock_price_data:
            try:
                response_live = requests.get(
                    "https://www.sharesansar.com/live-trading", timeout=10)
                
                if response_live.status_code == 200:
                    soup = BeautifulSoup(response_live.text, "lxml")
                    stock_rows = soup.find_all("tr")
                    
                    for row in stock_rows[1:]:
                        row_data = row.find_all("td")
                        
                        if len(row_data) > 9 and row_data[1].text.strip() == stock_name:
                            close_price = float(row_data[2].text.strip().replace(',', ''))
                            pt_change = float(row_data[3].text.strip().replace(',', ''))
                            pct_change = row_data[4].text.strip()
                            
                            trend = "📈" if pt_change > 0 else "📉" if pt_change < 0 else "➡️"
                            
                            print("=" * 100)
                            print(f"{trend} {stock_name} — {company_details['company_fullform']}")
                            print("=" * 100)
                            print(f"  Symbol: {stock_name}")
                            print(f"  Last Traded Price: Rs. {row_data[2].text.strip()} {trend}")
                            print(f"  Point Change: {row_data[3].text.strip()}")
                            print(f"  % Change: {pct_change}")
                            print(f"  Open: {row_data[5].text.strip()}")
                            print(f"  High: {row_data[6].text.strip()}")
                            print(f"  Low: {row_data[7].text.strip()}")
                            print(f"  Volume: {row_data[8].text.strip()}")
                            print(f"  Prev. Closing: {row_data[9].text.strip()}")
                            print(f"\n  Sector: {company_details['sector']}")
                            print(f"  Share Registrar: {company_details['share_registrar']}")
                            print("=" * 100)
                            timestamp = get_ss_time()
                            print(f"\nAs of: {timestamp}\n")
                            return
            except:
                pass
            
            print(f"⚠️  Stock '{stock_name}' not found.\n")
            return
        
        # Use NepseAlpha data
        close_price = stock_price_data.get("close", 0)
        percent_change = stock_price_data.get("percent_change", 0)
        
        try:
            if percent_change != 0 and close_price != 0:
                prev_close = close_price / (1 + percent_change / 100)
                pt_change = close_price - prev_close
            else:
                prev_close = close_price
                pt_change = 0
        except:
            prev_close = close_price
            pt_change = 0
        
        trend = "📈" if pt_change > 0 else "📉" if pt_change < 0 else "➡️"
        
        print("=" * 100)
        print(f"{trend} {stock_name} — {company_details['company_fullform']}")
        print("=" * 100)
        print(f"  Symbol: {stock_name}")
        print(f"  Last Traded Price: Rs. {close_price:,.2f} {trend}")
        print(f"  Point Change: {pt_change:+,.2f}")
        print(f"  % Change: {percent_change:+.2f}%")
        print(f"  Open: Rs. {stock_price_data.get('open', 0):,.2f}")
        print(f"  High: Rs. {stock_price_data.get('high', 0):,.2f}")
        print(f"  Low: Rs. {stock_price_data.get('low', 0):,.2f}")
        print(f"  Volume: {int(stock_price_data.get('volume', 0)):,}")
        print(f"  Prev. Closing: Rs. {prev_close:,.2f}")
        print(f"\n  Sector: {company_details['sector']}")
        print(f"  Share Registrar: {company_details['share_registrar']}")
        print("=" * 100)
        print(f"\nAs of: {data.get('stock_live', {}).get('asOf', 'N/A')}\n")
        
    except Exception as e:
        print(f"⚠️  Error fetching stock data: {str(e)}\n")

def main():
    parser = argparse.ArgumentParser(
        description="🚀 Meroshare Family IPO Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Meroshare IPO Automation
  nepse                    Run interactive menu
  nepse apply              Apply for IPO (headless mode)
  nepse apply-all          Apply IPO for ALL family members (multi-tab)
  nepse add                Add/update family member
  nepse list               List all family members
  nepse portfolio          Get portfolio for a member (headless mode)
  nepse login              Test login for a member (headless mode)
  nepse dp-list            View available DP list
  
  # Market Data Commands
  nepse ipo                View all open IPOs/FPOs
  nepse nepse              View NEPSE indices
  nepse subidx BANKING     View sub-index details
  nepse mktsum             View market summary
  nepse topgl              View top gainers/losers
  nepse stonk NABIL        View stock details
  
  nepse apply --gui        Apply for IPO with browser window visible
  nepse apply-all --gui    Apply IPO for all members with browser visible
  nepse portfolio --gui    Get portfolio with browser window visible
        """
    )
    # Keep window open after running (useful when invoking from Windows Run dialog)
    parser.add_argument("--wait", action="store_true", help="Keep window open after running (useful when running from Win+R or desktop shortcuts)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Apply IPO
    apply_parser = subparsers.add_parser("apply", help="Apply for IPO")
    apply_parser.add_argument("--gui", action="store_true", help="Show browser window (default is headless)")
    
    # Apply IPO for all members
    apply_all_parser = subparsers.add_parser("apply-all", help="Apply IPO for ALL family members (multi-tab)")
    apply_all_parser.add_argument("--gui", action="store_true", help="Show browser window (default is headless)")
    
    # Add member
    subparsers.add_parser("add", help="Add or update a family member")
    
    # List members
    subparsers.add_parser("list", help="List all family members")
    
    # Get portfolio
    portfolio_parser = subparsers.add_parser("portfolio", help="Get portfolio for a member")
    portfolio_parser.add_argument("name", nargs='?', help="Family member name (optional, will prompt if not provided)")
    portfolio_parser.add_argument("--gui", action="store_true", help="Show browser window (default is headless)")
    
    # Test login
    login_parser = subparsers.add_parser("login", help="Test login for a member")
    login_parser.add_argument("--gui", action="store_true", help="Show browser window (default is headless)")
    
    # DP list
    subparsers.add_parser("dp-list", help="View available DP (Depository Participant) list")
    
    # Market data commands
    subparsers.add_parser("ipo", help="View all open IPOs/public offerings")
    subparsers.add_parser("nepse", help="View NEPSE indices data")
    subidx_parser = subparsers.add_parser("subidx", help="View sub-index details")
    subidx_parser.add_argument("subindex", help="Sub-index name (e.g., BANKING, HYDROPOWER)")
    subparsers.add_parser("mktsum", help="View market summary")
    subparsers.add_parser("topgl", help="View top 10 gainers and losers")
    stonk_parser = subparsers.add_parser("stonk", help="View stock details")
    stonk_parser.add_argument("stock", help="Stock symbol (e.g., NABIL, NICA)")
    
    args = parser.parse_args()
    
    # If no command provided, run interactive menu
    if not args.command:
        try:
            interactive_menu()
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)
        return
    
    # Execute commands
    try:
        if args.command == "apply":
            # Default to headless, only show GUI if --gui flag is passed
            apply_ipo(auto_load=True, headless=not args.gui)
        elif args.command == "apply-all":
            # Apply IPO for all members - default to headless, show GUI if --gui flag is passed
            apply_ipo_for_all_members(headless=not args.gui)
        elif args.command == "add":
            add_family_member()
        elif args.command == "list":
            list_family_members()
            input("\nPress Enter to continue...")
        elif args.command == "portfolio":
            if args.name:
                # Find member by name
                config = load_family_members()
                members = config.get('members', [])
                member = None
                for m in members:
                    if m['name'].lower() == args.name.lower():
                        member = m
                        break
                if not member:
                    print(f"\n✗ Member '{args.name}' not found.")
                    print("\nAvailable members:")
                    for m in members:
                        print(f"  - {m['name']}")
                    print()
                    sys.exit(1)
            else:
                # Prompt for member selection
                member = select_family_member()
            
            if member:
                # Default to headless, only show GUI if --gui flag is passed
                get_portfolio_for_member(member, headless=not args.gui)
        elif args.command == "login":
            member = select_family_member()
            if member:
                # Default to headless, only show GUI if --gui flag is passed
                test_login_for_member(member, headless=not args.gui)
        elif args.command == "dp-list":
            get_dp_list()
        elif args.command == "ipo":
            cmd_ipo()
        elif args.command == "nepse":
            cmd_nepse()
        elif args.command == "subidx":
            cmd_subidx(args.subindex)
        elif args.command == "mktsum":
            cmd_mktsum()
        elif args.command == "topgl":
            cmd_topgl()
        elif args.command == "stonk":
            cmd_stonk(args.stock)
    except KeyboardInterrupt:
        print("\n\n✗ Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        # If --wait is provided, pause before exiting so users running from Win+R
        # or desktop shortcuts can read the output. Also provide a gentle hint
        # if running non-interactively but --wait is not provided.
        try:
            if getattr(args, 'wait', False):
                input("\nPress Enter to exit...")
            elif not sys.stdin.isatty():
                print("\nNote: This process was started without an active terminal. To keep the window open, run from PowerShell/Command Prompt or add '--wait' flag.")
        except Exception:
            # Ignore any input-related errors (e.g., no stdin)
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()

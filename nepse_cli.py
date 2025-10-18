#!/usr/bin/env python3
"""
Nepse CLI - Enhanced command line interface for Meroshare automation
"""
import argparse
import sys
from main import (
    apply_ipo,
    add_family_member,
    list_family_members,
    select_family_member,
    get_portfolio_for_member,
    test_login_for_member,
    get_dp_list,
    main as interactive_menu
)

def main():
    parser = argparse.ArgumentParser(
        description="🚀 Meroshare Family IPO Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nepse                    Run interactive menu
  nepse apply              Apply for IPO (headless mode)
  nepse add                Add/update family member
  nepse list               List all family members
  nepse portfolio          Get portfolio for a member (headless mode)
  nepse login              Test login for a member (headless mode)
  nepse dp-list            View available DP list
  
  nepse apply --gui        Apply for IPO with browser window visible
  nepse portfolio --gui    Get portfolio with browser window visible
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Apply IPO
    apply_parser = subparsers.add_parser("apply", help="Apply for IPO")
    apply_parser.add_argument("--gui", action="store_true", help="Show browser window (default is headless)")
    
    # Add member
    subparsers.add_parser("add", help="Add or update a family member")
    
    # List members
    subparsers.add_parser("list", help="List all family members")
    
    # Get portfolio
    portfolio_parser = subparsers.add_parser("portfolio", help="Get portfolio for a member")
    portfolio_parser.add_argument("--gui", action="store_true", help="Show browser window (default is headless)")
    
    # Test login
    login_parser = subparsers.add_parser("login", help="Test login for a member")
    login_parser.add_argument("--gui", action="store_true", help="Show browser window (default is headless)")
    
    # DP list
    subparsers.add_parser("dp-list", help="View available DP (Depository Participant) list")
    
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
        elif args.command == "add":
            add_family_member()
        elif args.command == "list":
            list_family_members()
            input("\nPress Enter to continue...")
        elif args.command == "portfolio":
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
    except KeyboardInterrupt:
        print("\n\n✗ Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

## IPO Result Automation (Playwright)

This repo now includes a small helper `iporesult_playwright.py` that opens https://iporesult.cdsc.com.np/, fills your BOID, and lets you solve the CAPTCHA manually before submitting.

Quick start (Windows PowerShell):

```
python -m pip install --upgrade pip
pip install playwright
python -m playwright install chromium

# Run (UI mode, manual CAPTCHA)
python iporesult_playwright.py --boid 1234567890123456 --company "SY Panel Nepal Limited (For General Public)"
```

Notes:
- The script will NOT bypass CAPTCHA. You need to type it yourself in the opened browser window.
- `--company` is optional; if omitted, the currently shown issue stays selected.
- Add `--headless` to run without opening a visible window.

# Nepse CLI - Meroshare IPO Automation

A command-line tool to automate IPO applications on Meroshare for multiple family members.

**✨ Features visual progress bars for all operations!**

```
[██████████████████░░░░░░░░░░░░] 50% (3/6) Selecting DP (value: 10900)...
```

## Installation

1. **Install the CLI globally:**
   ```powershell
   cd "Nepse CLI"
   pip install -e .
   ```

2. **Install Playwright browsers (first time only):**
   ```powershell
   playwright install chromium
   ```

## Usage

### Interactive Menu (Default)
```powershell
nepse
```

### Direct Commands

#### Meroshare IPO Automation
```powershell
# Apply for IPO (headless by default - no browser window)
nepse apply

# Apply with browser window visible
nepse apply --gui

# Apply for ALL family members (multi-tab automation)
nepse apply-all

# Apply for all members with browser visible
nepse apply-all --gui

# Add or update a family member
nepse add

# List all family members
nepse list

# Get portfolio (headless by default)
nepse portfolio

# Get portfolio with browser window visible
nepse portfolio --gui

# Test login (headless by default)
nepse login

# Test login with browser window visible
nepse login --gui

# View available DP list
nepse dp-list
```

#### Market Data Commands
```powershell
# View all open IPOs/FPOs
nepse ipo

# View NEPSE indices
nepse nepse

# View sub-index details (Banking, Hydropower, etc.)
nepse subidx BANKING
nepse subidx HYDROPOWER

# View market summary
nepse mktsum

# View top 10 gainers and losers
nepse topgl

# View stock details (information only - no charts)
nepse stonk NABIL
nepse stonk NICA
  # Keep window open when running from Win+R or desktop shortcuts
  nepse ipo --wait
  nepse stonk NABIL --wait
```

## Features

### Meroshare Automation
- ✅ Multi-member family support
- ✅ Automated IPO application
- ✅ Multi-tab IPO application for all family members
- ✅ Portfolio fetching
- ✅ Login testing
- ✅ Secure credential storage
- ✅ **Headless mode by default** - fast and silent operation
- ✅ Optional GUI mode with `--gui` flag for debugging

### Market Data
- ✅ View open IPOs/FPOs with detailed information
- ✅ View NEPSE indices (main index, sensitive, float, etc.)
- ✅ View sub-indices (Banking, Hydropower, Finance, etc.)
- ✅ View market summary (turnover, volume, market cap)
- ✅ View top 10 gainers and losers
- ✅ View individual stock details (price, volume, sector, etc.)
- ✅ Real-time data from ShareSansar, MeroLagani, and NepseAlpha APIs

## Configuration

All credential data is stored in a **fixed location** to avoid path issues:

📁 **Data Directory**: `C:\Users\%USERNAME%\Documents\merosharedata\`

Files stored here:
- `family_members.json` - All family member credentials
- `ipo_config.json` - IPO application settings (if any)

This means the CLI works from **any directory** - your data is always in the same place!

Family member data structure:

```json
{
  "members": [
    {
      "name": "Dad",
      "dp_value": "139",
      "username": "your_username",
      "password": "your_password",
      "transaction_pin": "1234",
      "applied_kitta": 10,
      "crn_number": "YOUR_CRN"
    }
  ]
}
```

## Security

- Passwords are stored locally in JSON format
- File permissions are set to 600 on Unix systems
- Never commit `family_members.json` to version control

## Troubleshooting

**Command not found:**
- Make sure you ran `pip install -e .` in the Nepse CLI directory
- Restart your terminal after installation

**Browser not installed:**
- Run: `playwright install chromium`

**Login fails:**
- Test with: `nepse login`
- Verify credentials with: `nepse list`
- Update credentials with: `nepse add`

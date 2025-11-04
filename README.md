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

```powershell
# Apply for IPO (headless by default - no browser window)
nepse apply

# Apply with browser window visible
nepse apply --gui

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

## Features

- ✅ Multi-member family support
- ✅ Automated IPO application
- ✅ Portfolio fetching
- ✅ Login testing
- ✅ Secure credential storage
- ✅ **Headless mode by default** - fast and silent operation
- ✅ Optional GUI mode with `--gui` flag for debugging

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

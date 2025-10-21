import requests
import json

# Fetch DP list to understand the mapping
response = requests.get('https://webbackend.cdsc.com.np/api/meroShare/capital/')
dp_data = response.json()

print('DP List sample:')
for dp in dp_data[:5]:
    print(f'ID: {dp["id"]}, Code: {dp["code"]}, Name: {dp["name"]}')

# Check what DP 10900 maps to
dp_10900 = next((dp for dp in dp_data if dp['id'] == 10900), None)
if dp_10900:
    print(f'\nDP 10900 details: {dp_10900}')
else:
    print('\nDP 10900 not found by ID, trying code...')
    dp_10900 = next((dp for dp in dp_data if str(dp['code']) == '10900'), None)
    if dp_10900:
        print(f'DP 10900 details: {dp_10900}')

# Also check what the demat format should be
# From the intercepted call: demat: ["1301090004121371"]
# This looks like: 13 + DP code (0109) + 000 + username (04121371)
print('\nAnalyzing demat format from intercepted call:')
print('Intercepted demat: "1301090004121371"')
print('Breaking it down:')
print('- Starts with 13 (maybe country code?)')
print('- Then DP code: 0109')
print('- Then 000 (padding?)')
print('- Then username: 04121371')
print('- DP code in member data: 10900')
print('- Username in member data: 04121371')
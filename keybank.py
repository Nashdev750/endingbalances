import re
from datetime import datetime
from collections import defaultdict

def standardize_date_keybank(date_str):
    date_str = date_str.strip()

    formats = [
        "%m-%d-%y",     # 5-27-25
        "%m-%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%b %d")  # Example: 'Sep 01'
        except ValueError:
            continue

    return date_str

def process_keybank(text):    
    parts = text.split('Subtractions\nPaperChecks')
    print(str(len(parts))+" parts")
    adds = parts[0].split('Additions\nDeposits')
    parts2 = parts[1].split('Fees and\ncharges Date')
    subs = ""
    if 'Totalsubtractions' in parts2[0]:
        subs = parts2[0].split('Totalsubtractions')[0]
    else:
        subs = parts2[0].split('Total subtractions')[0]

    feesncharges = ""
    if len(parts2) > 1:
        feesncharges = parts2[1]
    start_bal = extract_keybank_beginning_balance(adds[0])
    ac_adds = get_transactions_keybank(adds[1])    
    ac_subs = get_transactions_keybank(subs)    
    ac_fees = extract_fee_keybank(feesncharges)
   
    transaction_map = defaultdict(lambda: {'credits': 0, 'debits': 0})
    depo=0
    for date, amount in ac_adds + ac_fees:
        transaction_map[date]['credits'] += amount
        depo+=amount
    print(ac_adds)    
    print(depo)
    for date, amount in ac_subs:
        transaction_map[date]['debits'] += amount
   
    results = [] 
    current_balance = start_bal      
    for date in sorted(transaction_map.keys()): 
        tx = transaction_map[date]
        net = tx['credits'] - tx['debits']
        current_balance += net
        results.append({
            'date': date,
            'ending_balance': round(current_balance, 2),
            'net_change': round(amount, 2)
        }) 
    # print(results)      
    return results    

def get_transactions_keybank(text):
    pattern = re.compile(r'(?P<date>\b\d{1,2}-\d{1,2}\b).*?(?P<value>[+-]?\$?[\d,]+\.\d{2})')
    matches = pattern.finditer(text)
    transactions = []
    for match in matches:
        date = standardize_date_keybank(match.group('date'))
        value = match.group('value').replace('$', '').replace(',', '')
        transactions.append((date, float(value)))
    return transactions


def extract_fee_keybank(text):
    pattern = re.compile(
        r'(?P<date>\d{1,2}-\d{1,2}-\d{2})\s+.+?\s+\d+\s+\d+\.\d{2}\s+(?P<amount>[+-]?\$?\d+\.\d{2})'
    )

    results = []
    for match in pattern.finditer(text):
        date = standardize_date_keybank(match.group("date"))
        amount_str = match.group("amount").replace("$", "")
        amount = float(amount_str)
        results.append((date, amount))
    # print(results)
    return results  

def extract_keybank_beginning_balance(text):
    pattern = re.compile(
        r'Beginning balance.*?([-]?\$?-?\d[\d,]*\.\d{2})',
        re.IGNORECASE
    )
    match = pattern.search(text)
    # print(match)
    if match:
        amount_str = match.group(1).replace('$', '').replace(',', '')
        return float(amount_str)
    return 0 

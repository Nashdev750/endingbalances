import re
from datetime import datetime

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

with open('keybank.txt', 'r', encoding='utf-8') as fl:
    text =  fl.read()
def process_keybank(text):    
    parts = text.split('Subtractions\n')
    adds = parts[0]
    subsnfees = " ".join(parts[1:]) 
    parts2 = subsnfees.split('Fees and\ncharges Date')
    subs = parts2[0]
    feesncharges = parts2[1]
    start_bal = extract_keybank_beginning_balance(adds)
    ac_adds = get_transactions_keybank(adds)    
    ac_subs = get_transactions_keybank(subs)    
    ac_fees = extract_fee_keybank(feesncharges)
    transactions = {}
    transaction_map = {}
    for date, amount in ac_adds[1:] + ac_fees:
        transaction_map[date]['deposits'] += amount

    for date, amount in ac_subs:
        if date in transactions:
            transactions[date] -= amount
        else:    
            transactions[date] = -amount
    results = []       
    for date in sorted(transactions.keys()): 
        amount = transactions[date] 
        ending_balance = start_bal + amount 
        start_bal =  ending_balance
        results.append({
            'date': date,
            'ending_balance': round(ending_balance, 2),
            'net_change': round(amount, 2)
        })   
    print(results)    
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


process_keybank(text)

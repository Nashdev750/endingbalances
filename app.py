from flask import Flask, request, render_template, jsonify
import pdfplumber
import re
from collections import defaultdict
from datetime import datetime
import re

def standardize_date(date_str):
    date_str = date_str.strip()

    formats = [
        "%m/%d",        # 03/03
        "%d-%m-%Y",     # 01-03-2025
        "%b %d",        # Sep 01
        "%d-%m",        # 01-03 (without year)
        "%Y-%m-%d",     # 2025-03-01
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%b %d")  # Example: 'Sep 01'
        except ValueError:
            continue

    return date_str

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract_text():
    file = request.files.get('pdf_file')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    try:
        with pdfplumber.open(file.stream) as pdf:
            full_text = ''
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + '\n'
        with open('flag.txt', 'w') as fl:
            fl.write(full_text)            
        result = process_statement(full_text)
        if isinstance(result, str):  # return error string
            return jsonify({'error': result})
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def process_statement(text):
    if re.search(r"Novo Platform", text, re.IGNORECASE):
        return {'balances': process_novo(text),"bank":"/ending-balances/static/novo.jpeg"} 
    elif "1 (888) 216-9619" in text:
        return {'balances': process_bluevine(text),"bank":"/ending-balances/static/bluevine.jpeg"}  
    elif re.search(r"Truist", text, re.IGNORECASE):
        return {'balances': process_practive(text),"bank":"/ending-balances/static/truist.jpeg"}
    elif "(888) 248-6423" in text:
        return {'balances': process_flagstar(text),"bank":"/ending-balances/static/flagstar.jpeg"}
    else:
        return "❌ Unknown bank format."


def process_flagstar(text):
    match = re.search(r"Beginning Balance\s(-?\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", text)
    if not match:
        return "❌ Couldn't find Starting Balance for FlagStar."
    start_balance = float(match.group(1).replace(',', '').replace('$', ''))
    deposits = extractflagstar_deposits(text)
    credits = extract_credits(text,True)
    debits = extract_flagstardebits(text)

    # Step 3: Merge all transactions by date
    transaction_map = defaultdict(lambda: {'deposits': 0, 'credits': 0, 'debits': 0})

    for tx in deposits:
        for date, amt in tx.items():
            transaction_map[standardize_date(date)]['deposits'] += amt

    for tx in credits:
        for date, amt in tx.items():
            transaction_map[standardize_date(date)]['credits'] += amt

    for tx in debits:
        for date, amt in tx.items():
            transaction_map[standardize_date(date)]['debits'] += amt

    # Step 4: Compute balances in date order
    results = []
    current_balance = start_balance

    current_balance = start_balance

    for date in sorted(transaction_map.keys()):
        tx = transaction_map[date]
        net = tx['deposits'] + tx['credits'] - tx['debits']
        current_balance += net
        results.append({
            'date': date,
            'ending_balance': round(current_balance, 2),
            'net_change': round(net, 2)
        })     
    return results

def extract_flagstardebits(text):
    match = re.search(
        r"Electronic Debits(.*?)Checks Cleared",
        text,
        re.DOTALL
    )
    if not match:
        return []

    debits_section = match.group(1).strip()
    # 3. Extract all date + amount matches
    transactions = re.findall(
        r"(\d{2}/\d{2}/\d{4}).*?\$([\d,]+\.\d{2})",
        debits_section
    )

    # 4. Format into list of {date: amount} dicts
    debits = [
        {
            datetime.strptime(date, "%m/%d/%Y").strftime("%Y-%m-%d"):
            float(amount.replace(",", "").replace('$', ''))
        }
        for date, amount in transactions
    ]

    return debits
def extract_credits(text, skip_rejected=False):
    match = re.search(
        r"Electronic Credits(.*?)Electronic Debits",
        text,
        re.DOTALL
    )
    if not match:
        return []

    credit_section = match.group(1).strip()

    # 2. If skipping rejected, remove lines with (Rejected)
    if skip_rejected:
        credit_section = "\n".join(
            line for line in credit_section.splitlines()
            if "External Withdrawal" not in line
        )

    # 3. Extract all date + amount matches
    transactions = re.findall(
        r"(\d{2}/\d{2}/\d{4}).*?\$([\d,]+\.\d{2})",
        credit_section
    )

    # 4. Format into list of {date: amount} dicts
    credits = [
        {
            datetime.strptime(date, "%m/%d/%Y").strftime("%Y-%m-%d"):
            float(amount.replace(",", "").replace('$', ''))
        }
        for date, amount in transactions
    ]

    return credits

def extractflagstar_deposits(text):
    match = re.search(
        r"Deposits\s+Date Description Amount(.*?)\d+\sitem\(s\)\stotaling", 
        text, 
        re.DOTALL
    )
    if not match:
        return []  # No deposit section found

    deposit_section = match.group(1).strip()

    # Extract date and amount pairs
    pattern = re.findall(r"(\d{2}/\d{2}/\d{4}).*?\$([\d,]+\.\d{2})", deposit_section)

    # Convert to structured list
    transactions = [
        {
            datetime.strptime(date, "%m/%d/%Y").strftime("%Y-%m-%d"):
            float(amount.replace(",", "").replace('$', ''))
        }
        for date, amount in pattern
    ]

    return transactions

def process_bluevine(text):
    match = re.search(r'Beginning Balance on\s*\$([\d,]+\.\d{2})', text)
    if not match:
        return "❌ Couldn't find Starting Balance for Bluevine."

    starting_balance = float(match.group(1).replace(',', ''))

    full_matches = re.findall(
        r'(?P<date>\d{1,2}/\d{1,2}/\d{2,4})[^\n]*?(?P<amount>-?\$?[\d,]+\.\d{2})', text)
 
    if not full_matches:
        return "❌ No transactions matched in Bluevine."

    # Use date string exactly as in PDF
    daily_txns = defaultdict(float)
    for date_str, amount_str in full_matches:
        try:
            parsed_date = datetime.strptime(date_str, '%m/%d/%Y') if len(date_str.split('/')[-1]) == 4 \
                          else datetime.strptime(date_str, '%m/%d/%y')
            normalized_date = parsed_date.strftime('%d-%m-%Y')
            amount = float(amount_str.replace(',', '').replace('$', ''))
            daily_txns[normalized_date] += amount
        except ValueError:
            continue
    # sorted_txns = dict(sorted(daily_txns.items()))
    current_balance = starting_balance
    results = []
    for date in sorted(daily_txns.keys()):
        net = daily_txns[date]
        current_balance += net
        results.append({
            'date': standardize_date(str(date)),
            'ending_balance': round(current_balance, 2),
            'net_change': round(net, 2)
        })

    return results

    
def process_novo(text):
    # Extract Starting Balance
    match = re.search(
        r'Starting Balance\s+Income\s+Expenses\s+Ending Balance\s+\$\s*([\d,]+\.\d{2})',
        text
    )
    if not match:
        return []

    starting_balance = float(match.group(1).replace(',', ''))

    # Extract Transactions
    txn_pattern = re.findall(
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec) \d{2})[^\n]*?([+-]?\$?\-?\d{1,3}(?:,\d{3})*(?:\.\d{2}))',
        text
    )

    daily_txns = defaultdict(float)
    for date_str, amount_str in txn_pattern:
        clean_date = date_str.strip()
        amount_clean = amount_str.replace('$', '').replace(',', '').strip()
        try:
            amount = float(amount_clean)
            daily_txns[clean_date] += amount
        except ValueError:
            continue
        
    sorted_dates = sorted(
        daily_txns.keys(),
        key=lambda d: datetime.strptime(d.replace("Sept", "Sep"), "%b %d")
    )

    output = []
    current_balance = starting_balance
    for date in sorted_dates:
        net = daily_txns[date]
        current_balance += net
        output.append({
            'date': date,
            'ending_balance': round(current_balance, 2),
            'net_change': round(net, 2)
        })

    return output

def compute_balances(starting_balance, txn_data, date_fmt="%b %d"):
    daily_txns = defaultdict(float)

    for date_str, amount_str in txn_data:
        try:
            date_obj = datetime.strptime(date_str.strip(), date_fmt)
            day_key = date_obj.strftime("%Y-%m-%d")
            amount = float(amount_str.replace('$', '').replace(',', ''))
            daily_txns[day_key] += amount
        except Exception:
            continue

    current_balance = starting_balance
    results = []
    for date in sorted(daily_txns.keys()):
        net = daily_txns[date]
        current_balance += net
        results.append({
            'date': date,
            'ending_balance': round(current_balance, 2),
            'net_change': round(net, 2)
        })
    return results

def process_practive(text):
    # Extract starting balance
    # print(text)
    match = re.search(r'Yourpreviousbalanceasof[\d/]+ \$-?([\d,]+\.\d{2})', text)
    if not match:
        return "❌ Couldn't find Starting Balance for Practive Health."

    starting_balance = float(match.group(0).split(' ')[-1].replace(',', '').replace('$',''))
    # Split the text by the transaction divider
    sections = text.split('Deposits,creditsandinterest')
    if len(sections) < 2:
        return "❌ Could not split IN and OUT transaction sections for Practive."

    out_section = sections[1]
    in_section = sections[2]

    daily_txns = defaultdict(float)

    # Pattern: MM/DD ... number (non-signed)
    # pattern = r'(\d{2}/\d{2})[^\n]*?([+-]?\$?\-?\d{1,3}(?:,\d{3})*(?:\.\d{2}))'

    # transaction_line_regex = re.compile(r'(\d{2}/\d{2})\s+(.+?)\s+([\d,]+\.\d{2})')

    pattern = r'(\d{2}/\d{2})[^\n]*?([+-]?\$?\-?\d{1,3}(?:,\d{3})*(?:\.\d{2}))'
   
    # OUT transactions (negative)
    out = re.findall(pattern, out_section)
    intr = re.findall(pattern, in_section)

    for date_str, amt_str in out:
        try:
            amount = float(amt_str.replace(',', ''))
            daily_txns[date_str] -= amount
        except Exception as e:
            continue
    
    # IN transactions (positive)
    for date_str, amt_str in intr:
        try:
            amount = float(amt_str.replace(',', ''))
            daily_txns[date_str] += amount
        except ValueError:
            continue

    current_balance = starting_balance
    results = []

    for date in sorted(daily_txns.keys()):
        net = daily_txns[date]
        current_balance += net
        results.append({
            'date': standardize_date(str(date)),
            'net_change': round(net, 2),
            'ending_balance': round(current_balance, 2)
        })

    return results


if __name__ == '__main__':
    app.run(debug=True)

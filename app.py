from flask import Flask, request, render_template, jsonify
import pdfplumber
import re
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

@app.route('//ending-balances')
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
        result = process_statement(full_text)
        if isinstance(result, str):  # return error string
            return jsonify({'error': result})
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def process_statement(text):
    if "Novo Platform" in text:
        return {'balances': process_novo(text),"bank":"Novo Platform"} 
    elif "Bluevine Inc" in text:
        return {'balances': process_bluevine(text),"bank":"Bluevine Inc"}  
    elif "PRACTIVE HEALTH INC" in text or "Yourpreviousbalanceasof" in text:
        return {'balances': process_practive(text),"bank":"PRACTIVE HEALTH INC"}
    else:
        return "❌ Unknown bank format."
    

def process_bluevine(text):
    match = re.search(r'Beginning Balance on\s*\$([\d,]+\.\d{2})', text)
    if not match:
        return "❌ Couldn't find Starting Balance for Bluevine."

    starting_balance = float(match.group(1).replace(',', ''))

    # Match lines like: 06/01/25 H-E-B #697 ... $-86.22
    txn_pattern = re.findall(
        r'(\d{2}/\d{2}/\d{2})[^\n]*?\$\-?[\d,]+\.\d{2}', text)

    full_matches = re.findall(
        r'(?P<date>\d{2}/\d{2}/\d{2})[^\n]*?\$(?P<amount>-?[\d,]+\.\d{2})', text)

    if not full_matches:
        return "❌ No transactions matched in Bluevine."

    # Use date string exactly as in PDF
    daily_txns = defaultdict(float)
    for date_str, amount_str in full_matches:
        try:
            amount = float(amount_str.replace(',', ''))
            daily_txns[date_str] += amount
        except ValueError:
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
        r'(Nov \d{2})[^\n]*?([+-]?\$?\-?\d{1,3}(?:,\d{3})*(?:\.\d{2}))',
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
        key=lambda d: datetime.strptime(d, "%b %d")
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
    match = re.search(r'Yourpreviousbalanceasof[\d/]+ \$([\d,]+\.\d{2})', text)
    if not match:
        return "❌ Couldn't find Starting Balance for Practive Health."

    starting_balance = float(match.group(1).replace(',', ''))
    # Split the text by the transaction divider
    sections = text.split('Deposits,creditsandinterest')
    if len(sections) < 2:
        return "❌ Could not split IN and OUT transaction sections for Practive."

    out_section = sections[1]
    in_section = sections[2]

    daily_txns = defaultdict(float)

    # Pattern: MM/DD ... number (non-signed)
    pattern = r'(\d{2}/\d{2})[^\n]*?([+-]?\$?\-?\d{1,3}(?:,\d{3})*(?:\.\d{2}))'
    print(len(sections))
    print(in_section)
    print('-------------------------------------------------')
    print(out_section)
    # OUT transactions (negative)
    for date_str, amt_str in re.findall(pattern, out_section):
        try:
            print(date_str+" ->"+ amt_str)
            amount = float(amt_str.replace(',', ''))
            daily_txns[date_str] -= amount
        except Exception as e:
            print(e)
            continue
    
    # IN transactions (positive)
    for date_str, amt_str in re.findall(pattern, in_section):
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
            'date': date,
            'net_change': round(net, 2),
            'ending_balance': round(current_balance, 2)
        })

    return results


if __name__ == '__main__':
    app.run(debug=True)

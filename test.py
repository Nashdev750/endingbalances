import re
from datetime import datetime

def extract_debits(file_path):
    with open(file_path, 'r') as fl:
        text = fl.read()
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
            float(amount.replace(",", ""))
        }
        for date, amount in transactions
    ]

    return debits

debits = extract_credits("flag.txt")
print(str(len(debits)))

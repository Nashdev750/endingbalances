import re


with open('flag.txt', 'r') as fl:
    text =  fl.read()
def get_flagstarchecks(text):
    # Step 1: Find the position of the first "Checks Cleared"
    match = re.search(r'Checks Cleared', text)
    if not match:
        result = []
    else:
        start_pos = match.end()
        remaining_text = text[start_pos:]

        # Step 2: Extract all (date, amount) pairs after that point
        pattern = r'(\d{2}/\d{2}/\d{4})\s+\$([\d,]+\.\d{2})'
        matches = re.findall(pattern, remaining_text)

        # Step 3: Build the result list
        result = [{date: float(amount.replace(",", "").replace("$", ""))} for date, amount in matches]
    return result    

print(result)

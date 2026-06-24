import pandas as pd
import re
from datetime import datetime, timedelta
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font

SRC = '/mnt/user-data/uploads/Planilha_base_porsche.xlsx'
OUT = '/home/claude/work/Planilha_base_porsche_schema.xlsx'

df = pd.read_excel(SRC, sheet_name=0, dtype={'sale_date': object})
INVALID = "Inválido"

# ---------- 1. sale_date ----------
MONTHS = {
    'january':1,'february':2,'march':3,'april':4,'may':5,'june':6,'july':7,
    'august':8,'september':9,'october':10,'november':11,'december':12,
    'jan':1,'feb':2,'mar':3,'apr':4,'jun':6,'jul':7,'aug':8,'sep':9,'sept':9,
    'oct':10,'nov':11,'dec':12
}

def excel_serial_to_date(n):
    try:
        n = float(n)
        base = datetime(1899, 12, 30)
        d = base + timedelta(days=n)
        return d
    except Exception:
        return None

def try_valid_date(y, m, d):
    try:
        return datetime(int(y), int(m), int(d))
    except Exception:
        return None

def parse_sale_date(val):
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d')
    if pd.isna(val):
        return INVALID
    s = str(val).strip()

    # pure number -> excel serial
    if re.fullmatch(r'\d{4,6}', s):
        d = excel_serial_to_date(s)
        if d:
            return d.strftime('%Y-%m-%d')
        return INVALID

    # written month name: "September 17, 2024" / "Dec 25th 2024" / "May 12, 2025" / "Jun 18th 2027"
    m_match = re.match(
        r'^([A-Za-z]+)\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})$', s)
    if m_match:
        mon_name, day, year = m_match.groups()
        mon = MONTHS.get(mon_name.lower())
        if mon:
            d = try_valid_date(year, mon, day)
            return d.strftime('%Y-%m-%d') if d else INVALID
        return INVALID

    # numeric with separators: handle -, /, ., space
    sep_match = re.fullmatch(r'(\d{1,4})[\-/\.](\d{1,2})[\-/\.](\d{1,4})', s)
    if sep_match:
        a, b, c = sep_match.groups()
        sep = '-' if '-' in s else ('/' if '/' in s else '.')
        lens = (len(a), len(b), len(c))
        # AAAA-MM-DD or AAAA.MM.DD
        if len(a) == 4:
            y, m, d = a, b, c
            dt = try_valid_date(y, m, d)
            return dt.strftime('%Y-%m-%d') if dt else INVALID
        # AAAA/DD/MM (4-digit year first but day/month order swapped, sep '/')
        if len(c) == 4:
            y = c
            # ambiguous between (a=month,b=day) and (a=day,b=month)
            # Known formats present: MM/DD/AAAA, DD/MM/AAAA, MM-DD-AA
            # Try MM/DD first (US standard), validate; if invalid try DD/MM
            dt = try_valid_date(y, a, b)
            if dt:
                return dt.strftime('%Y-%m-%d')
            dt = try_valid_date(y, b, a)
            if dt:
                return dt.strftime('%Y-%m-%d')
            return INVALID
        # 2-digit year cases: MM-DD-AA or MM/DD/AA
        if len(c) == 2:
            y = '20' + c
            dt = try_valid_date(y, a, b)
            if dt:
                return dt.strftime('%Y-%m-%d')
            dt = try_valid_date(y, b, a)
            if dt:
                return dt.strftime('%Y-%m-%d')
            return INVALID
        return INVALID

    return INVALID

df['sale_date_clean'] = df['sale_date'].apply(parse_sale_date)

# ---------- 2. customer_name ----------
def title_case_name(val):
    if pd.isna(val):
        return INVALID
    s = str(val).strip()
    s = s.replace('-', ' ')
    s = re.sub(r'\s+', ' ', s)
    return ' '.join(w.capitalize() for w in s.split(' '))

df['customer_name_clean'] = df['customer_name'].apply(title_case_name)

# ---------- 3. porsche_model ----------
CANONICAL_MODELS = [
    "911 Carrera", "911 Carrera S", "911 Carrera GTS", "911 Turbo", "911 Turbo S",
    "911 GT3", "911 GT3 RS", "911 Dakar", "911 Targa 4", "911 Targa 4S",
    "718 Cayman", "718 Cayman S", "718 Cayman GT4 RS", "718 Boxster",
    "718 Boxster GTS", "718 Spyder RS",
    "Cayenne", "Cayenne S", "Cayenne Coupe", "Cayenne E-Hybrid", "Cayenne Turbo",
    "Cayenne Turbo GT",
    "Macan", "Macan S", "Macan T", "Macan GTS", "Macan Electric",
    "Panamera", "Panamera 4", "Panamera 4S", "Panamera Turbo", "Panamera Turbo S",
    "Panamera 4 E-Hybrid",
    "Taycan", "Taycan 4S", "Taycan GTS", "Taycan Turbo", "Taycan Turbo S",
    "Taycan Cross Turismo",
]
CANON_LOOKUP = {re.sub(r'\s+', ' ', m.strip().lower()): m for m in CANONICAL_MODELS}

def title_case_model(s):
    # Title-case but keep all-caps short tokens reasonable; simple word capitalize
    words = s.split(' ')
    out = []
    for w in words:
        if '-' in w:
            out.append('-'.join(p.capitalize() for p in w.split('-')))
        else:
            out.append(w.capitalize())
    return ' '.join(out)

def normalize_model(val):
    if pd.isna(val):
        return title_case_model('')
    s = str(val).strip()
    s_norm = re.sub(r'\s+', ' ', s.lower())
    if s_norm in CANON_LOOKUP:
        return CANON_LOOKUP[s_norm]
    return title_case_model(re.sub(r'\s+', ' ', s.strip()))

df['porsche_model_clean'] = df['porsche_model'].apply(normalize_model)

# ---------- 4. model_year ----------
NUM_WORDS = {
    'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,
    'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,
    'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18,
    'nineteen':19,'twenty':20,'thirty':30,'forty':40,'fifty':50,
    'sixty':60,'seventy':70,'eighty':80,'ninety':90,
    'thousand':1000,'hundred':100
}

def words_to_number(s):
    tokens = s.lower().split()
    # "twenty twenty four" -> two pairs of two-digit groups (e.g., 20 + 24)
    if len(tokens) == 3 and all(t in NUM_WORDS for t in tokens):
        # pattern: twenty(20) twenty(20) four(4) -> 2024
        a, b, c = tokens
        if a in NUM_WORDS and b in NUM_WORDS and c in NUM_WORDS:
            part1 = NUM_WORDS[a]
            part2 = NUM_WORDS[b] + NUM_WORDS[c]
            if part1 >= 10 and part2 < 100:
                return part1 * 100 + part2
    # "two thousand twenty one" -> 2000 + 21
    total = 0
    current = 0
    for t in tokens:
        if t not in NUM_WORDS:
            return None
        val = NUM_WORDS[t]
        if val == 1000:
            current = max(current, 1) * 1000
            total += current
            current = 0
        elif val == 100:
            current = max(current, 1) * 100
        else:
            current += val
    total += current
    return total if total > 0 else None

def parse_model_year(val):
    if pd.isna(val):
        return INVALID
    s = str(val).strip()
    if re.fullmatch(r'\d{4}', s):
        y = int(s)
        return y if 2000 <= y <= 2035 else INVALID
    # "20-23", "20 24", "20 25"
    m = re.fullmatch(r'(\d{2})[\-\s](\d{2})', s)
    if m:
        y = int('20' + m.group(2))
        return y if 2000 <= y <= 2035 else INVALID
    # written words
    s_clean = s.lower().strip()
    n = words_to_number(s_clean)
    if n is not None and 2000 <= n <= 2035:
        return n
    return INVALID

df['model_year_clean'] = df['model_year'].apply(parse_model_year)

# ---------- 5. sale_price ----------
def words_to_number_price(s):
    tokens = s.lower().replace(',', ' ').split()
    total = 0
    current = 0
    found = False
    for t in tokens:
        if t in ('usd', 'dollars', 'dollar', 'and'):
            continue
        if t not in NUM_WORDS:
            return None
        found = True
        val = NUM_WORDS[t]
        if val == 1000:
            current = max(current, 1) * 1000
            total += current
            current = 0
        elif val == 100:
            current = max(current, 1) * 100
        else:
            current += val
    total += current
    return total if found and total > 0 else None

def parse_sale_price(val):
    if pd.isna(val):
        return INVALID
    s = str(val).strip()
    s_lower = s.lower()

    # written words
    if re.fullmatch(r'[a-z\s]+(usd|dollars)?', s_lower.replace('  ', ' ').strip()) and any(w in NUM_WORDS for w in s_lower.split()):
        n = words_to_number_price(s_lower)
        if n is not None:
            return round(float(n), 2)

    # remove currency words/symbols
    cleaned = re.sub(r'(usd|dollars|dollar)', '', s_lower, flags=re.IGNORECASE).strip()
    cleaned = cleaned.replace('$', '').strip()

    # k suffix (e.g., 121k)
    k_match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*k', cleaned)
    if k_match:
        return round(float(k_match.group(1)) * 1000, 2)

    # now cleaned should be a number with various separators
    # detect decimal separator: if both , and . present, last one is decimal
    has_comma = ',' in cleaned
    has_dot = '.' in cleaned
    try:
        if has_comma and has_dot:
            if cleaned.rfind(',') > cleaned.rfind('.'):
                # comma is decimal: European format 89.750,00
                num = cleaned.replace('.', '').replace(',', '.')
            else:
                # dot is decimal: US format 1,234.56
                num = cleaned.replace(',', '')
            return round(float(num), 2)
        elif has_comma and not has_dot:
            # comma could be thousand sep (79,500) -> remove
            num = cleaned.replace(',', '')
            return round(float(num), 2)
        elif has_dot and not has_comma:
            # ambiguous: could be thousand sep (89.750) or decimal (153200.50)
            parts = cleaned.split('.')
            if len(parts[-1]) == 2:
                # decimal
                num = cleaned.replace('.', '', cleaned.count('.') - 1) if cleaned.count('.') > 1 else cleaned
                return round(float(num), 2)
            else:
                # thousands separator
                num = cleaned.replace('.', '')
                return round(float(num), 2)
        else:
            return round(float(cleaned), 2)
    except Exception:
        return INVALID

df['sale_price_clean'] = df['sale_price'].apply(parse_sale_price)

# ---------- 6. vehicle_mileage ----------
def words_to_number_mileage(s):
    tokens = s.lower().split()
    total = 0
    current = 0
    found = False
    for t in tokens:
        if t in ('miles', 'mi', 'mile'):
            continue
        if t not in NUM_WORDS:
            return None
        found = True
        val = NUM_WORDS[t]
        if val == 1000:
            current = max(current, 1) * 1000
            total += current
            current = 0
        elif val == 100:
            current = max(current, 1) * 100
        else:
            current += val
    total += current
    return total if found else None

def parse_mileage(val):
    if pd.isna(val):
        return INVALID
    s = str(val).strip()
    s_lower = s.lower()

    if s_lower in ('new', 'new car', 'zero', 'zero miles', 'zero mi'):
        return 0

    # written words
    if any(w in NUM_WORDS for w in re.findall(r'[a-z]+', s_lower)):
        n = words_to_number_mileage(s_lower)
        if n is not None:
            return int(n)

    is_km = bool(re.search(r'\bkm\b', s_lower))
    # extract number
    num_match = re.search(r'[\d.,]+', s)
    if not num_match:
        return INVALID
    num_str = num_match.group(0)

    has_comma = ',' in num_str
    has_dot = '.' in num_str
    try:
        if has_comma and has_dot:
            if num_str.rfind(',') > num_str.rfind('.'):
                num = num_str.replace('.', '').replace(',', '.')
            else:
                num = num_str.replace(',', '')
            value = float(num)
        elif has_comma:
            value = float(num_str.replace(',', ''))
        elif has_dot:
            parts = num_str.split('.')
            if len(parts[-1]) == 3:
                # thousands sep, e.g. 1.200 / 41.000
                value = float(num_str.replace('.', ''))
            else:
                value = float(num_str)
        else:
            value = float(num_str)
    except Exception:
        return INVALID

    if is_km:
        value = value * 0.621371

    return int(round(value))

df['vehicle_mileage_clean'] = df['vehicle_mileage'].apply(parse_mileage)

# ---------- 7. payment_method ----------
PAYMENT_MAP = {
    'credit card': 'Credit Card', 'creditcard': 'Credit Card', 'credit': 'Credit Card',
    'credit card payment': 'Credit Card',
    'debit card': 'Debit Card',
    'cash': 'Cash', 'cash payment': 'Cash',
    'bank transfer': 'Bank Transfer', 'bank-transfer': 'Bank Transfer',
    'bank_transfer': 'Bank Transfer', 'bank wire': 'Bank Transfer',
    'wire': 'Wire Transfer', 'wire transfer': 'Wire Transfer',
    'wiretransfer': 'Wire Transfer', 'wire-transfer': 'Wire Transfer',
    'financing': 'Financing', 'financing plan': 'Financing', 'finance': 'Financing',
    'lease': 'Lease', 'leasing': 'Lease', 'lease plan': 'Lease',
    'ach payment': 'ACH', 'ach': 'ACH',
    'crypto': 'Crypto', 'crypto payment': 'Crypto',
}

def normalize_payment(val):
    if pd.isna(val):
        return INVALID
    s = str(val).strip().lower()
    s = re.sub(r'[_\-]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    if s in PAYMENT_MAP:
        return PAYMENT_MAP[s]
    return INVALID

df['payment_method_clean'] = df['payment_method'].apply(normalize_payment)

# ---------- 8. city ----------
def title_case_city(val):
    if pd.isna(val):
        return INVALID
    s = str(val).strip()
    s = re.sub(r'\s+', ' ', s)
    parts = s.split(' ')
    out = []
    for p in parts:
        if '.' in p:
            out.append('.'.join(seg.capitalize() for seg in p.split('.')))
        else:
            out.append(p.capitalize())
    return ' '.join(out)

df['city_clean'] = df['city'].apply(title_case_city)

# ---------- 9. state ----------
STATE_NAME_TO_ABBR = {
    'alabama':'AL','alaska':'AK','arizona':'AZ','arkansas':'AR','california':'CA',
    'colorado':'CO','connecticut':'CT','delaware':'DE','florida':'FL','georgia':'GA',
    'hawaii':'HI','idaho':'ID','illinois':'IL','indiana':'IN','iowa':'IA',
    'kansas':'KS','kentucky':'KY','louisiana':'LA','maine':'ME','maryland':'MD',
    'massachusetts':'MA','michigan':'MI','minnesota':'MN','mississippi':'MS',
    'missouri':'MO','montana':'MT','nebraska':'NE','nevada':'NV',
    'new hampshire':'NH','new jersey':'NJ','new mexico':'NM','new york':'NY',
    'north carolina':'NC','north dakota':'ND','ohio':'OH','oklahoma':'OK',
    'oregon':'OR','pennsylvania':'PA','rhode island':'RI','south carolina':'SC',
    'south dakota':'SD','tennessee':'TN','texas':'TX','utah':'UT','vermont':'VT',
    'virginia':'VA','washington':'WA','west virginia':'WV','wisconsin':'WI',
    'wyoming':'WY',
}
VALID_ABBR = set(STATE_NAME_TO_ABBR.values())

def normalize_state(val):
    if pd.isna(val):
        return INVALID
    s = str(val).strip()
    if len(s) == 2 and s.upper() in VALID_ABBR:
        return s.upper()
    s_lower = s.lower()
    if s_lower in STATE_NAME_TO_ABBR:
        return STATE_NAME_TO_ABBR[s_lower]
    return INVALID

df['state_clean'] = df['state'].apply(normalize_state)

# ---------- 10. salesperson ----------
df['salesperson_clean'] = df['salesperson'].apply(title_case_name)

# ---------- 11. delivery_status ----------
STATUS_MAP = {
    'delivered': 'Delivered', 'deliverd': 'Delivered',
    'pending': 'Pending',
    'pending approval': 'Pending Approval',
    'pending review': 'Pending Review',
    'in transit': 'In Transit',
    'shipped': 'Shipped',
    'cancelled': 'Cancelled',
    'awaiting delivery': 'Awaiting Delivery',
    'awaiting pickup': 'Awaiting Pickup',
    'awaiting review': 'Awaiting Review',
}

def normalize_status(val):
    if pd.isna(val):
        return INVALID
    s = str(val).strip().lower()
    s = re.sub(r'[!.\u2022]+', '', s)
    s = re.sub(r'[\-_]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    if s in STATUS_MAP:
        return STATUS_MAP[s]
    return INVALID

df['delivery_status_clean'] = df['delivery_status'].apply(normalize_status)

# ---------- Reorder columns: original col immediately followed by its _clean ----------
ordered_cols = []
for col in ['sale_id', 'sale_date', 'customer_name', 'porsche_model', 'model_year',
            'sale_price', 'vehicle_mileage', 'payment_method', 'city', 'state',
            'salesperson', 'delivery_status']:
    ordered_cols.append(col)
    clean_col = f'{col}_clean'
    if clean_col in df.columns:
        ordered_cols.append(clean_col)

df = df[ordered_cols]
df.to_excel(OUT, sheet_name='db_psc_25354543_no_tracked', index=False)
print("OK", df.shape)
print(df.head(10).to_string())

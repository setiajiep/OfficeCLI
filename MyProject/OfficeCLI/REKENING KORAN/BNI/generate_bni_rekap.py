import glob, pdfplumber, re
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

def clean_page_chars(page):
    seen = set()
    clean = []
    for c in page.chars:
        key = (c['text'], round(c['x0'], 1), round(c['top'], 1))
        if key not in seen:
            seen.add(key)
            clean.append(c)
    return clean

def group_chars_by_line(chars):
    lines = []
    if not chars: return lines
    chars = sorted(chars, key=lambda c: (c['top'], c['x0']))
    cur = [chars[0]]
    for c in chars[1:]:
        if abs(c['top'] - cur[0]['top']) < 2.5:
            cur.append(c)
        else:
            lines.append(sorted(cur, key=lambda x: x['x0']))
            cur = [c]
    if cur:
        lines.append(sorted(cur, key=lambda x: x['x0']))
    return lines

def parse_pdf(filename):
    transactions = []
    meta = {}
    
    with pdfplumber.open(filename) as pdf:
        for page_idx, page in enumerate(pdf.pages, 1):
            chars = clean_page_chars(page)
            
            if page_idx == 1:
                page_text = page.extract_text()
                for line in page_text.split('\n'):
                    if 'Ledger Balance:' in line:
                        m = re.search(r'Ledger Balance:\s*([\d,]+\.\d{2})', line)
                        if m: meta['ledger_balance'] = float(m.group(1).replace(',', ''))
                    if 'Period' in line:
                        meta['period'] = line.split(':', 1)[-1].strip() if ':' in line else line
            
            last_text = page.extract_text()
            for line in last_text.split('\n'):
                if 'Ending Balance' in line:
                    m = re.search(r'Ending Balance\s*:\s*([\d,]+\.\d{2})', line)
                    if m: meta['ending_balance'] = float(m.group(1).replace(',', ''))
                if 'Total Debet' in line:
                    m = re.search(r'Total Debet\s*:\s*(\d+)?\s*([\d,]+\.\d{2})', line)
                    if m: meta['total_debit'] = float(m.group(2).replace(',', ''))
                if 'Total Credit' in line:
                    m = re.search(r'Total Credit\s*:\s*(\d+)?\s*([\d,]+\.\d{2})', line)
                    if m: meta['total_credit'] = float(m.group(2).replace(',', ''))

            lines_dict = {}
            for c in chars:
                if c['top'] < 320: continue
                t = round(c['top'], 1)
                matched = None
                for k in lines_dict:
                    if abs(k - t) < 2.5:
                        matched = k
                        break
                if matched is None:
                    lines_dict[t] = [c]
                else:
                    lines_dict[matched].append(c)
            
            sorted_tops = sorted(lines_dict.keys())
            table_tops = []
            for t in sorted_tops:
                l_str = ''.join(c['text'] for c in lines_dict[t]).strip()
                if any(k in l_str for k in ['Ending Balance', 'Total Debet', 'Total Credit', 'Ledger Balance']):
                    continue
                if 'SEJAHTERA BERSAMA 0' in l_str or 'ACCOUNT STATEMENT' in l_str:
                    continue
                table_tops.append(t)
                
            anchors = []
            for t in table_tops:
                l_chars = sorted(lines_dict[t], key=lambda x: x['x0'])
                d_str = ''.join(c['text'] for c in l_chars if 15 <= c['x0'] <= 125).strip()
                if re.match(r'^\d{2}/\d{2}/\d{4}', d_str):
                    anchors.append(t)
                    
            if not anchors:
                continue
                
            tx_groups = {anc: [] for anc in anchors}
            for t in table_tops:
                closest_anc = min(anchors, key=lambda a: abs(a - t))
                tx_groups[closest_anc].append(t)
                
            for anc in anchors:
                tops_for_tx = sorted(tx_groups[anc])
                tx_chars = [c for t in tops_for_tx for c in lines_dict[t]]
                
                anc_chars = sorted(lines_dict[anc], key=lambda c: c['x0'])
                post_date = ''.join(c['text'] for c in anc_chars if 15 <= c['x0'] < 125).strip()
                eff_date = ''.join(c['text'] for c in anc_chars if 125 <= c['x0'] < 230).strip()
                journal = ''.join(c['text'] for c in anc_chars if 290 <= c['x0'] < 335).strip()
                db_cr = ''.join(c['text'] for c in anc_chars if 575 <= c['x0'] < 610).strip()
                balance_str = ''.join(c['text'] for c in anc_chars if 610 <= c['x0'] < 710).strip()
                
                if not balance_str:
                    bal_chars = sorted([c for c in tx_chars if 610 <= c['x0'] < 710], key=lambda c: (c['top'], c['x0']))
                    balance_str = ''.join(c['text'] for c in bal_chars).strip()
                
                branch_chars = [c for c in tx_chars if 230 <= c['x0'] < 290]
                branch_lines = group_chars_by_line(branch_chars)
                branch = ' '.join(''.join(c['text'] for c in l) for l in branch_lines).strip()
                
                desc_chars = [c for c in tx_chars if 335 <= c['x0'] < 500]
                desc_lines = group_chars_by_line(desc_chars)
                desc = ' '.join(''.join(c['text'] for c in l) for l in desc_lines).strip()
                
                balance_val = float(balance_str.replace(',', '')) if balance_str else None
                
                transactions.append({
                    'source_file': filename,
                    'page': page_idx,
                    'posting_date': post_date,
                    'effective_date': eff_date,
                    'branch': branch,
                    'journal': journal,
                    'description': desc,
                    'db_cr': db_cr,
                    'balance_raw': balance_str,
                    'balance': balance_val
                })
                
    return meta, transactions

def get_category(desc):
    d = desc.upper()
    if 'MPN G2' in d: return 'Pajak (MPN G2)'
    if 'BPJS KES' in d: return 'BPJS Kesehatan'
    if 'BPJS TK' in d: return 'BPJS Ketenagakerjaan'
    if 'PLN' in d or 'BIAYA ADMIN (PLN' in d: return 'Listrik / PLN'
    if 'BIFAST' in d or 'BI FAST' in d: return 'Transfer BI-FAST'
    if 'SETOR TUNAI' in d: return 'Setor Tunai'
    if 'JASA GIRO' in d: return 'Jasa Giro'
    if 'BIAYA ADM' in d or 'BY TRX ATM' in d: return 'Biaya Admin / Bank'
    if 'PPH' in d: return 'Pajak PPh'
    if 'PEMINDAHAN' in d or 'TRANSFER' in d: return 'Transfer / Pemindahan'
    return 'Lainnya'

# Collect all data
month_names = {
    '2026-01_RK_BNI.pdf': 'Jan 2026',
    '2026-02_RK_BNI.pdf': 'Feb 2026',
    '2026-03_RK_BNI.pdf': 'Mar 2026',
    '2026-04_RK_BNI.pdf': 'Apr 2026',
    '2026-05_RK_BNI.pdf': 'Mei 2026',
    '2026-06_RK_BNI.pdf': 'Jun 2026',
    '2026-07_RK_BNI.pdf': 'Jul 2026',
}

pdf_files = sorted(glob.glob('*.pdf'))
all_data = []

for f in pdf_files:
    m_name = month_names.get(f, f)
    meta, txs = parse_pdf(f)
    cur_bal = meta['ledger_balance']
    for tx in txs:
        if tx['balance'] is not None:
            diff = round(tx['balance'] - cur_bal, 2)
            tx['amount'] = abs(diff)
            tx['db_cr'] = 'K' if diff > 0 else 'D'
            cur_bal = tx['balance']
        else:
            diff = round(meta['ending_balance'] - cur_bal, 2)
            tx['amount'] = abs(diff)
            tx['db_cr'] = 'K' if diff > 0 else 'D'
            tx['balance'] = meta['ending_balance']
            cur_bal = meta['ending_balance']
        tx['month'] = m_name
        tx['category'] = get_category(tx['description'])
    all_data.append((f, m_name, meta, txs))

print('Data parsing complete. Building Excel workbook...')

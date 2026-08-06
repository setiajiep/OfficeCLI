import pandas as pd
import numpy as np

# Load Sheet1
df_s1 = pd.read_excel('Akr_Payment.xlsx', sheet_name='Sheet1', header=None)
df_akr = pd.read_excel('Akr_Payment.xlsx', sheet_name='Payment Akr', header=6)

print("=== AKR PAYMENT SHEET ROWS ===")
print(df_akr[['No', 'Periode', 'Tanggal & Waktu', 'Mutasi Kredit / Masuk (Rp)', 'Keterangan / Remark']].to_string())

# Let's write a comprehensive parser to extract all payment blocks from Sheet1
# In Sheet1, tables are located at column blocks starting at index 0, 8, 16, 24

blocks = []

for r in range(len(df_s1)):
    for c in [0, 8, 16, 24]:
        val_no = str(df_s1.iloc[r, c]).strip()
        val_tgl = str(df_s1.iloc[r, c+1]).strip()
        
        if val_no == 'No' and val_tgl == 'Tanggal':
            # We found a table header at row r, col c
            invoices = []
            total_amt = None
            bayar_tgl = None
            
            # Scan down up to 20 rows
            for rr in range(r + 1, min(r + 25, len(df_s1))):
                no_val = df_s1.iloc[rr, c]
                inv_val = df_s1.iloc[rr, c+1]
                
                # Check for invoice in column c+1 ("Tanggal")
                if pd.notna(inv_val):
                    inv_str = str(inv_val).strip()
                    if inv_str not in ['No', 'Tanggal', 'Keterangan', 'Jumlah', 'TOTAL', 'nan'] and not inv_str.startswith('Bayar'):
                        invoices.append(inv_str)
                
                # Check across columns in this block for TOTAL and Bayar tgl
                for cc in range(c, min(c+8, df_s1.shape[1])):
                    cell_val = str(df_s1.iloc[rr, cc]).strip()
                    if 'TOTAL' in cell_val:
                        # find numerical total in this row
                        for cc2 in range(cc, min(cc+6, df_s1.shape[1])):
                            num = df_s1.iloc[rr, cc2]
                            if isinstance(num, (int, float, np.number)) and not np.isnan(num) and num > 0:
                                total_amt = float(num)
                    if 'Bayar tgl' in cell_val:
                        bayar_tgl = cell_val

            blocks.append({
                'r': r,
                'c': c,
                'invoices': invoices,
                'total': total_amt,
                'bayar_tgl': bayar_tgl
            })

print("\n=== PARSED SHEET1 TABLES ===")
for idx, b in enumerate(blocks, 1):
    print(f"Table {idx:2d} (R{b['header_row'] if 'header_row' in b else b['r']}, C{b['c']}): Bayar='{b['bayar_tgl']}' | Total={b['total']} | Invoices={b['invoices']}")

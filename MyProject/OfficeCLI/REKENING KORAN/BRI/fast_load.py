import pandas as pd
import numpy as np

# Load Sheet1 using pandas
df = pd.read_excel('Akr_Payment.xlsx', sheet_name='Sheet1', header=None)

print(f"Shape of Sheet1: {df.shape}")

# Save to CSV for quick viewing/inspection
df.to_csv('sheet1_pandas.csv', index=False)
print("Saved sheet1_pandas.csv")

import pandas as pd

file_path = "datadotgov_main.xlsx"

print("Reading file...")
if file_path.endswith('.xlsx'):
    df = pd.read_excel(file_path)
else:
    df = pd.read_csv(file_path)

column_name = 'ABN' 

if column_name in df.columns:
    # Convert to string and remove trailing '.0' if present
    abns = df[column_name].dropna().astype(str).str.split('.').str[0].str.strip().unique()
    
    with open("abn_list.txt", "w", encoding="utf-8") as f:
        for abn in abns:
            f.write(f"{abn}\n")
            
    print(f"Success! Extracted unique ABNs: {len(abns)}")
    print("File 'abn_list.txt' generated and ready to use!")
else:
    print(f"Error: Column '{column_name}' not found.")

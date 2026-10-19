import pandas as pd

INPUT_EXCEL = "all_charities_emails.xlsx"
CLEAN_OUTPUT_EXCEL = "clean_charities_emails.xlsx"

print("1. Reading the source file...")
df = pd.read_excel(INPUT_EXCEL)

# 2. Filtering: validate both Email and ABN fields
clean_df = df[
    # Email validation rules
    df['Email'].notna() & 
    (df['Email'].astype(str).str.strip().str.lower() != 'not found') &
    (df['Email'].astype(str).str.strip() != '') &
    (df['Email'].astype(str).str.strip() != 'nan') &
    
    # ABN validation rules
    df['ABN'].notna() &
    (df['ABN'].astype(str).str.strip() != '') &
    (df['ABN'].astype(str).str.strip() != 'nan')
].copy()

print(f"Total initial rows: {len(df)}")
print(f"Remaining pristine records (valid ABN and Email): {len(clean_df)}")

# 3. Saving the final clean dataset
clean_df.to_excel(CLEAN_OUTPUT_EXCEL, index=False)
print(f"Done! Clean dataset saved as: {CLEAN_OUTPUT_EXCEL}")

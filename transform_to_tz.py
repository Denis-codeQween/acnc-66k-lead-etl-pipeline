import pandas as pd

input_file = "acnc_full_database.xlsx"
output_file = "clean_charities_emails.xlsx"

print("[*] Loading database...")
df = pd.read_excel(input_file)

print(f"[*] Total rows in database: {len(df)}")

# 1. Filter only active companies (Registered)
df_active = df[df["Status"].astype(str).str.lower() == "registered"].copy()
print(f"[*] Active companies filtered (Registered): {len(df_active)}")

# 2. Build clean dataset using exact database keys
cleaned_df = pd.DataFrame()

cleaned_df["ABN"] = df_active.get("Abn", df_active.get("ABN", ""))
cleaned_df["Charity_Legal_Name"] = df_active.get("Name", "")
cleaned_df["Address_1_Address_Line_1"] = df_active.get("AddressLine1", "")
cleaned_df["Address_1_Address_Line_2"] = df_active.get("AddressLine2", "")
cleaned_df["Town_City"] = df_active.get("AddressSuburb", "")
cleaned_df["State"] = df_active.get("AddressStateOrProvince", "")
cleaned_df["Postcode"] = df_active.get("AddressPostalCode", "")
cleaned_df["Country"] = df_active.get("AddressCountry", "Australia")
cleaned_df["Charity_Size"] = df_active.get("CharitySize", "")
cleaned_df["Email"] = df_active.get("Email", "")

# Clean up rows with missing ABNs
cleaned_df = cleaned_df.dropna(subset=["ABN"])

# Save the result
cleaned_df.to_excel(output_file, index=False, engine="openpyxl")
print(f"[+] Done! Clean file saved as: {output_file}")
print(f"[+] Total rows in report: {len(cleaned_df)}")
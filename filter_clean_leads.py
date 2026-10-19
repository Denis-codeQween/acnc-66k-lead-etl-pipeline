import pandas as pd

INPUT_EXCEL = "all_charities_emails.xlsx"
CLEAN_OUTPUT_EXCEL = "clean_charities_emails.xlsx"

print("1. Читаем итоговый файл...")
df = pd.read_excel(INPUT_EXCEL)

# 2. Фильтруем: проверяем и Email, и ABN
clean_df = df[
    # Проверка E-mail
    df['Email'].notna() & 
    (df['Email'].astype(str).str.strip().str.lower() != 'not found') &
    (df['Email'].astype(str).str.strip() != '') &
    (df['Email'].astype(str).str.strip() != 'nan') &
    
    # Проверка ABN
    df['ABN'].notna() &
    (df['ABN'].astype(str).str.strip() != '') &
    (df['ABN'].astype(str).str.strip() != 'nan')
].copy()

print(f"Всего исходных строк: {len(df)}")
print(f"Осталось идеально чистых записей (есть и ABN, и Email): {len(clean_df)}")

# 3. Сохраняем итоговую базу
clean_df.to_excel(CLEAN_OUTPUT_EXCEL, index=False)
print(f"Готово! Чистый файл сохранен как: {CLEAN_OUTPUT_EXCEL}")
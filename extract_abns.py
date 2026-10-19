import pandas as pd

file_path = "datadotgov_main.xlsx"

print("Чтение файла...")
if file_path.endswith('.xlsx'):
    df = pd.read_excel(file_path)
else:
    df = pd.read_csv(file_path)

column_name = 'ABN' 

if column_name in df.columns:
    # Приводим к строке и убираем '.0' на конце, если он появился
    abns = df[column_name].dropna().astype(str).str.split('.').str[0].str.strip().unique()
    
    with open("abn_list.txt", "w", encoding="utf-8") as f:
        for abn in abns:
            f.write(f"{abn}\n")
            
    print(f"Успешно! Извлечено уникальных ABN: {len(abns)}")
    print("Файл 'abn_list.txt' очищен и готов к использованию!")
else:
    print(f"Ошибка: Колонка '{column_name}' не найдена.")
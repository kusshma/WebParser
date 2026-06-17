import os
import sqlite3

def process_files_comparison(folder_path, db_name, main_table, name_column):
    # 1. Получаем имена файлов без расширений
    files_in_folder = [
        os.path.splitext(f)[0] 
        for f in os.listdir(folder_path) 
        if os.path.isfile(os.path.join(folder_path, f))
    ]
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        # 2. Создаем временную таблицу для текущих файлов в папке
        cursor.execute('CREATE TEMP TABLE temp_folder_files (f_name TEXT)')
        cursor.executemany('INSERT INTO temp_folder_files VALUES (?)', [(f,) for f in files_in_folder])

        # --- РАБОТА С FOUND_FILES ---
        # Создаем таблицу, если её нет (структура как у основной таблицы)
        cursor.execute(f'CREATE TABLE IF NOT EXISTS found_files AS SELECT * FROM {main_table} WHERE 1=0')
        
        # Добавляем записи, которых еще нет в found_files
        cursor.execute(f'''
            INSERT INTO found_files
            SELECT * FROM {main_table} 
            WHERE {name_column} IN (SELECT f_name FROM temp_folder_files)
              AND {name_column} NOT IN (SELECT {name_column} FROM found_files)
        ''')

        # --- РАБОТА С MISSING_FILES ---
        # Создаем таблицу, если её нет
        cursor.execute('CREATE TABLE IF NOT EXISTS missing_files (f_name TEXT)')
        
        # Добавляем файлы, которых нет в основной базе И которых еще нет в missing_files
        cursor.execute(f'''
            INSERT INTO missing_files (f_name)
            SELECT f_name FROM temp_folder_files 
            WHERE f_name NOT IN (SELECT {name_column} FROM {main_table})
              AND f_name NOT IN (SELECT f_name FROM missing_files)
        ''')

        conn.commit()
        
        # Статистика
        cursor.execute('SELECT COUNT(*) FROM found_files')
        found_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM missing_files')
        missing_count = cursor.fetchone()[0]
        
        print(f"Обработка завершена (данные добавлены):")
        print(f"- Всего записей в 'found_files': {found_count}")
        print(f"- Всего записей в 'missing_files': {missing_count}")

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
    finally:
        conn.close()

# --- Настройки ---
path = r'C:\Users\ramik\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\Market\Selected'
db = r'D:\WebParser\mql5_products.db'
table = 'products'
column = 'title'

process_files_comparison(path, db, table, column)

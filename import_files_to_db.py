import os
import sqlite3

def scan_to_db(folder_path, db_name='D:\\WebParser\\files_list.db'):
    # 1. Получаем только имена файлов БЕЗ расширений
    files = [
        os.path.splitext(f)[0] 
        for f in os.listdir(folder_path) 
        if os.path.isfile(os.path.join(folder_path, f))
    ]
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute('CREATE TABLE IF NOT EXISTS file_names (id INTEGER PRIMARY KEY, name TEXT)')
    cursor.execute('DELETE FROM file_names')
    
    # Записываем в базу
    cursor.executemany('INSERT INTO file_names (name) VALUES (?)', [(name,) for name in files])
    
    conn.commit()
    conn.close()
    print(f"Добавлено имен файлов: {len(files)}")

# Запуск
scan_to_db('D:\\WebParser\\Selected')
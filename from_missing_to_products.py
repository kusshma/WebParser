import sqlite3

def append_missing_to_products(db_name, main_table, name_column, missing_table='missing_files'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        # Вставляем только те записи, которых еще нет в main_table (на всякий случай)
        query = f'''
            INSERT INTO {main_table} ({name_column})
            SELECT f_name FROM {missing_table}
            WHERE f_name NOT IN (SELECT {name_column} FROM {main_table})
        '''
        
        cursor.execute(query)
        added_count = cursor.rowcount
        conn.commit()
        
        print(f"Успешно добавлено новых записей в '{main_table}': {added_count}")
        
        # Опционально: очистить таблицу missing_files после переноса
        # cursor.execute(f'DELETE FROM {missing_table}')
        # conn.commit()

    except sqlite3.Error as e:
        print(f"Ошибка при переносе: {e}")
    finally:
        conn.close()

# --- Настройки ---
db = r'D:\WebParser\mql5_products.db'
table = 'products'
column = 'title'

append_missing_to_products(db, table, column)
import sqlite3
import os

# Указываем путь к базе данных
db_path = "D:\Python\Work\WebParser\mql5_products.db"  # замените на путь к вашей базе данных

# Путь к папке с файлами
folder_path = r"C:\Users\ramik\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\Market"

# Путь к файлу для не найденных файлов
nofiles_txt_path = os.path.join(os.path.dirname(__file__), 'nofiles.txt')

# подключение к базе
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Получаем все записи

cursor.execute("SELECT title FROM products")
titles = cursor.fetchall()

# Открываем файл для записи названий отсутствующих файлов
with open(nofiles_txt_path, 'w', encoding='utf-8') as nofiles_file:
    for row in titles:
        title = row[0]
        # Проверка наличия файла с именем title в папке
        file_path = os.path.join(folder_path, title+".ex5")
        if not os.path.isfile(file_path):
            # Если файла нет, записываем название
            nofiles_file.write(title + '\n')

# закрываем подключение
conn.close()
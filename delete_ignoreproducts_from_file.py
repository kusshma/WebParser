import sqlite3

# Настройки путей к файлам
INPUT_FILE = "output_filtered.txt"
OUTPUT_FILE = "output_filtered_clear.txt"
DB_NAME = "mql5_products.db"  # Укажите расширение, если это SQLite


def filter_products():
    try:
        # 1. Подключение к базе данных
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 2. Получение списка игнорируемых авторов из таблицы ignoreauthor
        # Предполагаем, что имя автора хранится в колонке 'author_name'
        cursor.execute("SELECT author FROM ignoreauthor")
        ignored_authors = {row[0].strip().lower() for row in cursor.fetchall()}

        # 3. Получение продуктов, которые принадлежат этим авторам
        # Предполагаем, что в таблице products есть колонки 'product_name' и 'author_name'
        query = """
            SELECT title
            FROM products 
            WHERE LOWER(author) IN ({})
        """.format(
            ",".join("?" for _ in ignored_authors)
        )

        cursor.execute(query, list(ignored_authors))
        forbidden_products = {row[0].strip().lower() for row in cursor.fetchall()}

        # Закрываем соединение с БД
        conn.close()

        # 4. Фильтрация текстового файла
        with open(INPUT_FILE, "r", encoding="utf-8") as infile, open(
            OUTPUT_FILE, "w", encoding="utf-8"
        ) as outfile:

            for line in infile:
                product_name = line.strip()

                # Если строка пустая или продукт в черном списке — пропускаем
                if not product_name or product_name.lower() in forbidden_products:
                    continue

                # Записываем разрешенные продукты
                outfile.write(product_name + "\n")

        print(f"Фильтрация успешно завершена. Результат сохранен в {OUTPUT_FILE}")

    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")
    except FileNotFoundError:
        print(f"Ошибка: Файл {INPUT_FILE} не найден.")


if __name__ == "__main__":
    filter_products()
import os
import re
import sqlite3
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import subprocess


DB = "mql5_products.db"


class Database:

    def __init__(self):
        self.db = sqlite3.connect(DB)
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            author TEXT,
            price TEXT,
            rating TEXT,
            description TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """)
        self.db.commit()

    def is_ignored_author(self, author):
        query = "SELECT 1 FROM ignoreauthor WHERE author = ? LIMIT 1"
        cursor = self.db.cursor()
        cursor.execute(query, (author,))
        result = cursor.fetchone()
        cursor.close()
        return result is not None

    def is_product_exists(self, title):
        """Проверяет, есть ли уже продукт в базе"""
        cursor = self.db.execute(
            "SELECT COUNT(*) FROM products WHERE title = ?", (title,)
        )
        exists = cursor.fetchone()[0] > 0
        return exists

    def save(self, d):
        try:
            created_at = updated_at = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            url = d["url"]
            title = d["title"] if d["title"] else ""
            author = d["author"] if d["author"] else ""
            price = str(d["price"]) if d["price"] else ""
            rating = str(d["rating"]) if d["rating"] else ""
            description = d["description"] if "description" in d else ""

            if not url or not title:
                return False

            self.db.execute(
                """
                INSERT INTO products(url, title, author, price, rating, description, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(url) DO UPDATE SET 
                    title=excluded.title,
                    author=excluded.author,
                    price=excluded.price,
                    rating=excluded.rating,
                    description=excluded.description,
                    updated_at=excluded.updated_at
            """,
                (
                    url,
                    title,
                    author,
                    price,
                    rating,
                    description,
                    created_at,
                    updated_at,
                ),
            )

            self.db.commit()
            print(f"💾 Сохранено в БД: {title}")

            newfiles_txt_path = os.path.join(os.path.dirname(__file__), 'newfiles_new.txt')
            with open(newfiles_txt_path, 'a', encoding='utf-8') as newfiles_file:
                newfiles_file.write(title + '\n')

            return True            


        except Exception as e:
            print(f"[DB ERROR] {e}")
            self.db.rollback()
            return False


class MQL5Parser:

    db = Database()

    def scroll(self, page):
        for _ in range(10):
            page.mouse.wheel(0, 2200)
            page.wait_for_timeout(1500)

    import re


    def trigger_mt5_download(self, page, url):
        """Универсальная функция для отправки платных (демо) и бесплатных продуктов в MT5"""
        print(f"🚀 Перехожу на страницу продукта: {url}")
        try:
            page.goto(url, timeout=60000, wait_until="networkidle")

            # 1. Ищем главную кнопку. На бесплатном это "Скачать", на платном - "Скачать демо бесплатно"
            # Используем селектор, который переберет все возможные текстовые варианты на RU и EN
            target_button = page.locator(
                "a.buy_button:has-text('Скачать'), "
                "a.buy_button:has-text('Download'), "
                "a.buy_button:has-text('Скачать демо'), "
                "a.buy_button:has-text('Download Demo')"
            ).first

            if target_button.count() == 0:
                print(f"❌ Кнопка скачивания не найдена на странице {url}")
                return

            print("🖱️ Нажимаю на первичную кнопку скачивания...")
            target_button.click()

            # Ждем 1.5 секунды, пока отработает внутренний JS сайта и отобразит скрытое диалоговое окно
            page.wait_for_timeout(1500)

            # 2. Ищем кнопку подтверждения "Да, у меня есть MetaTrader 5" внутри всплывающего блока (.hasMt5Window)
            confirm_button = page.locator(
                "div.hasMt5Window button:has-text('MetaTrader'), "
                "div.hasMt5Window button:has-text('у меня есть')"
            ).first

            if confirm_button.count() > 0:
                # Вытаскиваем JS-код, зашитый в атрибут onclick
                onclick_content = confirm_button.get_attribute("onclick")

                if onclick_content:
                    # Регуляркой забираем всё, что находится внутри mql5buy://...
                    match = re.search(
                    r"(mql5buy://[^'\"]+)", onclick_content
                    )  # Ищет mql5buy://... до закрывающей кавычки
                    if match:
                        mql5_link = match.group(1)
                        print(f"🎯 Ссылка успешно извлечена: {mql5_link}")

                        # 3. Передаем команду напрямую в систему через страницу браузера
                        print("📡 Отправляю команду в MetaTrader...")
                        try:
                            os.startfile(mql5_link)
                            time.sleep(10)

                        except Exception:
                            # Ловим и глушим ожидаемое исключение Playwright,
                            # так как протокол mql5buy:// не возвращает HTTP-страницу.
                            pass

                        page.wait_for_timeout(4000)  # Даем время терминалу проснуться
                        print("✅ Процесс передачи команды завершен.")
                        return

            print(f"❌ Не удалось распарсить JS-ссылку во всплывающем окне {url}")

        except Exception as e:
            print(f"❌ Критическая ошибка при обработке {url}: {e}")

    def process_market(self, page, pages=1):
        """Основной цикл обхода страниц"""
        BASE = "https://www.mql5.com/en/market/mt5/expert/page{}/"

        for num in range(1, pages + 1):
            url = BASE.format(num)
            print(f"\n📄 Открываю страницу каталога {num}: {url}")

            try:
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(2000)
                self.scroll(page)
                items = page.query_selector_all("div.product-card")
                print(f"  → Найдено товаров: {len(items)}")

                for el in items:
                    a = el.query_selector("a.product-card__title")
                    if not a:
                        continue

                    link = a.get_attribute("href")
                    if not link:
                        continue

                    full_link = (
                        link
                        if link.startswith("http")
                        else "https://www.mql5.com" + link
                    )

                    title_el = el.query_selector(
                        "a.product-card__title span.product-card__title-wrapper"
                    )
                    title = title_el.inner_text().strip() if title_el else ""

                    author_el = el.query_selector("div.product-card__author")
                    author = author_el.inner_text().strip() if author_el else ""

                    # Проверки
                    if self.db.is_ignored_author(author):
                        print(f"⛔ Пропущен автор: {author}")
                        continue

                    if self.db.is_product_exists(title):
                        print(
                            f"⚠️ '{title}' уже обрабатывался. Пропускаем клик."
                        )
                        continue

                    # Сбор дополнительных полей
                    rating_el = el.query_selector(
                        "div.product-card__info span.g-rating__info"
                    )
                    rating_text = (
                        rating_el.inner_text().strip() if rating_el else ""
                    )
                    rating_value = ""
                    reviews_count = ""
                    if rating_text:
                        match = re.match(r"([0-9.]+) \((\d+)\)", rating_text)
                        if match:
                            rating_value = match.group(1)
                            reviews_count = match.group(2)

                    desc_el = el.query_selector("div.product-card__description")
                    description = desc_el.inner_text().strip() if desc_el else ""

                    price_el = el.query_selector("a.product-card__price")
                    price = price_el.inner_text().strip() if price_el else ""

                    data = {
                        "url": full_link,
                        "title": title,
                        "author": author,
                        "price": price,
                        "rating": rating_value,
                        "reviews": reviews_count,
                        "description": description,
                    }

                    # Сохраняем и кликаем только если это НОВЫЙ продукт
                    if self.db.save(data):
                        # Создаем чистую временную вкладку для карточки товара
                        det_page = page.context.new_page()
                        self.trigger_mt5_download(det_page, full_link)
                        det_page.close()
                        time.sleep(1)

            except Exception as e:
                print(f"[ERROR IN PAGE PROCESSING]: {e}")


# ===================== MAIN ===============================


def main():
    with sync_playwright() as p:
        # Запуск браузера с флагами, отключающими блокировку внешних протоколов
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-features=IsolateOrigins,site-per-process",
                "--process-per-site",
            ],
        )

        # Конфигурируем контекст: разрешаем скачивания по умолчанию
        context = browser.new_context(accept_downloads=True)

        page = context.new_page()
        mql = MQL5Parser()

        # Меняйте количество страниц по необходимости
        mql.process_market(page, pages=20)

        browser.close()
        print("\n🏁 Скрипт завершил работу!")


if __name__ == "__main__":
    main()
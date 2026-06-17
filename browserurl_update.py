import sqlite3
import tkinter as tk
from tkinter import messagebox
from tkinterweb import HtmlFrame

class FileViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Редактор записей mql5_products")
        self.root.geometry("1200x800")

        # Подключение к БД
        self.db_path = 'D:\\WebParser\\mql5_products.db'
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        self.load_data()
        self.current_index = 0

        if not self.records:
            messagebox.showinfo("Инфо", "Таблица пуста")
            self.root.destroy()
            return

        self.main_paned = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        self.left_frame = tk.Frame(self.main_paned)
        self.main_paned.add(self.left_frame)

        # Поля (убедитесь, что порядок совпадает с SELECT *)
        self.fields = ['ID', 'URL', 'Title', 'Author', 'Price', 'Rating', 'Description', 'Created_At', 'Updated_At']
        self.entries = {}

        for i, field in enumerate(self.fields):
            lbl = tk.Label(self.left_frame, text=field + ":", font=('Arial', 10, 'bold'))
            lbl.grid(row=i, column=0, sticky='e', padx=10, pady=5)
            
            ent = tk.Entry(self.left_frame, width=40)
            ent.grid(row=i, column=1, padx=10, pady=5)
            self.entries[field] = ent
            
        # ID редактировать нельзя
        self.entries['ID'].config(state='readonly')

        # Кнопки управления
        btn_frame = tk.Frame(self.left_frame)
        btn_frame.grid(row=len(self.fields), column=0, columnspan=2, pady=10)

        tk.Button(btn_frame, text="<< Назад", command=self.prev_record).pack(side=tk.LEFT, padx=5)
        self.lbl_status = tk.Label(btn_frame, text="")
        self.lbl_status.pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Вперед >>", command=self.next_record).pack(side=tk.LEFT, padx=5)

        # Кнопка СОХРАНЕНИЯ
        save_btn = tk.Button(self.left_frame, text="💾 СОХРАНИТЬ ИЗМЕНЕНИЯ", bg="#4CAF50", fg="white", 
                             font=('Arial', 10, 'bold'), command=self.save_record)
        save_btn.grid(row=len(self.fields)+1, column=0, columnspan=2, pady=10, sticky='we', padx=20)

        self.browser_frame = HtmlFrame(self.main_paned)
        self.main_paned.add(self.browser_frame)

        self.show_record()

    def load_data(self):
        """Загрузка или обновление данных из БД"""
        self.cursor.execute("SELECT * FROM found_files ORDER BY Price")
        self.records = self.cursor.fetchall()

    def show_record(self):
        record = self.records[self.current_index]
        for i, field in enumerate(self.fields):
            self.entries[field].config(state='normal') # Разблокируем для вставки
            self.entries[field].delete(0, tk.END)
            self.entries[field].insert(0, str(record[i]))
            if field == 'ID':
                self.entries[field].config(state='readonly') # Снова блокируем ID
        
        url = self.entries['URL'].get()
        if url.startswith('http'):
            self.browser_frame.load_website(url)
        
        self.lbl_status.config(text=f"{self.current_index + 1} из {len(self.records)}")

    def save_record(self):
        """Записывает измененные данные из полей обратно в БД"""
        try:
            # Собираем данные из полей (кроме ID)
            data = {f: self.entries[f].get() for f in self.fields}
            record_id = data['ID']

            query = """
                UPDATE found_files 
                SET URL=?, Title=?, Author=?, Price=?, Rating=?, Description=?, [Created_At]=?, [Updated_At]=?
                WHERE ID=?
            """
            params = (data['URL'], data['Title'], data['Author'], data['Price'], 
                      data['Rating'], data['Description'], data['Created_At'], data['Updated_At'], record_id)
            
            self.cursor.execute(query, params)
            self.conn.commit()
            
            # Обновляем локальный список записей, чтобы данные не "откатились" при навигации
            self.load_data()
            messagebox.showinfo("Успех", "Данные успешно обновлены!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def next_record(self):
        if self.current_index < len(self.records) - 1:
            self.current_index += 1
            self.show_record()

    def prev_record(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_record()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileViewerApp(root)
    root.mainloop()

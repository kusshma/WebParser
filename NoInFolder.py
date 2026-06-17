import os

# НАСТРОЙКИ: Укажите свои пути к файлам и папке
folder_path = "C:\\Users\\ramik\\\AppData\Roaming\\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075\\MQL5\\Experts\\Market\\"  # Папка с файлами .ex5
input_txt = "newfiles_new.txt"       # Исходный файл с названиями (без .ex5)
output_txt = "missed.txt"     # Итоговый файл для отсутствующих имен

def find_missing_ex5_files(folder, check_list, result_file):
    # 1. Проверяем существование папки
    if not os.path.exists(folder):
        print(f"Ошибка: Папка '{folder}' не найдена.")
        return
        
    # 2. Собираем реальные файлы из папки (в нижнем регистре для точности)
    folder_files = {f.lower() for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))}

    # 3. Читаем имена из текстового файла
    try:
        with open(check_list, "r", encoding="utf-8") as f:
            requested_names = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Ошибка: Файл '{check_list}' не найден.")
        return

    missing_names = []

    # 4. Проверяем наличие каждого файла, добавляя к нему .ex5
    for name in requested_names:
        # Формируем имя файла с расширением
        filename_with_ext = f"{name}.ex5"
        
        # Проверяем его наличие в папке без учета регистра
        if filename_with_ext.lower() not in folder_files:
            missing_names.append(name)  # Записываем чистое имя (без .ex5), как в исходном файле

    # 5. Записываем результат в новый файл
    with open(result_file, "w", encoding="utf-8") as f:
        for name in missing_names:
            f.write(name + "\n")

    print(f"Проверка завершена! Всего в списке: {len(requested_names)}.")
    print(f"Отсутствует файлов .ex5: {len(missing_names)}.")
    print(f"Результат сохранен в: {result_file}")

# Запуск скрипта
if __name__ == "__main__":
    find_missing_ex5_files(folder_path, input_txt, output_txt)

def reverse_file(input_path, output_path):
    # Читаем все строки из исходного файла
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Записываем строки в обратном порядке в новый файл
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(reversed(lines))

# Пример использования
reverse_file('old.txt', 'output.txt')
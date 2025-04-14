import os
import pathlib
import logging
import pyperclip
from typing import Optional, Tuple, List
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_gitignore_patterns(folder_path: str) -> Optional[PathSpec]:
    """
    Загружает шаблоны из .gitignore в указанной директории.
    """
    gitignore_path = os.path.join(folder_path, '.gitignore')
    if not os.path.exists(gitignore_path):
        return None

    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return PathSpec.from_lines(GitWildMatchPattern, patterns)
    except Exception as e:
        logging.error(f"Ошибка при загрузке .gitignore: {e}")
        return None


def is_ignored(ignore_spec: Optional[PathSpec], base_path: pathlib.Path, path: str) -> bool:
    """
    Проверяет, игнорируется ли файл/директория согласно .gitignore.
    """
    if not ignore_spec:
        return False

    try:
        relative_path = pathlib.Path(path).relative_to(base_path).as_posix()
        # Если это директория, добавляем завершающий слеш для корректного сопоставления
        if os.path.isdir(path):
            relative_path += '/'
        return ignore_spec.match_file(relative_path)
    except ValueError:
        return False


def get_all_code_files(folder_path: str) -> Tuple[str, int, int]:
    """
    Обходит папку и собирает содержимое файлов с расширениями, относящимися к коду,
    пропуская файлы, соответствующие .gitignore или не читаемые.
    """
    code_extensions = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
        '.cs', '.go', '.rb', '.php', '.swift', '.kt', '.kts', '.scala', '.rs',
        '.m', '.sql', '.html', '.css', '.scss', '.sass', '.less', '.xml', '.json',
        '.yaml', '.yml', '.ini', '.cfg', '.conf', '.toml', '.sh', '.bat', '.ps1',
        '.cmd', '.md', '.txt',
    }

    code_contents: List[str] = []
    total_files = 0
    skipped_files = 0

    ignore_spec = load_gitignore_patterns(folder_path)
    base_path = pathlib.Path(folder_path)

    for root, dirs, files in os.walk(folder_path, topdown=True):
        # Пропускаем игнорируемые директории
        dirs[:] = [d for d in dirs if not is_ignored(ignore_spec, base_path, os.path.join(root, d))]

        for file in files:
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file)

            if ext.lower() in code_extensions:
                if is_ignored(ignore_spec, base_path, file_path):
                    skipped_files += 1
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    relative_path = os.path.relpath(file_path, folder_path)
                    code_contents.append(f'=== {relative_path} ===\n{content}\n')
                    total_files += 1
                except UnicodeDecodeError:
                    logging.warning(f"UnicodeDecodeError при чтении файла {file_path}. Пропускаем.")
                    skipped_files += 1
                except Exception as e:
                    logging.error(f"Ошибка при обработке файла {file_path}: {e}")
                    skipped_files += 1
            else:
                skipped_files += 1

    final_output = f'Total code files: {total_files}\nSkipped files: {skipped_files}\n\n' + '\n'.join(code_contents)
    return final_output, total_files, skipped_files


def main() -> None:
    folder_path = input("Enter the full path to your code folder: ").strip()
    if not os.path.isdir(folder_path):
        print("Invalid directory path. Exiting.")
        return

    output, total_files, skipped_files = get_all_code_files(folder_path)
    
    pyperclip.copy(output)
    print(f'\nSuccess! Code from {total_files} files copied to clipboard.')
    print(f'Skipped {skipped_files} files/directories (non-code or gitignored)')


if __name__ == '__main__':
    main()

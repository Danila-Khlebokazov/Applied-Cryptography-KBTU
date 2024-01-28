import curses
import tkinter as tk
from tkinter import filedialog
import threading
import time

from des_cipher import bytes_to_bits, encode_bits as des_encode, bits_to_bytes, create_random_key, \
    decode_bits as des_decode

PROGRAM_NAME = 'SymmetricCipherEncoder'
VERSION = "0.9.0"
AUTHOR = "Khlebokazov Danila"

RUNNING_TITLE = f"{PROGRAM_NAME} v.{VERSION} // {AUTHOR}"

WELCOME_TEXT = "Добро пожаловать в программу!"
PRESS_ENTER_TEXT = "Нажмите Enter для продолжения..."
GOODBYE_TEXT = "До свидания! Спасибо за использование программы."
CONGRATS_TEXT = "Процесс завершился!"
ENCODE_PROCESS_TEXT = "Процесс шифрования..."
DECODE_PROCESS_TEXT = "Процесс расшифрования..."

MENU_DOWN_SHIFT = 1


class Stepper:
    def __init__(self, total_steps):
        self.total_steps = total_steps
        self.current_step = 0

    def step(self):
        self.current_step += 1

    def get_percentage(self):
        return self.current_step / self.total_steps

    def is_complete(self):
        return self.current_step >= self.total_steps


stepper = Stepper(100)


def loading_screen(stdscr, progress, title="Обработка..."):
    curses.curs_set(0)  # Скрываем курсор
    stdscr.clear()
    # Получаем размеры окна
    height, width = stdscr.getmaxyx()
    # Отображаем заголовок
    title_y = height // 2 - 1
    title_x = (width - len(title)) // 2
    stdscr.addstr(title_y, title_x, title, curses.A_BOLD)
    # Отображаем прогресс бар
    progress_bar_y = title_y + 2
    progress_bar_x = (width - 40) // 2  # Ширина прогресс бара 40 символов
    stdscr.addstr(progress_bar_y, progress_bar_x, "[", curses.A_BOLD)
    stdscr.addstr(progress_bar_y, progress_bar_x + 41, "]", curses.A_BOLD)

    # Анимированный индикатор загрузки
    indicator = "|/-\\"
    indicator_y = title_y + 4
    indicator_x = (width - 1) // 2
    while not progress.is_complete():
        # Обновляем прогресс бар
        progress_bar_width = int(progress.get_percentage() * 40)
        stdscr.addstr(progress_bar_y, progress_bar_x + 1, "=" * progress_bar_width)

        # Обновляем индикатор загрузки
        for char in indicator:
            stdscr.addch(indicator_y, indicator_x, char)
            stdscr.refresh()
            time.sleep(0.1)
            stdscr.addch(indicator_y, indicator_x, ' ')
            stdscr.refresh()
    # Обновляем прогресс бар до конца
    stdscr.addstr(progress_bar_y, progress_bar_x + 1, "=" * 40)


def change_state(_, state):
    global CURRENT_STATE
    CURRENT_STATE = state


def show_welcome_screen(stdscr, state):
    height, width = stdscr.getmaxyx()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(height // 2 - 1, (width - len(WELCOME_TEXT)) // 2, WELCOME_TEXT, curses.A_BOLD)
    stdscr.addstr(height // 2 + 1, (width - len(PRESS_ENTER_TEXT)) // 2, PRESS_ENTER_TEXT, curses.A_NORMAL)
    stdscr.attroff(curses.color_pair(1))
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key == 10:
            global CURRENT_STATE
            CURRENT_STATE = state
            break


def show_single_message(stdscr, message, state):
    height, width = stdscr.getmaxyx()
    start_width = (width - len(message)) // 2
    padding = " " * start_width
    stdscr.addstr(height // 2, 0, f"{padding}{message}".ljust(width), curses.A_BOLD)
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key == 10:
            global CURRENT_STATE
            CURRENT_STATE = state
            break


def show_menu(stdscr, options, **kwargs):
    current_option = 0
    max_option_length = max(len(option[0]) for option in options)

    if kwargs.get("extra_padding"):
        ext_padding = kwargs.get("extra_padding")
    else:
        ext_padding = 0

    while True:
        for i, (option, _) in enumerate(options):
            padding = " " * ((max_option_length - len(option)) + 2)
            if i == current_option:
                stdscr.addstr(i + MENU_DOWN_SHIFT + ext_padding, 0, f"> {option}{padding}",
                              curses.color_pair(1) | curses.A_REVERSE)
            else:
                stdscr.addstr(i + MENU_DOWN_SHIFT + ext_padding, 0, f"  {option}{padding}", curses.color_pair(1))

        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_option > 0:
            current_option -= 1
        elif key == curses.KEY_DOWN and current_option < len(options) - 1:
            current_option += 1
        elif key == 10:
            global CURRENT_STATE
            CURRENT_STATE = options[current_option][1]
            break


def enter_custom_key():
    # Ваш код для ввода своего ключа
    return input("Введите свой ключ: ")


def open_file_dialog(stdscr, next_func, *args, **kwargs):
    file_path = filedialog.askopenfilename(title="Выберите файл")
    next_func(stdscr, file_path, *args, **kwargs)


def get_save_path():
    save_path = filedialog.askdirectory(title="Выберите место для сохранения файла")
    return save_path


def show_file_menu(stdscr, file_path, options):
    stdscr.addstr(1, 0, f"Выбран файл: {file_path}", curses.color_pair(1))
    show_menu(stdscr, options, extra_padding=1)

    if CURRENT_STATE == "des_gen":
        key = create_random_key()
    elif CURRENT_STATE == "des_input":
        key = create_random_key()

    des_encode_choice(stdscr, file_path, key=key)


def des_encode_choice(stdscr, file_path, key: str = None):
    file_name = file_path.split("/")[-1]
    file_name_tuple = file_name.split(".")

    loading_thread = threading.Thread(target=loading_screen, args=(stdscr, stepper, ENCODE_PROCESS_TEXT))
    loading_thread.start()

    with open(file_path, "rb") as file:
        bytetext = file.read()
        bits = bytes_to_bits(bytetext)

    ciphertext, key = des_encode(bits, key, stepper)

    save_path = get_save_path()
    with open(f"{save_path}/{file_name}.bin", "wb+") as file:
        file.write(bits_to_bytes(ciphertext))
    with open(f"{save_path}/{file_name_tuple[0]}_key.bin", "wb+") as file:
        file.write(bits_to_bytes(key))

    loading_thread.join()
    change_state(1, "congrats")


def des_decode_choice(stdscr, file_path):
    key_types = [("Text files", "*.bin")]
    key_path = filedialog.askopenfilename(title="Выберите файл ключа", filetypes=key_types)

    loading_thread = threading.Thread(target=loading_screen, args=(stdscr, stepper, DECODE_PROCESS_TEXT))
    loading_thread.start()

    file_name = file_path.split("/")[-1]
    file_name = file_name.replace(".bin", "")

    with open(file_path, "rb") as file:
        bytetext = file.read()
        bits = bytes_to_bits(bytetext)
    with open(key_path, "rb") as file:
        bytetext = file.read()
        key = bytes_to_bits(bytetext)

    plaintext, key = des_decode(bits, key, stepper=stepper)
    save_path = get_save_path()
    with open(f"{save_path}/{file_name}", "wb+") as file:
        file.write(bits_to_bytes(plaintext))
    loading_thread.join()
    change_state(1, "congrats")


OPTIONS = {
    "hello": [show_welcome_screen, "main"],
    "main": [show_menu, [("DES", "DES"), ("Выйти из программы", "exit_text")]],
    "DES": [show_menu, [("Шифровать", "des_encode"), ("Расшифровать", "des_decode"), ("Назад в меню", "back_main")]],
    "exit_text": [show_single_message, GOODBYE_TEXT, "exit"],
    "des_encode": [open_file_dialog, show_file_menu,
                   [("Сгенерировать ключ", "des_gen"), ("Ввести свой ключ(Пока не работает)", "des_input")]],
    "des_decode": [open_file_dialog, des_decode_choice],
    "back_main": [change_state, "main"],
    "congrats": [show_single_message, CONGRATS_TEXT, "main"]
}

CURRENT_STATE = "hello"


def show_canvas(stdscr, extension, *args, **kwargs):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    stdscr.addstr(0, width - len(RUNNING_TITLE) - 2, RUNNING_TITLE, curses.A_BOLD | curses.color_pair(1))
    extension(stdscr, *args, **kwargs)


def main(stdscr):
    root = tk.Tk()
    root.withdraw()  # Скрываем основное окно
    height, width = stdscr.getmaxyx()
    curses.curs_set(0)
    curses.resizeterm(20, width)
    while True:
        if CURRENT_STATE == "exit":
            break

        show_canvas(stdscr, *OPTIONS[CURRENT_STATE])

    root.destroy()


if __name__ == "__main__":
    curses.wrapper(main)

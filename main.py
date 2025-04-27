import requests
import colorama
import os
import sys
import time
import readchar
from datetime import datetime, timezone
import json

API_BASE_URL = "https://discord.com/api/v10"
MESSAGE_HISTORY_LIMIT = 30
TOKEN_FILE = "token.json"

def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        return {}
    try:
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
            tokens = json.load(f)
            return tokens if isinstance(tokens, dict) else {}
    except (json.JSONDecodeError, IOError) as e:
        term_width = get_terminal_width()
        print_centered_text(f"Ошибка чтения файла токенов ({TOKEN_FILE}): {e}", term_width, colorama.Fore.RED)
        print_centered_text("Будет создан новый файл при добавлении аккаунта.", term_width, colorama.Fore.YELLOW)
        time.sleep(3)
        return {}

def save_tokens(tokens):
    try:
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, indent=4, ensure_ascii=False)
        return True
    except IOError as e:
        term_width = get_terminal_width()
        print_centered_text(f"Ошибка сохранения файла токенов ({TOKEN_FILE}): {e}", term_width, colorama.Fore.RED)
        time.sleep(3)
        return False

def get_headers(token):
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

def validate_token(token):
    url = f"{API_BASE_URL}/users/@me"
    headers = get_headers(token)
    term_width = get_terminal_width()
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            return f"{user_data['username']}#{user_data['discriminator']}"
        elif response.status_code == 401:
            return None
        else:
            print_centered_text(f"Ошибка API Discord при проверке tok: {response.status_code}", term_width, colorama.Fore.RED)
            return None
    except requests.exceptions.RequestException as e:
        print_centered_text(f"Ошибка сети при проверке токена: {e}", term_width, colorama.Fore.RED)
        return None

def get_server_list(token):
    url = f"{API_BASE_URL}/users/@me/guilds"
    headers = get_headers(token)
    term_width = get_terminal_width()
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print_centered_text(f"Ошибка при получении серверов: {response.status_code}", term_width, colorama.Fore.RED)
            return None
    except requests.exceptions.RequestException as e:
        print_centered_text(f"Ошибка сети (серверы): {e}", term_width, colorama.Fore.RED)
        return None

def get_dm_channels(token):
    url = f"{API_BASE_URL}/users/@me/channels"
    headers = get_headers(token)
    term_width = get_terminal_width()
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print_centered_text(f"Ошибка при получении ЛС: {response.status_code}", term_width, colorama.Fore.RED)
            return None
    except requests.exceptions.RequestException as e:
        print_centered_text(f"Ошибка сети (ЛС): {e}", term_width, colorama.Fore.RED)
        return None

def get_channel_list(token, server_id):
    url = f"{API_BASE_URL}/guilds/{server_id}/channels"
    headers = get_headers(token)
    term_width = get_terminal_width()
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return [ch for ch in response.json() if ch['type'] == 0]
        elif response.status_code == 403:
            print_centered_text(f"Нет прав для просмотра каналов.", term_width, colorama.Fore.RED)
            return None
        else:
            print_centered_text(f"Ошибка при получении каналов: {response.status_code}", term_width, colorama.Fore.RED)
            return None
    except requests.exceptions.RequestException as e:
        print_centered_text(f"Ошибка сети (каналы): {e}", term_width, colorama.Fore.RED)
        return None

def get_message_history(token, channel_id, limit=MESSAGE_HISTORY_LIMIT):
    url = f"{API_BASE_URL}/channels/{channel_id}/messages?limit={limit}"
    headers = get_headers(token)
    term_width = get_terminal_width()
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()[::-1]
        elif response.status_code == 403:
            print_centered_text(f"Нет прав на чтение истории.", term_width, colorama.Fore.RED)
            return None
        else:
            print_centered_text(f"Ошибка при получении истории: {response.status_code}", term_width, colorama.Fore.RED)
            return None
    except requests.exceptions.RequestException as e:
        print_centered_text(f"Ошибка сети (история): {e}", term_width, colorama.Fore.RED)
        return None

def send_message(token, channel_id, message):
    url = f"{API_BASE_URL}/channels/{channel_id}/messages"
    headers = get_headers(token)
    payload = {"content": message}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            return True
        elif response.status_code == 403:
            print(colorama.Fore.RED + "Ошибка отправки: Нет прав на отправку в этот канал.")
            time.sleep(2)
            return False
        else:
            print(colorama.Fore.RED + f"Ошибка отправки: {response.status_code} - {response.text}")
            time.sleep(2)
            return False
    except requests.exceptions.RequestException as e:
        print(colorama.Fore.RED + f"Ошибка сети при отправке: {e}")
        time.sleep(2)
        return False

def delete_message(token, channel_id, message_id):
    url = f"{API_BASE_URL}/channels/{channel_id}/messages/{message_id}"
    headers = get_headers(token)
    try:
        response = requests.delete(url, headers=headers, timeout=10)
        if response.status_code == 204:
            print(colorama.Fore.GREEN + "Сообщение успешно удалено.")
            time.sleep(1)
            return True
        elif response.status_code == 403:
            print(colorama.Fore.RED + "Ошибка: Нет прав на удаление сообщения (возможно, это не ваше сообщение).")
            time.sleep(2)
            return False
        elif response.status_code == 404:
            print(colorama.Fore.RED + "Ошибка: Сообщение не найдено.")
            time.sleep(2)
            return False
        else:
            print(colorama.Fore.RED + f"Ошибка удаления: {response.status_code} - {response.text}")
            time.sleep(2)
            return False
    except requests.exceptions.RequestException as e:
        print(colorama.Fore.RED + f"Ошибка сети при удалении: {e}")
        time.sleep(2)
        return False

def edit_message(token, channel_id, message_id, new_content):
    url = f"{API_BASE_URL}/channels/{channel_id}/messages/{message_id}"
    headers = get_headers(token)
    payload = {"content": new_content}
    try:
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            print(colorama.Fore.GREEN + "Сообщение успешно отредактировано.")
            time.sleep(1)
            return True
        elif response.status_code == 403:
            print(colorama.Fore.RED + "Ошибка: Нет прав на редактирование сообщения (возможно, это не ваше сообщение).")
            time.sleep(2)
            return False
        elif response.status_code == 404:
            print(colorama.Fore.RED + "Ошибка: Сообщение не найдено.")
            time.sleep(2)
            return False
        else:
            print(colorama.Fore.RED + f"Ошибка редактирования: {response.status_code} - {response.text}")
            time.sleep(2)
            return False
    except requests.exceptions.RequestException as e:
        print(colorama.Fore.RED + f"Ошибка сети при редактировании: {e}")
        time.sleep(2)
        return False

def get_terminal_size():
    try:
        return os.get_terminal_size()
    except OSError:
        return 80, 24

def get_terminal_width():
    return get_terminal_size()[0]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_centered_text(text, width, color_code=""):
    padding = max(0, (width - len(text)) // 2)
    print(" " * padding + color_code + text + colorama.Style.RESET_ALL)

def display_interactive_menu(title_text, options_list):
    term_width, term_height = get_terminal_size()
    border_char = "="; separator_char = "-"; side_border_char = "|"
    num_options = len(options_list)
    if num_options == 0: return None
    selected_index = 0

    is_channel_menu = "Выберите канал" in title_text or any(opt[0].startswith("# ") for opt in options_list)
    is_dm_menu = "Выберите ЛС" in title_text or any(opt[0].startswith("💬 ") or opt[0].startswith("👥 ") for opt in options_list)
    use_multi_columns = (is_channel_menu or is_dm_menu) and num_options > 10

    if use_multi_columns:
        min_column_width = 20
        spacing = 4
        max_option_len = max(len(opt[0].encode('utf-8').decode('utf-8')) for opt in options_list)
        column_width = max(min_column_width, max_option_len + 2)
        num_columns = max(1, (term_width - 2) // (column_width + spacing))
        num_columns = min(num_columns, 4)
        num_rows = (num_options + num_columns - 1) // num_columns
        total_content_width = (column_width * num_columns) + (spacing * (num_columns - 1))
        left_padding = max(0, (term_width - total_content_width - 2) // 2)
    else:
        num_columns = 1
        num_rows = num_options
        column_width = term_width - 4
        left_padding = 0

    while True:
        clear_screen()
        print(colorama.Fore.CYAN + colorama.Style.DIM + border_char * term_width)
        title_padding = max(0, (term_width - len(title_text)) // 2)
        right_padding = max(0, term_width - len(title_text) - title_padding)
        print(colorama.Fore.CYAN + " " * title_padding + colorama.Fore.YELLOW + colorama.Style.BRIGHT + title_text + colorama.Fore.CYAN + " " * right_padding)
        print(colorama.Fore.CYAN + colorama.Style.DIM + separator_char * term_width)
        print()

        if use_multi_columns:
            for row in range(num_rows):
                line_parts = []
                for col in range(num_columns):
                    idx = row + col * num_rows
                    if idx >= num_options:
                        line_parts.append(" " * column_width)
                        continue

                    display_text, return_value = options_list[idx]
                    is_selected = (idx == selected_index)

                    is_control_option = str(return_value).lower() in ["exit", "back", "add_new", "dm"]
                    is_exit_option = str(return_value).lower() == "exit"
                    is_add_option = str(return_value).lower() in ["add_new", "dm"]

                    option_fore_color = colorama.Fore.BLACK if is_selected else \
                                       (colorama.Fore.GREEN if is_add_option else \
                                       (colorama.Fore.RED if is_exit_option else \
                                       (colorama.Fore.YELLOW if is_control_option else colorama.Fore.WHITE)))
                    option_back_color = colorama.Back.CYAN if is_selected else colorama.Back.RESET
                    option_style = colorama.Style.BRIGHT if is_selected else colorama.Style.NORMAL

                    content = display_text[:column_width-2].encode('utf-8')[:column_width-2].decode('utf-8', errors='ignore')
                    content_len = len(content.encode('utf-8').decode('utf-8'))
                    left_internal_padding = (column_width - content_len) // 2
                    right_internal_padding = column_width - content_len - left_internal_padding
                    colored_content = (option_back_color + option_style + option_fore_color + " " * left_internal_padding + content + " " * right_internal_padding + colorama.Style.RESET_ALL)
                    line_parts.append(colored_content)

                final_line = (colorama.Fore.CYAN + side_border_char + " " * left_padding + 
                             (" " * spacing).join(line_parts) + " " * (term_width - total_content_width - left_padding - 2) + 
                             colorama.Fore.CYAN + side_border_char)
                final_line = final_line[:term_width-1]
                print(final_line)
        else:
            content_area_width = term_width - 2
            for idx, (display_text, return_value) in enumerate(options_list):
                content_len = len(display_text)
                total_internal_padding = max(0, content_area_width - content_len)
                left_internal_padding = total_internal_padding // 2
                right_internal_padding = total_internal_padding - left_internal_padding
                is_selected = (idx == selected_index)

                is_control_option = str(return_value).lower() in ["exit", "back", "add_new", "dm"]
                is_exit_option = str(return_value).lower() == "exit"
                is_add_option = str(return_value).lower() in ["add_new", "dm"]

                option_fore_color = colorama.Fore.BLACK if is_selected else \
                                   (colorama.Fore.GREEN if is_add_option else \
                                   (colorama.Fore.RED if is_exit_option else \
                                   (colorama.Fore.YELLOW if is_control_option else colorama.Fore.WHITE)))
                option_back_color = colorama.Back.CYAN if is_selected else colorama.Back.RESET
                option_style = colorama.Style.BRIGHT if is_selected else colorama.Style.NORMAL

                colored_content = (option_back_color + option_style + option_fore_color + display_text + colorama.Style.RESET_ALL)
                final_line = (colorama.Fore.CYAN + side_border_char + " " * left_internal_padding + colored_content + " " * right_internal_padding + colorama.Fore.CYAN + side_border_char)
                print(final_line)

        print()
        print(colorama.Fore.CYAN + colorama.Style.DIM + border_char * term_width)

        key_pressed = readchar.readkey()
        if key_pressed == readchar.key.UP:
            if use_multi_columns and selected_index >= num_rows:
                selected_index -= num_rows
            else:
                selected_index = max(0, selected_index - 1)
        elif key_pressed == readchar.key.DOWN:
            if use_multi_columns and selected_index + num_rows < num_options:
                selected_index += num_rows
            else:
                selected_index = min(num_options - 1, selected_index + 1)
        elif key_pressed == readchar.key.LEFT and use_multi_columns:
            selected_index = max(0, selected_index - 1)
        elif key_pressed == readchar.key.RIGHT and use_multi_columns:
            selected_index = min(num_options - 1, selected_index + 1)
        elif key_pressed == readchar.key.ENTER:
            clear_screen()
            return options_list[selected_index][1]
        elif key_pressed == readchar.key.CTRL_C:
            clear_screen()
            print_centered_text("Выход по Ctrl+C", term_width, colorama.Fore.YELLOW)
            return "exit"
        elif key_pressed == readchar.key.ESC:
            for _, ret_val in options_list:
                if str(ret_val).lower() == "back":
                    clear_screen()
                    return "back"
                if str(ret_val).lower() == "exit":
                    clear_screen()
                    return "exit"
            pass

def format_timestamp(iso_timestamp_str):
    try:
        ts_str = iso_timestamp_str.split('+')[0].split('.')[0]
        dt_object = datetime.fromisoformat(ts_str)
        return dt_object.strftime("%H:%M")
    except ValueError:
        return "??:??"

def display_chat_view(server_name, channel_name, history, is_dm=False):
    term_width, term_rows = get_terminal_size()
    clear_screen()
    print_centered_text(f"Сервер: {server_name}", term_width, colorama.Fore.GREEN)
    if is_dm:
        print_centered_text(f"ЛС: {channel_name}", term_width, colorama.Fore.CYAN)
    else:
        print_centered_text(f"Канал: #{channel_name}", term_width, colorama.Fore.CYAN)
    print(colorama.Fore.MAGENTA + "-" * term_width)
    available_rows = term_rows - 8
    start_index = max(0, len(history) - available_rows)
    if not history:
        print_centered_text("-- Нет сообщений --", term_width, colorama.Fore.YELLOW + colorama.Style.DIM)
    else:
        for idx, msg in enumerate(history[start_index:], start=start_index):
            try:
                ts = format_timestamp(msg['timestamp'])
                author = msg['author']
                user = f"{author['username']}#{author['discriminator']}"
                content = msg['content'].replace('\n', ' ')
                max_content_len = term_width - len(f"[{idx}] [{ts}] {user}: ") - 2
                if len(content) > max_content_len:
                    content = content[:max_content_len-3] + "..."
                if content:
                    print(f"{colorama.Fore.YELLOW}[{idx}] [{ts}]{colorama.Style.RESET_ALL} {colorama.Fore.GREEN}{user}:{colorama.Style.RESET_ALL} {content}")
            except KeyError:
                print(colorama.Fore.RED + "-- Ошибка отображения сообщения --")
    print("\n" * max(0, available_rows - (len(history[start_index:]) if history else 0)))
    print(colorama.Fore.MAGENTA + "-" * term_width)
    print(f"Введите сообщение (или команды):")
    print(f"{colorama.Fore.YELLOW}back{colorama.Style.RESET_ALL} - к каналам, {colorama.Fore.YELLOW}exit{colorama.Style.RESET_ALL} - выход")
    print(f"{colorama.Fore.YELLOW}delete <номер>{colorama.Style.RESET_ALL} - удалить, {colorama.Fore.YELLOW}edit <номер> <текст>{colorama.Style.RESET_ALL} - редактировать")
    print(colorama.Fore.MAGENTA + "-" * term_width, end="")

def add_new_account(tokens_dict):
    term_width = get_terminal_width()
    new_token = None
    new_username = None
    while not new_username:
        clear_screen()
        print_centered_text("--- Добавление нового аккаунта ---", term_width, colorama.Fore.MAGENTA + colorama.Style.BRIGHT)
        print("\n" * 2)
        try:
            prompt_padding = max(0, (term_width - 25) // 2)
            print(" " * prompt_padding, end="")
            token_input = input(colorama.Fore.YELLOW + "Введите новый Discord токен: " + colorama.Fore.WHITE).strip()

            if not token_input:
                print_centered_text("Токен не может быть пустым.", term_width, colorama.Fore.RED)
                time.sleep(1)
                continue
            if token_input.lower() == 'cancel':
                return None

            print_centered_text("Проверка токена...", term_width, colorama.Fore.CYAN)
            new_username = validate_token(token_input)

            if new_username:
                if new_username in tokens_dict:
                    print_centered_text(f"Аккаунт {new_username} уже существует.", term_width, colorama.Fore.YELLOW)
                    time.sleep(2)
                    return None
                else:
                    new_token = token_input
                    tokens_dict[new_username] = new_token
                    print_centered_text(f"Аккаунт {new_username} успешно добавлен!", term_width, colorama.Fore.GREEN)
                    time.sleep(1.5)
                    save_tokens(tokens_dict)
                    return new_token
            else:
                print_centered_text("Введенный токен недействителен или произошла ошибка.", term_width, colorama.Fore.RED)
                print_centered_text("(Введите 'cancel' для отмены добавления)", term_width, colorama.Fore.YELLOW)
                time.sleep(2.5)

        except KeyboardInterrupt:
            print_centered_text("\nОтмена добавления.", term_width, colorama.Fore.YELLOW)
            return None
    return None

def main():
    colorama.init(autoreset=True)
    term_width = get_terminal_width()
    current_token = None
    current_username = None
    loaded_tokens = load_tokens()

    while current_token is None:
        clear_screen()
        print_centered_text("---Klycord---", term_width, colorama.Fore.MAGENTA + colorama.Style.BRIGHT)
        print("\n" * 1)

        account_options = []
        if loaded_tokens:
            print_centered_text("Выберите аккаунт:", term_width, colorama.Fore.WHITE)
            account_options.extend([(f"👤 {username}", token) for username, token in loaded_tokens.items()])
            account_options.sort()
            print()
        else:
            print_centered_text("Нет сохраненных аккаунтов.", term_width, colorama.Fore.YELLOW)

        account_options.append(("[ Добавить новый аккаунт ]", "add_new"))
        account_options.append(("[ Выход ]", "exit"))

        selected_option = display_interactive_menu("Управление аккаунтами", account_options)

        if selected_option == "exit" or selected_option is None:
            colorama.deinit()
            sys.exit()
        elif selected_option == "add_new":
            added_token = add_new_account(loaded_tokens)
            if added_token:
                current_token = added_token
                loaded_tokens = load_tokens()
        elif selected_option in loaded_tokens.values():
            current_token = selected_option
        else:
            print_centered_text("Некорректный выбор.", term_width, colorama.Fore.RED)
            time.sleep(1)
            continue

        if current_token and not current_username:
            for name, tk in loaded_tokens.items():
                if tk == current_token:
                    current_username = name
                    break
            if current_username:
                print_centered_text(f"Выбран аккаунт: {current_username}", term_width, colorama.Fore.GREEN)
                time.sleep(1.5)

    while True:
        clear_screen()
        print_centered_text("Получение списка серверов...", term_width, colorama.Fore.CYAN)
        guilds = get_server_list(current_token)
        if guilds is None:
            print_centered_text("Не удалось получить серверы.", term_width, colorama.Fore.RED)
            time.sleep(2)
            break
        if not guilds:
            print_centered_text("Нет серверов.", term_width, colorama.Fore.YELLOW)

        server_options = [(f"{g['name']}", g['id']) for g in guilds]
        server_options.sort(key=lambda x: x[0].lower())
        server_options.append(("[ Личные сообщения ]", "dm"))
        server_options.append(("-- Сменить аккаунт / Выход --", "back"))
        selected_option = display_interactive_menu("Выберите сервер или ЛС", server_options)

        if selected_option == "back" or selected_option == "exit" or selected_option is None:
            current_token = None
            current_username = None
            main()
            return

        if selected_option == "dm":
            clear_screen()
            print_centered_text("Получение личных сообщений...", term_width, colorama.Fore.CYAN)
            dm_channels = get_dm_channels(current_token)
            if dm_channels is None:
                print_centered_text("Не удалось получить ЛС.", term_width, colorama.Fore.RED)
                time.sleep(2)
                continue
            if not dm_channels:
                print_centered_text("Нет личных сообщений.", term_width, colorama.Fore.YELLOW)
                time.sleep(2)
                continue

            dm_options = []
            for dm in dm_channels:
                if dm['type'] == 1:
                    recipient = dm['recipients'][0]
                    dm_name = f"{recipient['username']}#{recipient['discriminator']}"
                    dm_options.append((f"💬 {dm_name}", dm['id']))
                elif dm['type'] == 3:
                    dm_name = dm.get('name', "Групповой чат")
                    dm_options.append((f"👥 {dm_name}", dm['id']))
            dm_options.sort(key=lambda x: x[0].lower())
            dm_options.append(("-- Назад к серверам --", "back"))
            selected_dm_id = display_interactive_menu("Выберите ЛС (Esc - Назад)", dm_options)

            if selected_dm_id == "back" or selected_dm_id is None:
                continue
            if selected_dm_id == "exit":
                colorama.deinit()
                sys.exit()

            selected_dm_name = next((opt[0] for opt in dm_options if opt[1] == selected_dm_id), "?")
            selected_dm_name = selected_dm_name[2:]

            clear_screen()
            print_centered_text(f"Загрузка ЛС {selected_dm_name}...", term_width, colorama.Fore.CYAN)
            message_history = get_message_history(current_token, selected_dm_id) or []

            while True:
                display_chat_view("ЛС", selected_dm_name, message_history, is_dm=True)
                try:
                    message_input = input(colorama.Fore.WHITE + "> ").strip()
                    if not message_input:
                        continue
                    parts = message_input.split(maxsplit=2)

                    if parts[0].lower() == "delete" and len(parts) >= 2:
                        try:
                            msg_index = int(parts[1])
                            available_rows = get_terminal_size()[1] - 8
                            start_index = max(0, len(message_history) - available_rows)
                            if msg_index < start_index or msg_index >= len(message_history):
                                print(colorama.Fore.RED + "Неверный номер сообщения.")
                                time.sleep(1)
                                continue
                            message_id = message_history[msg_index]['id']
                            if delete_message(current_token, selected_dm_id, message_id):
                                time.sleep(0.5)
                                new_history = get_message_history(current_token, selected_dm_id)
                                if new_history is not None:
                                    message_history = new_history
                        except ValueError:
                            print(colorama.Fore.RED + "Номер сообщения должен быть числом.")
                            time.sleep(1)
                        continue

                    if parts[0].lower() == "edit" and len(parts) >= 3:
                        try:
                            msg_index = int(parts[1])
                            new_content = parts[2]
                            available_rows = get_terminal_size()[1] - 8
                            start_index = max(0, len(message_history) - available_rows)
                            if msg_index < start_index or msg_index >= len(message_history):
                                print(colorama.Fore.RED + "Неверный номер сообщения.")
                                time.sleep(1)
                                continue
                            message_id = message_history[msg_index]['id']
                            if edit_message(current_token, selected_dm_id, message_id, new_content):
                                time.sleep(0.5)
                                new_history = get_message_history(current_token, selected_dm_id)
                                if new_history is not None:
                                    message_history = new_history
                        except ValueError:
                            print(colorama.Fore.RED + "Номер сообщения должен быть числом.")
                            time.sleep(1)
                        continue

                    if message_input.lower() == "back":
                        break
                    if message_input.lower() == "exit":
                        clear_screen()
                        colorama.deinit()
                        sys.exit()

                    if send_message(current_token, selected_dm_id, message_input):
                        time.sleep(0.5)
                        new_history = get_message_history(current_token, selected_dm_id)
                        if new_history is not None:
                            message_history = new_history
                except KeyboardInterrupt:
                    clear_screen()
                    colorama.deinit()
                    sys.exit()
            continue

        selected_server_id = selected_option
        selected_server_name = next((g['name'] for g in guilds if g['id'] == selected_server_id), "?")

        while True:
            clear_screen()
            print_centered_text(f"Сервер: {selected_server_name}", term_width, colorama.Fore.GREEN)
            print_centered_text("Получение каналов...", term_width, colorama.Fore.CYAN)
            channels = get_channel_list(current_token, selected_server_id)
            if channels is None:
                print_centered_text("Не удалось получить каналы.", term_width, colorama.Fore.RED)
                time.sleep(2)
                break
            if not channels:
                print_centered_text("Нет текст. каналов.", term_width, colorama.Fore.YELLOW)
                time.sleep(2)
                break

            channel_options = [(f"# {c['name']}", c['id']) for c in channels]
            channel_options.sort(key=lambda x: x[0].lower())
            channel_options.append(("-- Назад к серверам --", "back"))
            selected_channel_id = display_interactive_menu("Выберите канал (Esc - Назад)", channel_options)

            if selected_channel_id == "back" or selected_channel_id is None:
                break
            if selected_channel_id == "exit":
                colorama.deinit()
                sys.exit()

            selected_channel_name = next((c['name'] for c in channels if c['id'] == selected_channel_id), "?")

            clear_screen()
            print_centered_text(f"Загрузка истории #{selected_channel_name}...", term_width, colorama.Fore.CYAN)
            message_history = get_message_history(current_token, selected_channel_id) or []

            while True:
                display_chat_view(selected_server_name, selected_channel_name, message_history)
                try:
                    message_input = input(colorama.Fore.WHITE + "> ").strip()
                    if not message_input:
                        continue
                    parts = message_input.split(maxsplit=2)

                    if parts[0].lower() == "delete" and len(parts) >= 2:
                        try:
                            msg_index = int(parts[1])
                            available_rows = get_terminal_size()[1] - 8
                            start_index = max(0, len(message_history) - available_rows)
                            if msg_index < start_index or msg_index >= len(message_history):
                                print(colorama.Fore.RED + "Неверный номер сообщения.")
                                time.sleep(1)
                                continue
                            message_id = message_history[msg_index]['id']
                            if delete_message(current_token, selected_channel_id, message_id):
                                time.sleep(0.5)
                                new_history = get_message_history(current_token, selected_channel_id)
                                if new_history is not None:
                                    message_history = new_history
                        except ValueError:
                            print(colorama.Fore.RED + "Номер сообщения должен быть числом.")
                            time.sleep(1)
                        continue

                    if parts[0].lower() == "edit" and len(parts) >= 3:
                        try:
                            msg_index = int(parts[1])
                            new_content = parts[2]
                            available_rows = get_terminal_size()[1] - 8
                            start_index = max(0, len(message_history) - available_rows)
                            if msg_index < start_index or msg_index >= len(message_history):
                                print(colorama.Fore.RED + "Неверный номер сообщения.")
                                time.sleep(1)
                                continue
                            message_id = message_history[msg_index]['id']
                            if edit_message(current_token, selected_channel_id, message_id, new_content):
                                time.sleep(0.5)
                                new_history = get_message_history(current_token, selected_channel_id)
                                if new_history is not None:
                                    message_history = new_history
                        except ValueError:
                            print(colorama.Fore.RED + "Номер сообщения должен быть числом.")
                            time.sleep(1)
                        continue

                    if message_input.lower() == "back":
                        break
                    if message_input.lower() == "exit":
                        clear_screen()
                        colorama.deinit()
                        sys.exit()

                    if send_message(current_token, selected_channel_id, message_input):
                        time.sleep(0.5)
                        new_history = get_message_history(current_token, selected_channel_id)
                        if new_history is not None:
                            message_history = new_history
                except KeyboardInterrupt:
                    clear_screen()
                    colorama.deinit()
                    sys.exit()

    clear_screen()
    print_centered_text("Работа завершена.", term_width, colorama.Fore.MAGENTA)
    colorama.deinit()

if __name__ == "__main__":
    main()
    
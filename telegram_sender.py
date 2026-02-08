#!/usr/bin/env python3
"""
Telegram Sender
Отправляет текст из файла в приватный Telegram-чат через бота.
"""

import requests
import sys
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class TelegramBot:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, text: str, parse_mode: Optional[str] = None) -> bool:
        """Отправляет сообщение в Telegram"""
        url = f"{self.api_url}/sendMessage"
        
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                print(f"Сообщение успешно отправлено в чат {self.chat_id}")
                return True
            else:
                error_msg = result.get('description', 'Неизвестная ошибка')
                print(f"Ошибка Telegram API: {error_msg}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети: {e}")
            return False
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return False
    
    def split_long_message(self, text: str, max_length: int = 4096) -> list:
        """Разделяет длинное сообщение на части"""
        if len(text) <= max_length:
            return [text]
        
        messages = []
        current_message = ""
        
        lines = text.split('\n')
        for line in lines:
            if len(current_message + line + '\n') <= max_length:
                current_message += line + '\n'
            else:
                if current_message:
                    messages.append(current_message.rstrip())
                current_message = line + '\n'
        
        if current_message:
            messages.append(current_message.rstrip())
        
        return messages
    
    def send_long_text(self, text: str) -> bool:
        """Отправляет длинный текст, разделяя на части"""
        messages = self.split_long_message(text)
        
        for i, message in enumerate(messages, 1):
            if len(messages) > 1:
                message = f"Часть {i}/{len(messages)}\n\n{message}"
            
            if not self.send_message(message):
                return False
        
        return True
    
    def read_text_file(self, file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """Читает текстовый файл"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except FileNotFoundError:
            print(f"Файл не найден: {file_path}")
            return None
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    return f.read()
            except Exception as e:
                print(f"Ошибка кодировки файла: {e}")
                return None
        except Exception as e:
            print(f"Ошибка чтения файла: {e}")
            return None


def get_env_var(var_name: str) -> Optional[str]:
    """Получает переменную окружения"""
    value = os.getenv(var_name)
    if not value:
        print(f"Переменная окружения {var_name} не установлена")
    return value


def print_setup_instructions():
    """Выводит инструкции по настройке"""
    print("""
Инструкции по настройке Telegram-бота:

1. Создайте бота в Telegram:
   - Найдите @BotFather в Telegram
   - Отправьте команду /newbot
   - Следуйте инструкциям для создания бота
   - Сохраните токен бота (выглядит как: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)

2. Получите ваш chat_id:
   - Найдите @userinfobot в Telegram
   - Отправьте ему любое сообщение
   - Он покажет ваш ID (число)

3. Установите переменные окружения:
   export TELEGRAM_BOT_TOKEN="ваш_токен"
   export TELEGRAM_CHAT_ID="ваш_chat_id"

Или создайте файл .env:
TELEGRAM_BOT_TOKEN=ваш_токен
TELEGRAM_CHAT_ID=ваш_chat_id
""")


def main():
    if len(sys.argv) < 2:
        print("Использование: python telegram_sender.py путь_к_файлу.txt")
        print("Или: python telegram_sender.py --help для инструкций по настройке")
        sys.exit(1)
    
    if sys.argv[1] == '--help':
        print_setup_instructions()
        sys.exit(0)
    
    file_path = sys.argv[1]
    
    bot_token = get_env_var('TELEGRAM_BOT_TOKEN')
    chat_id = get_env_var('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("Ошибка: необходимо установить TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID")
        print("Запустите python telegram_sender.py --help для инструкций")
        sys.exit(1)
    
    bot = TelegramBot(bot_token, chat_id)
    
    print(f"Читаем файл: {file_path}")
    text = bot.read_text_file(file_path)
    
    if text is None:
        sys.exit(1)
    
    if not text.strip():
        print("Файл пуст или содержит только пробельные символы")
        sys.exit(1)
    
    print(f"Отправляем {len(text)} символов в Telegram...")
    
    if bot.send_long_text(text):
        print("Текст успешно отправлен!")
    else:
        print("Не удалось отправить текст")
        sys.exit(1)


if __name__ == "__main__":
    main()
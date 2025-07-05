from typing import Optional
from datetime import datetime
import asyncio
from os.path import exists
import os
from functools import wraps
from dotmap import DotMap


class Logger:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    WHITE = '\033[97m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def __init__(self,
                 lvl_logging: Optional[str] = "info",
                 exit_path: Optional[str] = '/log/file.log',
                 color_lvl: Optional[bool] = False,
                 write_all: Optional[bool] = True):
        """
        Инициализирует экземпляр логгера.

        Параметры:
            lvl_logging: Уровень детализации логирования (info/error/warning/debug)
            exit_path: Относительный путь к файлу логов
            color_lvl: Включить цветное оформление консольного вывода
            write_all: Глобальный флаг активации логирования
        """
        self.lvl_logging = lvl_logging
        self.exit_path = os.getcwd() + exit_path
        self.color_lvl = color_lvl
        self.write_all = write_all

        if not self.get_path():
            return None

    def __schame_msg__(self, type_msg: str, data: dict) -> str:
        """
        Генерирует форматированное сообщение для лога.

        Параметры:
            type_msg: Тип сообщения (info/error/warning/debug)
            data: Словарь с данными для логирования:
                - method: HTTP-метод или название функции
                - url: URL-адрес или имя функции
                - msg: Дополнительное сообщение
                - status_code: Код статуса

        Возвращает:
            tuple: Кортеж из двух строк:
                [0] - сообщение для консоли (с цветовыми кодами)
                [1] - сообщение для файла (без форматирования)

        Генерирует:
            None: Если передан неподдерживаемый type_msg
        """
        if type_msg not in ['info', 'error', 'warning', 'debug']:
            return None
        match type_msg:
            case 'info':
                return (f"{self.OKGREEN}" + "INFO" + self.ENDC +
                        ":     " +
                        datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M") +
                        " ||" +
                        self.WHITE + self.BOLD + f"{data['method']:^8}" + self.ENDC +
                        "||" +
                        self.WHITE + self.BOLD + f"{data['url']:^25}" + self.ENDC +
                        "||" +
                        self.OKGREEN + f" {data['status_code']:^5} ||" + f" {data['msg']}" + self.ENDC,

                        "INFO" + ":     " +
                        datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M") +
                        " ||" + f"{data['method']:^8}" + "||" +
                        f"{data['url']:^25}" + f"|| {data['status_code']:^5} ||" + f" {data['msg']}\n")
            case "error":
                return (self.FAIL + "ERROR" + self.ENDC +
                        ":    " +
                        datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M") +
                        " ||" +
                        self.WHITE + self.BOLD + f"{data['method']:^8}" + self.ENDC +
                        "||" +
                        self.WHITE + self.BOLD + f"{data['url']:^25}" + self.ENDC +
                        "||" +
                        self.FAIL + f" {data['status_code']:^5} ||" + f" {data['msg']}" + self.ENDC,

                        "ERROR:    " +
                        datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M") +
                        " ||" + f"{data['method']:^8}" + "||" +
                        f"{data['url']:^25}" + f"|| {data['status_code']:^5} ||" + f" {data['msg']}\n")
            case "warning":
                pass

    def get_path(self) -> bool:
        """
        Проверяет существование файла логов и создает его при необходимости.

        Возвращает:
            bool: True - файл существует/создан, 
                  False - ошибка создания

        Действия:
            - Создает директорию для логов, если не существует
            - Инициализирует файл лога с заголовком
        """
        if not exists(self.exit_path):
            try:
                os.makedirs(os.path.dirname(self.exit_path), exist_ok=True)
                with open(self.exit_path, 'w', encoding="UTF-8") as file:
                    file.write("DEBUG" + ":    " +
                               datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M") +
                               " || " +
                               "Создан файл логгирования" + "\n")

            except Exception as e:
                pass
        return True

    async def write_file(self, msg: str):
        """
        Асинхронно записывает сообщение в файл логов.

        Параметры:
            msg: Строка сообщения для записи

        Обрабатывает:
            FileNotFoundError: Выводит предупреждение в консоль
        """
        try:
            with open(self.exit_path, 'a', encoding='UTF-8') as file:
                file.write(msg)
        except FileNotFoundError:
            print("File Not Found")

    def write(self,
              write_console: bool = True,
              write_file: bool = True):
        """
        Декоратор для автоматического логирования вызовов функций.

        Параметры:
            write_console: Разрешить вывод в консоль
            write_file: Разрешить запись в файл

        Возвращает:
            decorator: Декоратор для обработки функций

        Логируемые данные:
            - Для FastAPI-endpoint: 
                method = HTTP-метод, 
                url = путь запроса,
                msg = тело ответа,
                status_code = код статуса ответа
            - Для обычных функций:
                method = "-", 
                url = имя функции,
                msg = "OK",
                status_code = 200 или из возвращаемого словаря

        Особенности:
            - Автоматически определяет тип сообщения (info/error) по статус-коду
            - Игнорирует логирование если write_all=False
            - Поддерживает асинхронную запись в файл
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)

                if isinstance(result, dict) or result is None:
                    status_code = 200
                    if result is not None:
                        status_code = result.get("status_code", '-')
                    result = DotMap(result)
                    result.status_code = status_code

                if not self.write_all:
                    return result

                method = "-"
                url = func.__name__
                msg = "OK"
                type_msg = "info"

                if 'request' in kwargs:
                    method = kwargs['request'].method
                    url = kwargs['request'].url.path
                    msg = result.body

                if result.status_code != 200:
                    type_msg = "error"

                message = self.__schame_msg__(type_msg, {"method": method,
                                                         "url": url,
                                                         "msg": msg,
                                                         'status_code': result.status_code})

                if write_console:
                    print(message[0])

                if write_file:
                    asyncio.run(self.write_file(message[1]))

                return result
            return wrapper
        return decorator
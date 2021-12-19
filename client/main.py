import asyncio
import json
import mimetypes
import re
import sys
import threading
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QVBoxLayout,
    QTextBrowser,
    QLabel,
    QFileDialog,
)
from aiohttp import (
    ClientSession,
    ClientConnectionError,
    FormData,
)

from database.core import init_db_connection
from database.models import Message


class Application:
    def __init__(self):

        self.host = ""
        self.port = ""
        self.username = ""
        self.ws = None
        self.drawn_messages = []

        self.app = QApplication([])  # Главное приложение
        self.connect_to_server_window = QWidget()  # Окно подключения к серверу
        self.connect_to_server_window.setWindowTitle(
            "Подключение к серверу"
        )  # Меняем заголовок окна

        self.connect_to_server_layout = (
            QHBoxLayout()
        )  # Виждеты в окне будут расположены горизонтально

        self.host_line_edit = QLineEdit()  # Текстовое поле для хоста
        self.port_line_edit = QLineEdit()  # Текстовое поле для порта

        self.host_line_edit.setPlaceholderText("Хост")  # Меняем подсказку к полям
        self.port_line_edit.setPlaceholderText("Порт")

        self.connect_push_button = QPushButton(
            "Подключиться"
        )  # Кнопка подключения к серверу
        self.connect_push_button.clicked.connect(  # Вешаем обработчик нажатия
            lambda: asyncio.get_event_loop().run_until_complete(  # Функция асинхронная,
                self.handle_connect_button()  # поэтому такая страшная конструкция
            )
        )

        # Размещаем виджеты на экране подключения к серверу
        self.connect_to_server_layout.addWidget(self.host_line_edit)
        self.connect_to_server_layout.addWidget(self.port_line_edit)
        self.connect_to_server_layout.addWidget(self.connect_push_button)

        self.connect_to_server_window.setLayout(self.connect_to_server_layout)
        self.connect_to_server_window.show()

        # Всё то же самое, но для экрана авторизации / регистрации
        self.authorize_window = QWidget()
        self.authorize_layout = QHBoxLayout()

        self.authorize_window.setWindowTitle("Авторизация")

        self.username_line_edit = QLineEdit()
        self.password_line_edit = QLineEdit()

        self.username_line_edit.setPlaceholderText("Имя пользователя")
        self.password_line_edit.setPlaceholderText("Пароль")

        self.authorize_push_button = QPushButton("Авторизация")
        self.register_push_button = QPushButton("Регистрация")
        self.authorize_push_button.clicked.connect(
            lambda: asyncio.get_event_loop().run_until_complete(
                self.handle_authorize_button()
            )
        )
        self.register_push_button.clicked.connect(self.handle_register_button)

        self.authorize_layout.addWidget(self.username_line_edit)
        self.authorize_layout.addWidget(self.password_line_edit)
        self.authorize_layout.addWidget(self.authorize_push_button)
        self.authorize_layout.addWidget(self.register_push_button)

        self.authorize_window.setLayout(self.authorize_layout)

        self.chat_window = QWidget()
        self.chat_layout = QVBoxLayout()

        self.chat_username_label = QLabel()

        self.chat_clear_history_button = QPushButton()
        self.chat_clear_history_button.setText("Очистить историю")
        self.chat_clear_history_button.clicked.connect(
            lambda: asyncio.get_event_loop().run_until_complete(self.clear_history())
        )

        self.chat_history_text_area = QTextBrowser()
        self.chat_history_text_area.textChanged.connect(
            self.chat_history_text_area_scroll_to_bottom
        )

        self.chat_input_message = QLineEdit()
        self.chat_input_message.setPlaceholderText("Введите сообщение")

        self.chat_send_message = QPushButton("Отправить")
        self.chat_send_message.clicked.connect(
            lambda: asyncio.get_event_loop().run_until_complete(self.send_message())
        )

        self.chat_send_image = QPushButton("Прикрепить")
        self.chat_send_image.clicked.connect(
            lambda: asyncio.get_event_loop().run_until_complete(self.attach_image())
        )

        self.chat_layout.addWidget(self.chat_username_label)
        self.chat_layout.addWidget(self.chat_clear_history_button)
        self.chat_layout.addWidget(self.chat_history_text_area)
        self.chat_layout.addWidget(self.chat_input_message)
        self.chat_layout.addWidget(self.chat_send_message)
        self.chat_layout.addWidget(self.chat_send_image)

        self.chat_window.setLayout(self.chat_layout)

        # Запускаем приложение
        self.app.exec()

    async def handle_connect_button(self):
        alert = QMessageBox()  # Создаём окошко для ошибки

        if not self.host_line_edit.text():  # Если хост не указан
            alert.setWindowTitle("Ошибка!")
            alert.setText("Хост должен быть указан")

        elif not self.port_line_edit.text():  # Если порт не указан
            alert.setWindowTitle("Ошибка!")
            alert.setText("Порт должен быть указан")

        elif not re.match(  # Если порт не IP-адрес (регулярка взята с https://ihateregex.io)
            r"(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}",
            self.host_line_edit.text(),
        ):
            alert.setWindowTitle("Ошибка!")
            alert.setText("Неверный формат хоста")

        else:  # Валидация данных пройдена
            self.host = self.host_line_edit.text()  # Сохраняем хост и порт
            self.port = self.port_line_edit.text()

            try:
                async with ClientSession() as session:
                    async with session.ws_connect(
                        f"ws://{self.host}:{self.port}"
                    ) as ws:
                        await ws.ping()
            except ClientConnectionError as e:
                alert.setWindowTitle("Ошибка!")
                alert.setText(f"Невозможно подключиться к серверу. Ошибка {e}")
            else:  # Если все хорошо
                alert.setWindowTitle("Успех!")
                alert.setText("Подключение...")
                self.connect_to_server_window.close()  # Закрываем окно подключения к серверу
                self.authorize_window.show()  # Открываем окно авторизации / регистрации

        # Показать месседж
        alert.show()
        alert.exec()

    async def handle_authorize_button(self):
        alert = QMessageBox()  # Создаём окошко для ошибки
        self.username = self.username_line_edit.text()
        async with ClientSession() as session:
            async with session.get(
                f"http://{self.host}:{self.port}/login",
                json={
                    "action": "authorize",
                    "username": self.username_line_edit.text(),
                    "password": self.password_line_edit.text(),
                },
            ) as resp:
                if "error" in await resp.json():
                    alert.setWindowTitle("Ошибка!")
                    alert.setText("Неверный логин/пароль")
                else:  # Если все хорошо
                    alert.setWindowTitle("Успех!")
                    alert.setText("Подключение...")
                    self.authorize_window.close()  # Закрываем окно подключения к серверу
                    self.chat_username_label.setText(self.username)
                    self.chat_window.show()  # Открываем окно авторизации / регистрации
                    thread = threading.Thread(
                        target=asyncio.run, args=(self.start_listening(),)
                    )
                    thread.start()
        alert.exec()
        alert.show()

    def handle_register_button(self):
        pass

    async def send_message(self):
        async with ClientSession() as session:
            await session.get(
                f"http://{self.host}:{self.port}/ws/default",
                json={
                    "action": "send_message",
                    "username": self.username_line_edit.text(),
                    "message": self.chat_input_message.text(),
                    "silent": True,
                },
            )

    async def clear_history(self):
        """Очищает историю для всех пользователей в комнате"""
        self.chat_history_text_area.clear()
        await Message.filter(room_id=1).delete()

    def chat_history_text_area_scroll_to_bottom(self):
        self.chat_history_text_area.verticalScrollBar().setValue(
            self.chat_history_text_area.verticalScrollBar().maximum()
        )

    async def attach_image(self):
        file_name = QFileDialog().getOpenFileName(
            caption="Прикрепить изображение",
            filter="Изображение JPEG (*.jpeg);;Изображение JPG (*.jpg);;Изображение PNG (*.png)",
        )[0]

        async with ClientSession() as session:
            data = FormData()
            data.add_field(
                "file",
                open(file_name, "rb"),
                filename=Path(file_name).name,
                content_type=mimetypes.guess_type(file_name)[0],
            )
            data.add_field(
                "payload_json",
                json.dumps(
                    {
                        "action": "send_message",
                        "username": self.username,
                        "attachment": "image",
                    }
                ),
            )
            await session.post(
                f"http://{self.host}:{self.port}/ws/default",
                data=data,
            )

    async def start_listening(self):
        """Раз в 0.3 секунды обновляет сообщения в истории"""
        while True:
            messages = await Message.filter(room_id=1).prefetch_related("user")
            for msg in messages:
                if msg not in self.drawn_messages:
                    self.drawn_messages.append(msg)
                    if msg.user.username == self.username:
                        username = "Вы"
                    else:
                        username = msg.user.username
                    content = f"\n[{username}]: {msg.text if msg.text else ''}"
                    self.chat_history_text_area.insertPlainText(content)
            await asyncio.sleep(0.3)


def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


if __name__ == "__main__":  # Запускаем приложение
    sys._excepthook = sys.excepthook
    sys.excepthook = exception_hook
    asyncio.get_event_loop().run_until_complete(init_db_connection())
    Application()

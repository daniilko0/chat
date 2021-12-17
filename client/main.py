import asyncio
import re
import sys

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QVBoxLayout,
    QTextBrowser,
)
from aiohttp import (
    ClientSession,
    ClientConnectionError,
)


class Application:
    def __init__(self):

        self.host = ""
        self.port = ""
        self.username = ""
        self.ws = None

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

        self.chat_history_text_area = QTextBrowser()

        self.chat_input_message = QLineEdit()
        self.chat_input_message.setPlaceholderText("Введите сообщение")

        self.chat_send_message = QPushButton("Отправить")
        self.chat_send_message.clicked.connect(
            lambda: asyncio.get_event_loop().run_until_complete(self.send_message())
        )

        self.chat_layout.addWidget(self.chat_history_text_area)
        self.chat_layout.addWidget(self.chat_input_message)
        self.chat_layout.addWidget(self.chat_send_message)

        self.chat_window.setLayout(self.chat_layout)

        # Запускаем приложение
        self.app.exec()

    async def handle_connect_button(self):
        alert = QMessageBox()  # Создаём окошко для ошибки

        if not self.host_line_edit.text():  # Если хост не указан
            alert.setWindowTitle("Ошибка!")
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Хост должен быть указан")

        elif not self.port_line_edit.text():  # Если порт не указан
            alert.setWindowTitle("Ошибка!")
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Порт должен быть указан")

        elif not re.match(  # Если порт не IP-адрес (регулярка взята с https://ihateregex.io)
            r"(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}",
            self.host_line_edit.text(),
        ):
            alert.setWindowTitle("Ошибка!")
            alert.setIcon(QMessageBox.Critical)
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
                alert.setIcon(QMessageBox.Critical)
                alert.setText(f"Невозможно подключиться к серверу. Ошибка {e}")
            else:  # Если все хорошо
                alert.setWindowTitle("Успех!")
                alert.setIcon(QMessageBox.Information)
                alert.setText("Подключение...")
                self.connect_to_server_window.close()  # Закрываем окно подключения к серверу
                self.authorize_window.show()  # Открываем окно авторизации / регистрации

        # Показать месседж
        alert.show()
        alert.exec()

    async def handle_authorize_button(self):
        alert = QMessageBox()  # Создаём окошко для ошибки
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
                    alert.setIcon(QMessageBox.Critical)
                    alert.setText("Неверный логин/пароль")
                else:  # Если все хорошо
                    alert.setWindowTitle("Успех!")
                    alert.setIcon(QMessageBox.Information)
                    alert.setText("Подключение...")
                    self.authorize_window.close()  # Закрываем окно подключения к серверу
                    self.chat_window.show()  # Открываем окно авторизации / регистрации
        alert.exec()
        alert.show()

    def handle_register_button(self):
        pass

    # async def subscribe_to_events(self, websocket: ClientWebSocketResponse):
    #     async for event in websocket:
    #         print("new event: ", end="")
    #         if isinstance(event, WSMessage):
    #             if event.type == WSMsgType.text:
    #                 event_json = event.json()
    #                 print(event_json)
    #                 if (
    #                     event_json.get("action") == "authorized"
    #                 ):  # Если пришло событие об авторизации
    #                     alert = QMessageBox()  # Создаём месседж
    #                     if not event_json.get("success"):  # Если ошибка
    #                         alert.setText("Ошибка!")
    #                         alert.setIcon(QMessageBox.Critical)
    #                         alert.setWindowTitle("Ошибка авторизации")
    #                         alert.show()  # Показываем месседж
    #                         alert.exec()
    #                     else:  # Если успешно
    #                         alert.setText("Успех!")
    #                         alert.setIcon(QMessageBox.Information)
    #                         alert.setWindowTitle("Успешная авторизация")
    #                         alert.show()  # Показываем месседж
    #                         alert.exec()
    #                         self.username = self.username_line_edit.text()
    #                         self.authorize_window.close()
    #                         self.chat_window.show()
    #
    #                 if event_json.get("action") == "chat_message":
    #                     print("new_message")
    #                     self.chat_history_text_area.setHtml(
    #                         self.chat_history_text_area.toHtml()
    #                         + "\n"
    #                         + f">>> <b>{event_json.get('username')}</b>: {event_json.get('message')}"
    #                     )
    #
    #                 if event_json.get("action") == "join":
    #                     if event_json.get("user") != "User":
    #                         print("new_user")
    #                         self.chat_history_text_area.setHtml(
    #                             f"{self.chat_history_text_area.toHtml()}<b>{event_json.get('user')}</b> connected!\n"
    #                         )

    async def send_message(self):
        await self.ws.send_json(  # Отправляем на сервер введенные логин и пароль
            {
                "action": "send_message",
                "username": self.username_line_edit.text(),
                "message": self.chat_input_message.text(),
            },
        )
        # read_message_task = asyncio.create_task(self.subscribe_to_events(ws))
        #
        # done, pending = await asyncio.wait(
        #     [read_message_task],
        #     return_when=asyncio.FIRST_COMPLETED,
        # )
        #
        # if not ws.closed:
        #     await ws.close()
        #
        # for task in pending:
        #     task.cancel()


def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


if __name__ == "__main__":  # Запускаем приложение
    sys._excepthook = sys.excepthook
    sys.excepthook = exception_hook
    Application()

import asyncio
import re

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)
from aiohttp import (
    ClientSession,
    WSServerHandshakeError,
    ClientWebSocketResponse,
    WSMessage,
    WSMsgType,
    ClientConnectionError,
)


class Application:
    def __init__(self):

        self.host = ""
        self.port = ""

        self.app = QApplication([])
        self.connect_to_server_window = QWidget()
        self.connect_to_server_window.setWindowTitle("Подключение к серверу")

        self.connect_to_server_layout = QHBoxLayout()

        self.host_line_edit = QLineEdit()
        self.port_line_edit = QLineEdit()

        self.host_line_edit.setPlaceholderText("Хост")
        self.port_line_edit.setPlaceholderText("Порт")

        self.connect_push_button = QPushButton("Подключиться")
        self.connect_push_button.clicked.connect(
            lambda: asyncio.get_event_loop().run_until_complete(
                self.handle_connect_button()
            )
        )

        self.connect_to_server_layout.addWidget(self.host_line_edit)
        self.connect_to_server_layout.addWidget(self.port_line_edit)
        self.connect_to_server_layout.addWidget(self.connect_push_button)

        self.connect_to_server_window.setLayout(self.connect_to_server_layout)
        self.connect_to_server_window.show()

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

        self.app.exec()

    async def handle_connect_button(self):
        alert = QMessageBox()

        if not self.host_line_edit.text():
            alert.setWindowTitle("Ошибка!")
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Хост должен быть указан")

        elif not self.port_line_edit.text():
            alert.setWindowTitle("Ошибка!")
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Порт должен быть указан")

        elif not re.match(
            r"(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}",
            self.host_line_edit.text(),
        ):
            alert.setWindowTitle("Ошибка!")
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Неверный формат хоста")

        else:

            self.host = self.host_line_edit.text()
            self.port = self.port_line_edit.text()

            async with ClientSession() as session:
                try:
                    async with session.ws_connect(
                        f"ws://{self.host}:{self.port}/", ssl=False
                    ) as ws:
                        await ws.ping()
                except (WSServerHandshakeError, ClientConnectionError):
                    alert.setWindowTitle("Ошибка!")
                    alert.setIcon(QMessageBox.Critical)
                    alert.setText("Невозможно подключиться к серверу")
                else:
                    alert.setWindowTitle("Успех!")
                    alert.setIcon(QMessageBox.Information)
                    alert.setText("Подключение...")

                    self.connect_to_server_window.close()
                    self.authorize_window.show()

        alert.show()
        alert.exec()

    async def handle_authorize_button(self):
        async with ClientSession() as session:
            try:
                async with session.ws_connect(
                    f"ws://{self.host}:{self.port}/", ssl=False
                ) as ws:
                    await ws.send_json(
                        {
                            "action": "authorize",
                            "username": self.username_line_edit.text(),
                            "password": self.password_line_edit.text(),
                        },
                    )
                    read_events_task = await asyncio.create_task(
                        self.subscribe_to_events(ws)
                    )

                    done, pending = await asyncio.wait(
                        [read_events_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    if not ws.closed:
                        await ws.close()

                    for task in pending:
                        task.cancel()

            except WSServerHandshakeError:
                pass

    def handle_register_button(self):
        pass

    @staticmethod
    async def subscribe_to_events(websocket: ClientWebSocketResponse):
        async for event in websocket:
            if isinstance(event, WSMessage):
                if event.type == WSMsgType.text:
                    event_json = event.json()

                    if event_json.get("action") == "authorized":
                        alert = QMessageBox()
                        if event_json.get("success"):
                            alert.setText("Успех!")
                            alert.setIcon(QMessageBox.Information)
                            alert.setWindowTitle("Успешная авторизация")
                        else:
                            alert.setText("Ошибка!")
                            alert.setIcon(QMessageBox.Critical)
                            alert.setWindowTitle("Ошибка авторизации")
                        alert.show()
                        alert.exec()


if __name__ == "__main__":
    Application()

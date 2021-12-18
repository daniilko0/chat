# Chat
Asynchronous client-server chat with GUI. Supports text messages, voice messages and pictures

## Running
1. Clone repo with `git clone https://github.com/dadyarri/chat`
2. Go to the project's folder `cd chat`
3. Make sure you have poetry and Python 3.9+ installed (https://python-poetry.org/)
4. Run `poetry install` to create virtual environment and install dependencies
5. Run server with `poetry run python server/main.py`. It will be run on 127.0.0.1:8080
6. Run client with `poetry run python client/main.py`
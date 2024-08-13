import socket
import flet as ft
import threading
import json
import key
import app_open
import subprocess

def main(page: ft.Page):
    # テキストコンポーネントを作成
    message_box = ft.Text(
        value="",
        width=500,
        height=300,
    )
    page.add(message_box)

    # メッセージを表示するための関数
    def update_message_box(message: str):
        message_box.value += f"{message}\n"
        page.update()

    # サーバーのクラス
    class BlockingServerBase:
        def __init__(self, timeout: int = 60, buffer: int = 1024):
            self.__socket = None
            self.__timeout = timeout
            self.__buffer = buffer
            self.message_queue = []
            self.gui_update_event = threading.Event()

        def __del__(self):
            self.close()

        def close(self) -> None:
            if self.__socket:
                try:
                    self.__socket.shutdown(socket.SHUT_RDWR)
                    self.__socket.close()
                except Exception as e:
                    print(f"Error closing socket: {e}")

        def start(self, address, family: int, typ: int, proto: int) -> None:
            self.__socket = socket.socket(family, typ, proto)
            self.__socket.settimeout(self.__timeout)
            self.__socket.bind(address)
            self.__socket.listen(1)
            print(f"Server started on {address}")

            while True:
                try:
                    conn, addr = self.__socket.accept()
                    print(f"Connection from {addr}")
                    self.handle_client(conn)
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    break
            self.close()

        def handle_client(self, conn: socket.socket) -> None:
            with conn:
                while True:
                    try:
                        message_recv = conn.recv(self.__buffer).decode('utf-8')
                        if not message_recv:
                            break
                        print(f"Received message: {message_recv}")
                        self.message_queue.append(message_recv)
                        self.gui_update_event.set()
                        update_message_box(message_recv)
                        print(message_recv)
                        # message_recvを改行文字で分割してリストに格納
                        message_list = message_recv.split('\n')
                        print(message_list)
                        # リストの最後を取得
                        message_recv = message_list[-1]
                        try:
                            json_ob = json.loads(message_recv)
                            print(f"JSON object: {json_ob}")
                        except json.JSONDecodeError as json_err:
                            print(f"JSON decode error: {json_err}")
                            print(f"Invalid JSON: {message_recv}")
                            # 必要に応じてエラーメッセージをクライアントに送信することができます。
                            error_message = 'Invalid JSON format'.encode('utf-8')
                            conn.send(error_message)
                            continue

                        # Example of processing the JSON object
                        if 'data' in json_ob:
                            print(f"Data from JSON: {json_ob['data']}")
                            if json_ob['data'] == 'slack':
                                app_open.open_slack()
                                break
                            elif json_ob['data'] == 'copy':
                                key.copy()
                                break
                            elif json_ob['data'] == 'paste':
                                key.paste()
                                break
                        
                        byte = 'ok'.encode('utf-8')
                        conn.send(byte)
                    except ConnectionResetError:
                        print("Connection reset by client")
                        break
                    except BrokenPipeError:
                        print("Broken pipe error")
                        break
                    except Exception as e:
                        print(f"Error handling client: {e}")
                        break

        def respond(self, message: str) -> str:
            update_message_box(message)

    class InetServer(BlockingServerBase):
        def __init__(self, host: str = "192.168.252.44", port: int = 8080) -> None:
            super().__init__(timeout=60, buffer=1024)
            self.server = (host, port)
            self.message_queue = []  # message_queueの初期化
            self.start(self.server, socket.AF_INET, socket.SOCK_STREAM, 0)

    # サーバーを開始
    InetServer()


ft.app(target=main)
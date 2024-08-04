import socket
import flet as ft
import threading

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
            return message

    class InetServer(BlockingServerBase):
        def __init__(self, host: str = "192.168.10.103", port: int = 8080) -> None:
            super().__init__(timeout=60, buffer=1024)
            self.server = (host, port)
            threading.Thread(target=self.start, args=(self.server, socket.AF_INET, socket.SOCK_STREAM, 0), daemon=True).start()

    # サーバーを開始
    server = InetServer()

    # メッセージを更新するためのスレッド
    def update_gui():
        while True:
            server.gui_update_event.wait()
            while server.message_queue:
                message = server.message_queue.pop(0)
                update_message_box(message)
            server.gui_update_event.clear()

    threading.Thread(target=update_gui, daemon=True).start()

ft.app(target=main)
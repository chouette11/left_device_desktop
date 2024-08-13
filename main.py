import socket
import threading
import json
from pystray import Icon, MenuItem, Menu
from PIL import Image
import time

class BlockingServerBase:
    def __init__(self, timeout: int = 60, buffer: int = 1024):
        self.__socket = None
        self.__timeout = timeout
        self.__buffer = buffer
        self.message_queue = []
        self.gui_update_event = threading.Event()
        self.running = True

    def __del__(self):
        self.close()

    def close(self) -> None:
        if self.__socket:
            try:
                self.__socket.shutdown(socket.SHUT_RDWR)
                self.__socket.close()
            except (AttributeError, OSError) as e:
                print(f"Error closing socket: {e}")

    def start(self, address, family: int, typ: int, proto: int) -> None:
        self.__socket = socket.socket(family, typ, proto)
        self.__socket.settimeout(self.__timeout)
        try:
            self.__socket.bind(address)
            self.__socket.listen(1)
            print(f"Server started on {address}")

            while self.running:
                try:
                    conn, addr = self.__socket.accept()
                    print(f"Connection from {addr}")
                    self.handle_client(conn)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    break
        except OSError as e:
            print(f"Socket error: {e}")
        finally:
            self.close()

    def handle_client(self, conn: socket.socket) -> None:
        with conn:
            while self.running:
                try:
                    message_recv = conn.recv(self.__buffer).decode('utf-8')
                    if not message_recv:
                        break
                    self.message_queue.append(message_recv)
                    # メッセージを処理
                    message_list = message_recv.split('\n')
                    message_recv = message_list[-1]
                    print(f"Received message: {message_recv}")
                    try:
                        json_ob = json.loads(message_recv)
                        print(f"JSON object: {json_ob}")
                    except json.JSONDecodeError as json_err:
                        print(f"JSON decode error: {json_err}")
                        print(f"Invalid JSON: {message_recv}")
                        error_message = 'Invalid JSON format'.encode('utf-8')
                        conn.send(error_message)
                        continue

                    if 'data' in json_ob:
                        print(f"Data from JSON: {json_ob['data']}")
                        if json_ob['data'] == 'exit':
                            print("Client requested exit")
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
        print(message)  # Example of how to use respond method

class InetServer(BlockingServerBase):
    def __init__(self, host: str = "192.168.10.7", port: int = 8080) -> None:
        super().__init__(timeout=60, buffer=1024)
        self.server = (host, port)
        self.message_queue = []  # message_queueの初期化
        threading.Thread(target=self.start, args=(self.server, socket.AF_INET, socket.SOCK_STREAM, 0), daemon=True).start()

class TaskTray:
    def __init__(self, image):
        self.status = False
        # アイコンの画像
        self.image = Image.open(image)
        # 右クリックで表示されるメニュー
        self.menu = Menu(
            MenuItem('Exit', self.stop_program),
        )
        self.icon = Icon(name='nameTray', title='titleTray', icon=self.image, menu=self.menu)

    def stop_program(self, icon, item):
        self.status = False
        self.icon.stop()

    def run_schedule(self):
        # 5秒ごとにタスクを実行する
        while self.status:
            print('タスクを実行しました。')
            time.sleep(5)

    def run_program(self):
        # サーバーを起動
        self.server = InetServer()
        self.status = True
        threading.Thread(target=self.run_schedule, daemon=True).start()
        self.icon.run()

if __name__ == '__main__':
    system_tray = TaskTray(image="sample.png")
    system_tray.run_program()
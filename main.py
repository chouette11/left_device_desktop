import socket, threading, json, time, sys, os, key, app_open, qrcode, io, base64
from pystray import Icon, MenuItem, Menu
from PIL import Image
import flet as ft


class BlockingServerBase:
    def __init__(self, timeout: int = 60, buffer: int = 1024):
        self._socket = None  # ソケットを保持する変数
        self._timeout = timeout  # タイムアウト設定
        self._buffer = buffer  # バッファサイズ設定
        self.message_queue = []
        self.gui_update_event = threading.Event()
        self.running = True

    def __del__(self):
        self.close()

    def close(self) -> None:
        """サーバーソケットを閉じる"""
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
                self._socket.close()
            except (AttributeError, OSError) as e:
                print(f"Error closing socket: {e}")

    def start(self, address, family: int, typ: int, proto: int) -> None:
        """サーバーを開始する"""
        self._socket = socket.socket(family, typ, proto)  # ソケットを作成
        self._socket.settimeout(self._timeout)  # タイムアウトを設定
        try:
            self._socket.bind(address)  # ソケットをアドレスにバインド
            self._socket.listen(1)  # クライアントからの接続を待つ
            print(f"Server started on {address}")

            while self.running:
                try:
                    conn, addr = (
                        self._socket.accept()
                    )  # クライアントからの接続を受け入れ
                    print(f"Connection from {addr}")
                    self.handle_client(conn)  # クライアントの処理を行う
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
        """クライアントからのメッセージを処理する"""
        with conn:
            while self.running:
                try:
                    message_recv = conn.recv(self._buffer).decode("utf-8")
                    if not message_recv:
                        break
                    self.message_queue.append(message_recv)
                    print(f"Received message: {message_recv}")

                    try:
                        json_ob = json.loads(message_recv)
                        print(f"JSON object: {json_ob}")
                    except json.JSONDecodeError as json_err:
                        print(f"JSON decode error: {json_err}")
                        error_message = "Invalid JSON format".encode("utf-8")
                        conn.send(error_message)
                        continue

                    if "data" in json_ob:
                        if json_ob["data"] == "slack":
                            app_open.open_slack()
                            break
                        elif json_ob["data"] == "copy":
                            key.copy()
                            break
                        elif json_ob["data"] == "paste":
                            key.paste()
                            break

                    conn.send("ok".encode("utf-8"))
                except (ConnectionResetError, BrokenPipeError) as e:
                    print(f"Connection error: {e}")
                    break


class InetServer(BlockingServerBase):
    def __init__(self, host: str = None, port: int = 8080) -> None:
        super().__init__(timeout=60, buffer=1024)  # 親クラスの初期化を最初に呼び出す

        # ローカルIPアドレスを取得
        host = host or self.get_local_ip()
        self.server = (host, port)

        # サーバーを新しいスレッドで開始
        threading.Thread(
            target=self.start,
            args=(self.server, socket.AF_INET, socket.SOCK_STREAM, 0),
            daemon=True,
        ).start()

        # QRコードを生成
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(host)
        qr.make(fit=True)
        self.qr_image = qr.make_image(fill_color="black", back_color="white")

    def get_local_ip(self):
        """ローカルIPアドレスを取得する"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # GoogleのDNSサーバーに接続しているかのように振る舞い、ローカルIPを取得
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception as e:
            print(f"Failed to get local IP address: {e}")
            ip = "127.0.0.1"  # 取得できなかった場合はループバックアドレスを使用
        finally:
            s.close()
        return ip

    def get_qr_image(self):
        return self.qr_image  # 生成したQRコード画像を返す


class TaskTray:
    def __init__(self, image, server: InetServer):
        self.status = False
        self.server = server  # サーバーインスタンスを保持
        # アイコンの画像を読み込む
        self.image = Image.open(image)
        # 右クリックで表示されるメニューを作成
        self.menu = Menu(
            MenuItem("Exit", self.stop_program),
            MenuItem("Setting", self.setting),
        )
        self.icon = Icon(
            name="nameTray", title="titleTray", icon=self.image, menu=self.menu
        )

    def stop_program(self):
        self.status = False
        self.icon.stop()

    def setting(self):
        def main(page: ft.Page):
            page.title = "Settings"
            page.window.width = 400
            page.window.height = 500

            page.update()
            page.window.center()

            # QRコード画像をPILからバイトデータに変換
            qr_image = self.server.get_qr_image()
            with io.BytesIO() as buffer:
                qr_image.save(buffer, format="PNG")
                qr_image_bytes = buffer.getvalue()

            qr_image_base64 = base64.b64encode(qr_image_bytes).decode("utf-8")

            page.add(
                ft.Column(
                    [
                        ft.Text("Settings", size=25),
                        ft.Text("スマートフォンでこちらを読み取ってください", size=16),
                        ft.Image(src_base64=qr_image_base64),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            )

        ft.app(target=main)

    def run_schedule(self):
        # 5秒ごとにタスクを実行する
        while self.status:
            print("タスクを実行しました。")
            time.sleep(5)

    def run_program(self):
        self.status = True
        threading.Thread(target=self.run_schedule, daemon=True).start()
        self.icon.run()


def resource_path(relative_path):
    """リソースファイルのパスを返す"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    icon_path = resource_path("sample.icns")
    server = InetServer()  # InetServer インスタンスを作成
    system_tray = TaskTray(
        image=icon_path, server=server
    )  # タスクトレイのインスタンスを作成
    system_tray.run_program()  # プログラムを実行

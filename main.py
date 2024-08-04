import flet as ft
from flet import Page


def main(page: Page):
    page.title = "Flet Server"
    page.update()

    def handle_request(event):
        data = event.data
        print(f"Received data: {data}")
        page.send("response", {"status": "success"})

    page.on_message = handle_request


ft.app(target=main, view=ft.WEB_BROWSER, port=8080)

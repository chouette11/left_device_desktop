import pyautogui

def open_spotlight(e):
    pyautogui.hotkey('command', 'space')
    pyautogui.typewrite('TextEdit')
    pyautogui.press('enter')
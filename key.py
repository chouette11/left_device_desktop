import pyautogui

def open_spotlight():
    pyautogui.hotkey('command', 'space')
    pyautogui.typewrite('TextEdit')
    pyautogui.press('enter')

def copy():
    pyautogui.hotkey('command', 'c')

def paste():
    pyautogui.hotkey('command', 'v')

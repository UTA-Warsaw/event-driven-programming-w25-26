from pynput import keyboard


def on_press(key):
    try:
        print(f"Key pressed: {key.char}")
    except AttributeError:
        print(f"Special key pressed: {key}")


with keyboard.Listener(on_press=on_press) as listener:
    listener.join()

from pynput import keyboard

def on_press(key):
    try:
        # If it's a normal character key, get its ASCII value
        ascii_value = ord(key.char)
        print(f"Key pressed: {key.char} | ASCII: {ascii_value}")
    except AttributeError:
        # Special keys (like space, esc, shift) have their own enum
        print(f"Special key pressed: {key} | No ASCII value")

    # Stop after one key press
    return False

# Listen for a single key press
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
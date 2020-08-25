from threading import Thread
from threading import Timer
from pynput import keyboard
from pynput import mouse
import time

'''Start a daemon responsible for pasting login and password from the
        clipboard to the input fields when user press double click in the user field'''
# Listen to mouse event
# Access the clipboard or a memory area where login and password are stored
#
DOUBLE_CLICK = 0.35


class TypewriteThread(Thread):
    def __init__(self, text, timeout=30, *args, **kwargs):
        super(TypewriteThread, self).__init__(*args, **kwargs)
        self.text = text
        self.control_key = None
        self.start_time = 0
        self.timeout = timeout

    def run(self):
        mouseListener = mouse.Listener(on_click=self.on_click)
        t = Timer(self.timeout, mouseListener.stop)
        t.start()
        mouseListener.start()
        mouseListener.join()

    def on_click(self, x, y, button, pressed):
        if not self.start_time and pressed:
            self.start_time = time.time()
        elif self.start_time and pressed:
            click = time.time()
            elapsed_time = click - self.start_time
            if elapsed_time < DOUBLE_CLICK:
                writer = keyboard.Controller()
                # for word in data:
                for c in self.text:
                    writer.press(c)
                    writer.release(c)
                return False
            else:
                self.start_time = click


if __name__ == '__main__':
    pass

    data = 'user\tpassword'
    daemon = TypewriteThread(text=data, timeout=10)
    daemon.start()
    daemon.join() # The Main thread wait for daemon stop before process further
    print('All done!')

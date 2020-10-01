from threading import Thread, Timer
from pynput import keyboard, mouse
import time

'''


'''
# Listen to mouse event
# Access the clipboard or a memory area where login and password are stored
#
DOUBLE_CLICK = 0.35

class TypewriteThread(Thread):
    """Thread responsible for input a text into a field.

    The text is inserted when the user press double click on an input field.
    """

    only_one = []

    def __init__(self, text, timeout=30, *args, **kwargs):
        """Thread responsible for input a text into a field.

        The text is inserted when the user press double click on an input field.

        Args:

        text (str): input text

        timeout (int, optional): After timeout seconds the thread is stopped.
        Defaults to 30 secs.
        """
        super(TypewriteThread, self).__init__()
        self.text = text
        self.timeout = timeout
        self.start_time = 0
        self._stop_thread = False

    def run(self):
        for twt in self.only_one:
            twt.interrupt()
        del self.only_one[:]
        self.only_one.append(self)
        # Save obj creation time
        self.writer = keyboard.Controller()
        self.mouseListener = mouse.Listener(on_click=self.on_click)
        self.mouseListener.name = f'{id(self)}-mouselistener'
        # Set a timeout
        t = Timer(self.timeout, self.interrupt)
        t.name = f'{id(self)}-timeout'
        t.start()
        # Mouselistener thread
        self.mouseListener.start()
        while True:
            time.sleep(0.2)
            if self._stop_thread:
                break

    def on_click(self, x, y, button, pressed):
        if not self.start_time and pressed:
            self.start_time = time.time()
        elif self.start_time and pressed:
            click = time.time()
            elapsed_time = click - self.start_time
            if elapsed_time < DOUBLE_CLICK:
                for c in self.text:
                    self.writer.press(c)
                    self.writer.release(c)
                # Interrupt
                self._stop_thread = True
                return False
            else:
                # Store the first mouse click
                self.start_time = click

    def interrupt(self):
        self._stop_thread = True
        if self.mouseListener.is_alive():
            self.mouseListener.stop()
        

if __name__ == '__main__':
    pass

    data = 'user\tpassword'
    daemon = TypewriteThread(text=data, timeout=10)
    daemon.name = 'typewrite'
    daemon.start()
    # The Main thread wait for daemon stop before process further
    print(daemon.getName())
    time.sleep(2)
    daemon.interrupt()
    print(daemon)
    # daemon.join()
    print('All done!')

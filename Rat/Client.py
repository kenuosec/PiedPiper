import socket
import sys
import tkinter
import rsa
import win32api
import win32con


class Client:
    """
    A socket client class that sets a client by ip and port and initialize its connection to the server
    """

    def __init__(self, ip, port, type):  # type - piper or rat
        """
        Initiate client object
        :param ip: server ip
        :param port: server port
        """
        super().__init__()
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip, self.port = ip, port
        self.rsa_public_key, self.rsa_private_key = rsa.newkeys(1024)
        self.client_id = None
        self.client_type = type
        self.isClientInitiated = False
        self.symmetric_encryption = None
        self.size_left = 0
        self.overall_size = 0

    def sockets_error(self, error):
        win32api.MessageBox(0, 'Sockets met an obstacle: ' + error, "Connection Error", win32con.MB_OK)
        sys.exit()

    def set_id(self, id):
        """
        sets a new id
        :param id: desired id
        """
        self.id = id

    def recv_large_data(self):
        """
        this functions handles recieving a large amount of data (like images)
        so it recieves the required size of data and divides it into several times
        :param my_socket: the socket it receives through
        :return: the data received
        """
        self.overall_size = int(self.recv(1024).decode())
        self.size_left = self.overall_size
        self.send("got".encode())
        print("sent to server that i got the size")

        data = b''
        c = 0
        while self.size_left != 0:
            packet_data = self.my_socket.recv(1024)
            packet_len = len(packet_data)
            data += packet_data
            self.size_left -= packet_len
            c += 1


        print("received data in " + str(c) + " seperate times.")
        #print("the data is: ", data)
        self.size_left = 0
        self.overall_size = 0
        return self.symmetric_encryption.decrypt(data)

    def init_client(self):
        """
        try to connect the client to the server
        """
        connected = False
        while not connected:
            try:
                self.my_socket.connect((self.ip, self.port))
                connected = True
            except socket.error as exc:
                if self.client_type == 'Piper':
                    response = win32api.MessageBox(0, "Trying to reach the Pied Piper Server...", "Notification", win32con.MB_RETRYCANCEL)
                    if response == win32con.IDCLOSE or response == win32con.IDCANCEL:
                        exit()
                print("My socket was closed successfully.")
                print("Caught exception socket.error : %s" % exc)


        print("I connected to ip-" + self.ip + " And to port-" + str(self.port))
        self.my_socket.send(self.client_type.encode())
        self.id = self.my_socket.recv(1024).decode()
        if id is not None:
            self.my_socket.send('1'.encode())
        else:
            self.my_socket.send('0'.encode())

        if self.client_type == 'Piper':
            pass


        elif self.client_type == 'Rat':
            pass

        self.isClientInitiated = True

        # self.server_public_rsa_key = pickle.loads(self.my_socket.recv(1024))
        # encrypted_key = rsa.encrypt(self.symmetric_encryption.get_key(), self.server_public_rsa_key)
        # self.my_socket.send(encrypted_key)

    def send(self, bytes, encrypt=True):
        """
        sends data, encrypted or not
        :param bytes: bytes to send
        :param encrypt: boolean to say if to encrypt or not
        :return:
        """
        try:
            if encrypt:
                self.my_socket.send(self.symmetric_encryption.encrypt(bytes))
            else:
                self.my_socket.send(bytes)
        except Exception as e:
            self.sockets_error(str(e))

    def recv(self, amount, decrypt=True):
        """
        recvs data, then, decrypt it or not
        :param amount: amount of bytes to recv
        :param encrypt: boolean to say if to encrypt or not
        :return: the data (decrypted or not)
        """
        try:
            if decrypt:
                data = self.my_socket.recv(amount)
                return self.symmetric_encryption.decrypt(data)
            else:
                return self.my_socket.recv(amount)
        except Exception as e:
            self.sockets_error(str(e))

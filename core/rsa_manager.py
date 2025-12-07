from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import os

class RSAManager:
    @staticmethod
    def generate_keys(save_dir="assets"):
        """Generates a 2048-bit RSA Key Pair."""
        if not os.path.exists(save_dir): os.makedirs(save_dir)
        
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        
        priv_path = os.path.join(save_dir, "my_private_key.pem")
        pub_path = os.path.join(save_dir, "my_public_key.pem")
        
        with open(priv_path, "wb") as f: f.write(private_key)
        with open(pub_path, "wb") as f: f.write(public_key)
            
        return pub_path, priv_path

    @staticmethod
    def encrypt_session_key(aes_key_str, public_key_path):
        """Encrypts the AES session key using the Receiver's Public Key."""
        with open(public_key_path, "rb") as f:
            public_key = RSA.import_key(f.read())
            
        cipher_rsa = PKCS1_OAEP.new(public_key)
        # RSA can only encrypt small data, which is perfect for a 32-byte hex key
        enc_session_key = cipher_rsa.encrypt(aes_key_str.encode('utf-8'))
        
        return enc_session_key.hex()

    @staticmethod
    def decrypt_session_key(enc_hex_key, private_key_path):
        """Decrypts the AES session key using your Private Key."""
        with open(private_key_path, "rb") as f:
            private_key = RSA.import_key(f.read())
            
        cipher_rsa = PKCS1_OAEP.new(private_key)
        
        try:
            enc_bytes = bytes.fromhex(enc_hex_key)
            session_key = cipher_rsa.decrypt(enc_bytes)
            return session_key.decode('utf-8')
        except Exception as e:
            raise ValueError("RSA Decryption Failed: Invalid Private Key or Corrupted Data.")
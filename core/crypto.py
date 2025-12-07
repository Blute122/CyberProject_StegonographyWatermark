from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
import hashlib

class CryptoHandler:
    def __init__(self, key=None):
        # AES-256 requires a 32-byte key
        if key:
             # Ensure key is 32 bytes (hash it to be safe)
            self.key = hashlib.sha256(key.encode()).digest()
        else:
            self.key = get_random_bytes(32)

    def encrypt(self, plain_text):
        """Encrypts string using AES-CBC and returns a Base64 string."""
        # 1. Generate a random Initialization Vector (IV)
        iv = get_random_bytes(16)
        
        # 2. Initialize Cipher
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        
        # 3. Pad the data to be a multiple of 16 bytes
        padded_data = pad(plain_text.encode('utf-8'), AES.block_size)
        
        # 4. Encrypt
        encrypted_bytes = cipher.encrypt(padded_data)
        
        # 5. Combine IV + Encrypted Data (we need the IV to decrypt later)
        combined_data = iv + encrypted_bytes
        
        # 6. Return as Base64 string so it fits into our LSB text hider
        return base64.b64encode(combined_data).decode('utf-8')

    def decrypt(self, enc_string):
        """Decrypts a Base64 AES-CBC string."""
        try:
            # 1. Decode from Base64 back to bytes
            enc_data = base64.b64decode(enc_string)
            
            # 2. Extract the IV (first 16 bytes) and the actual ciphertext
            iv = enc_data[:16]
            ciphertext = enc_data[16:]
            
            # 3. Initialize Cipher with the extracted IV
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            
            # 4. Decrypt and Unpad
            decrypted_padded = cipher.decrypt(ciphertext)
            decrypted_data = unpad(decrypted_padded, AES.block_size)
            
            return decrypted_data.decode('utf-8')
        except (ValueError, KeyError) as e:
            return f"Decryption Error: {str(e)} (Key might be wrong or data corrupted)"
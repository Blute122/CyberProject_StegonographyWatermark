import cv2
import numpy as np

class DCTSteganography:
    def __init__(self):
        self.block_size = 8
        self.delimiter = "$$$"
        self.Q = 25 
        self.threshold = 10 

    def to_binary(self, data):
        if isinstance(data, str):
            return ''.join([format(ord(i), "08b") for i in data])
        elif isinstance(data, bytes):
            return ''.join([format(i, "08b") for i in data])
        return ""

    def get_adaptive_map(self, img):
        """
        Generates the 'Map' of busy blocks.
        Updated with STRONGER DILATION for Q=18 stability.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. Stability Fix: Strong Masking
        gray_stable = gray & 0xF0 
        blurred = cv2.GaussianBlur(gray_stable, (5, 5), 0) 
        
        # 2. Edge Detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # 3. INCREASED DILATION: Makes the map more generous
        # This prevents the "No Data Found" error even with lower Q.
        kernel = np.ones((5,5), np.uint8)
        texture_map = cv2.dilate(edges, kernel, iterations=2) 
        
        return texture_map

    def dct_embed(self, image_path, message, output_path):
        img = cv2.imread(image_path)
        if img is None: raise ValueError("Image not found")
        
        h, w, _ = img.shape
        h = h - (h % 8)
        w = w - (w % 8)
        img = img[:h, :w]
        
        texture_map = self.get_adaptive_map(img)
        
        (B, G, R) = cv2.split(img)
        B_float = np.float32(B)
        
        message += self.delimiter
        binary_msg = self.to_binary(message)
        msg_len = len(binary_msg)
        msg_index = 0
        
        print(f"[*] Adaptive Encoding (Q={self.Q})...")

        for r in range(0, h, 8):
            for c in range(0, w, 8):
                if msg_index >= msg_len: break
                
                # Check Map
                map_block = texture_map[r:r+8, c:c+8]
                if np.mean(map_block) < self.threshold:
                    continue
                
                block = B_float[r:r+8, c:c+8]
                dct_block = cv2.dct(block)
                
                coeff = dct_block[4, 4]
                bit = int(binary_msg[msg_index])
                
                # Quantization Embedding
                if bit == 0:
                    new_coeff = round(coeff / self.Q) * self.Q
                else:
                    new_coeff = (round((coeff - (self.Q / 2)) / self.Q) * self.Q) + (self.Q / 2)
                
                dct_block[4, 4] = float(new_coeff)
                
                idct_block = cv2.idct(dct_block)
                B_float[r:r+8, c:c+8] = idct_block
                
                msg_index += 1
                
        if msg_index < msg_len:
            print(f"[!] WARNING: Message truncated! Image texture capacity too low.")
            
        B_out = np.uint8(np.clip(B_float, 0, 255))
        merged = cv2.merge((B_out, G, R))
        cv2.imwrite(output_path, merged)
        print(f"[+] Saved Adaptive DCT Stego-Image to {output_path}")

    def dct_extract(self, stego_path):
        img = cv2.imread(stego_path)
        if img is None: raise ValueError("Image not found")
        
        h, w, _ = img.shape
        h = h - (h % 8)
        w = w - (w % 8)
        img = img[:h, :w]
        
        # Re-Calculate Map (Should be identical to Sender now due to MSB masking)
        texture_map = self.get_adaptive_map(img)
        
        (B, _, _) = cv2.split(img)
        B_float = np.float32(B)
        
        extracted_bits = ""
        
        for r in range(0, h, 8):
            for c in range(0, w, 8):
                map_block = texture_map[r:r+8, c:c+8]
                if np.mean(map_block) < self.threshold:
                    continue
                
                block = B_float[r:r+8, c:c+8]
                dct_block = cv2.dct(block)
                
                coeff = dct_block[4, 4]
                remainder = coeff % self.Q
                
                if remainder > (self.Q / 4) and remainder < (3 * self.Q / 4):
                    extracted_bits += '1'
                else:
                    extracted_bits += '0'
        
        message = ""
        for i in range(0, len(extracted_bits), 8):
            byte = extracted_bits[i:i+8]
            if len(byte) < 8: break
            try:
                char = chr(int(byte, 2))
                message += char
            except:
                continue
            if message.endswith(self.delimiter):
                return message[:-len(self.delimiter)]
                
        return "No hidden message found."
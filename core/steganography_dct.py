import cv2
import numpy as np

class DCTSteganography:
    def __init__(self):
        self.block_size = 8
        self.delimiter = "$$$"
        self.Q = 25  # Standard Quality for Images
        self.threshold = 10 

    def to_binary(self, data):
        if isinstance(data, str):
            return ''.join([format(ord(i), "08b") for i in data])
        elif isinstance(data, bytes):
            return ''.join([format(i, "08b") for i in data])
        return ""

    def get_adaptive_map(self, img):
        """Generates the 'Map' of busy blocks (AI Brain)."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_stable = gray & 0xF0 
        blurred = cv2.GaussianBlur(gray_stable, (5, 5), 0) 
        edges = cv2.Canny(blurred, 50, 150)
        kernel = np.ones((5,5), np.uint8)
        texture_map = cv2.dilate(edges, kernel, iterations=2)
        return texture_map

    def dct_embed(self, image_path, message, output_path, use_adaptive=True):
        """
        Embeds message. 
        - If use_adaptive=True (Images): Uses AI Texture Analyzer.
        - If use_adaptive=False (Video): Skips AI, uses sequential embedding.
        """
        img = cv2.imread(image_path)
        if img is None: raise ValueError("Image not found")
        
        h, w, _ = img.shape
        h = h - (h % 8)
        w = w - (w % 8)
        img = img[:h, :w]
        
        # --- MODE CHECK ---
        if use_adaptive:
            # IMAGE MODE: Calculate Map
            texture_map = self.get_adaptive_map(img)
        
        (B, G, R) = cv2.split(img)
        B_float = np.float32(B)
        
        message += self.delimiter
        binary_msg = self.to_binary(message)
        msg_len = len(binary_msg)
        msg_index = 0
        
        # Log which brain we are using
        mode_str = "Adaptive AI" if use_adaptive else "Sequential"
        print(f"[*] DCT Encoding Mode: {mode_str} (Q={self.Q})")

        for r in range(0, h, 8):
            for c in range(0, w, 8):
                if msg_index >= msg_len: break
                
                # --- AI CHECK ---
                if use_adaptive:
                    # Only check the map if we are in Image Mode
                    map_block = texture_map[r:r+8, c:c+8]
                    if np.mean(map_block) < self.threshold:
                        continue # Skip smooth blocks
                
                # Standard Embedding Logic...
                block = B_float[r:r+8, c:c+8]
                dct_block = cv2.dct(block)
                
                coeff = dct_block[4, 4]
                bit = int(binary_msg[msg_index])
                
                if bit == 0:
                    new_coeff = round(coeff / self.Q) * self.Q
                else:
                    new_coeff = (round((coeff - (self.Q / 2)) / self.Q) * self.Q) + (self.Q / 2)
                
                dct_block[4, 4] = float(new_coeff)
                idct_block = cv2.idct(dct_block)
                B_float[r:r+8, c:c+8] = idct_block
                
                msg_index += 1
            if msg_index >= msg_len: break
            
        B_out = np.uint8(np.clip(B_float, 0, 255))
        merged = cv2.merge((B_out, G, R))
        cv2.imwrite(output_path, merged)

    def dct_extract(self, stego_path, use_adaptive=True):
        """
        Extracts message.
        - Must match the mode used during embedding!
        """
        img = cv2.imread(stego_path)
        if img is None: raise ValueError("Image not found")
        
        h, w, _ = img.shape
        h = h - (h % 8)
        w = w - (w % 8)
        img = img[:h, :w]
        
        if use_adaptive:
            texture_map = self.get_adaptive_map(img)
        
        (B, _, _) = cv2.split(img)
        B_float = np.float32(B)
        
        extracted_bits = ""
        
        for r in range(0, h, 8):
            for c in range(0, w, 8):
                # --- AI CHECK ---
                if use_adaptive:
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
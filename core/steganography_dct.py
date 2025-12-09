import cv2
import numpy as np

class DCTSteganography:
    def __init__(self):
        self.block_size = 8
        self.delimiter = "$$$"
        self.Q = 50  # Increased Strength for Robustness
        self.threshold = 20 
        self.repeats = 5  # <--- NEW: Error Correction (Must be odd number)

    def to_binary(self, data):
        if isinstance(data, str):
            return ''.join([format(ord(i), "08b") for i in data])
        elif isinstance(data, bytes):
            return ''.join([format(i, "08b") for i in data])
        return ""

    def get_adaptive_map(self, img):
        """Generates the 'Map' of busy blocks using Green channel."""
        green_channel = img[:, :, 1]
        blurred = cv2.GaussianBlur(green_channel, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        kernel = np.ones((5,5), np.uint8)
        texture_map = cv2.dilate(edges, kernel, iterations=2)
        return texture_map

    def dct_embed(self, image_path, message, output_path, use_adaptive=True):
        img = cv2.imread(image_path)
        if img is None: raise ValueError("Image not found")
        
        h, w, _ = img.shape
        h = h - (h % 8)
        w = w - (w % 8)
        img = img[:h, :w]
        
        if use_adaptive:
            texture_map = self.get_adaptive_map(img)
        
        (B, G, R) = cv2.split(img)
        B_float = np.float32(B)
        
        message += self.delimiter
        binary_msg = self.to_binary(message)
        
        # --- APPLY REDUNDANCY ---
        # "1" -> "11111", "0" -> "00000"
        redundant_msg = ""
        for bit in binary_msg:
            redundant_msg += bit * self.repeats
            
        msg_len = len(redundant_msg)
        msg_index = 0
        
        print(f"[*] DCT Embed Mode: {'Adaptive AI' if use_adaptive else 'Robust'} | Q={self.Q} | Redundancy={self.repeats}x")

        for r in range(0, h, 8):
            for c in range(0, w, 8):
                if msg_index >= msg_len: break
                
                if use_adaptive:
                    map_block = texture_map[r:r+8, c:c+8]
                    if np.mean(map_block) < self.threshold:
                        continue 
                
                block = B_float[r:r+8, c:c+8]
                dct_block = cv2.dct(block)
                
                # Use Low-Mid Frequency (2,2) for balance
                coeff = dct_block[1,0]
                bit = int(redundant_msg[msg_index])
                
                if bit == 0:
                    new_coeff = round(coeff / self.Q) * self.Q
                else:
                    new_coeff = (round((coeff - (self.Q / 2)) / self.Q) * self.Q) + (self.Q / 2)
                
                dct_block[1,0]=float(new_coeff)
                idct_block = cv2.idct(dct_block)
                B_float[r:r+8, c:c+8] = idct_block
                
                msg_index += 1
            if msg_index >= msg_len: break
            
        B_out = np.uint8(np.clip(B_float, 0, 255))
        merged = cv2.merge((B_out, G, R))
        cv2.imwrite(output_path, merged)

    def dct_extract(self, stego_path, use_adaptive=True):
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
        
        raw_bits = ""
        
        # 1. Extract ALL Raw Bits
        for r in range(0, h, 8):
            for c in range(0, w, 8):
                if use_adaptive:
                    map_block = texture_map[r:r+8, c:c+8]
                    if np.mean(map_block) < self.threshold:
                        continue
                
                block = B_float[r:r+8, c:c+8]
                dct_block = cv2.dct(block)
                coeff = dct_block[1,0]
                
                remainder = coeff % self.Q
                if remainder > (self.Q / 4) and remainder < (3 * self.Q / 4):
                    raw_bits += '1'
                else:
                    raw_bits += '0'
        
        # 2. Majority Vote (Error Correction)
        final_bits = ""
        for i in range(0, len(raw_bits), self.repeats):
            chunk = raw_bits[i:i+self.repeats]
            if len(chunk) < self.repeats: break
            
            # Count 1s
            ones = chunk.count('1')
            if ones > (self.repeats / 2):
                final_bits += '1'
            else:
                final_bits += '0'
        
        # 3. Convert to Text
        message = ""
        for i in range(0, len(final_bits), 8):
            byte = final_bits[i:i+8]
            if len(byte) < 8: break
            try:
                char = chr(int(byte, 2))
                message += char
            except:
                continue
            if message.endswith(self.delimiter):
                return message[:-len(self.delimiter)]
                
        return message[:50] + "..."
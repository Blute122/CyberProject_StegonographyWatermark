import cv2
import pywt
import numpy as np
import hashlib

class WatermarkHandler:
    def __init__(self, watermark_path="assets/watermark.png"):
        self.watermark_path = watermark_path
        self.alpha = 0.2 

    # --- ROBUST LAYER (DWT) ---
    def embed_watermark(self, image_path, output_path):
        """Embeds robust DWT watermark into HH band."""
        print(f"[*] Watermarking image (High Frequency): {image_path}")
        
        img = cv2.imread(image_path)
        if img is None: raise ValueError(f"Image not found: {image_path}")
        
        h, w, _ = img.shape
        # Ensure even dimensions
        h = h if h % 2 == 0 else h - 1
        w = w if w % 2 == 0 else w - 1
        img = img[:h, :w]

        logo = cv2.imread(self.watermark_path, cv2.IMREAD_GRAYSCALE)
        if logo is None: raise ValueError("Watermark logo not found")
        logo = cv2.bitwise_not(logo)
        
        logo = cv2.resize(logo, (w//2, h//2))
        
        (B, G, R) = cv2.split(img)
        img_float = np.float32(B) 
        
        coeffs = pywt.dwt2(img_float, 'haar')
        LL, (LH, HL, HH) = coeffs
        
        # Embed in HH (High Frequency) for invisibility
        watermark_embedding = self.alpha * logo
        HH_new = HH + watermark_embedding 
        
        new_coeffs = (LL, (LH, HL, HH_new))
        img_reconstructed = pywt.idwt2(new_coeffs, 'haar')
        
        img_reconstructed = np.clip(img_reconstructed, 0, 255)
        img_reconstructed = np.uint8(img_reconstructed)
        
        merged_img = cv2.merge((img_reconstructed, G, R))
        cv2.imwrite(output_path, merged_img)
        return output_path

    def extract_watermark(self, watermarked_path, original_path, output_path):
        """Extracts robust watermark."""
        img_wm = cv2.imread(watermarked_path)
        img_orig = cv2.imread(original_path)
        
        if img_wm is None or img_orig is None: raise ValueError("Could not load comparison images")

        h, w, _ = img_wm.shape
        img_orig = img_orig[:h, :w]
        
        (B_wm, _, _) = cv2.split(img_wm)
        (B_orig, _, _) = cv2.split(img_orig)
        
        _, (_, _, HH_wm) = pywt.dwt2(np.float32(B_wm), 'haar')
        _, (_, _, HH_orig) = pywt.dwt2(np.float32(B_orig), 'haar')
        
        extracted = (HH_wm - HH_orig) / self.alpha
        extracted = np.clip(extracted, 0, 255)
        extracted = np.uint8(extracted)
        
        cv2.imwrite(output_path, extracted)

    # --- FRAGILE LAYER (TAMPER DETECTION) ---
    def embed_fragile_seal(self, image_path, output_path):
        """
        Calculates a Hash of the image and hides it in the Last Row.
        Uses 0xFE mask to avoid integer overflow errors.
        """
        print("[*] Applying Fragile Tamper-Seal...")
        img = cv2.imread(image_path)
        if img is None: raise ValueError(f"Image not found: {image_path}")

        h, w, c = img.shape
        
        # 1. Calculate SHA-256 Hash of the image content (excluding last row)
        content_to_hash = img[:-1, :, :].tobytes()
        img_hash = hashlib.sha256(content_to_hash).hexdigest()
        
        # 2. Convert Hash to Binary
        binary_hash = ''.join([format(ord(i), "08b") for i in img_hash])
        
        # 3. Embed into LSB of RED Channel in the LAST ROW
        data_idx = 0
        data_len = len(binary_hash)
        
        for col in range(w):
            if data_idx >= data_len: break
            
            # Get pixel as a standard Python int to avoid overflow warnings
            pixel_val = int(img[h-1, col, 2]) 
            bit = int(binary_hash[data_idx])
            
            # LSB Modification
            if bit == 1:
                pixel_val = pixel_val | 1
            else:
                # FIX: Use 0xFE (254) instead of ~1 (-2) to keep it unsigned
                pixel_val = pixel_val & 0xFE
                
            img[h-1, col, 2] = pixel_val
            data_idx += 1
            
        cv2.imwrite(output_path, img)
        return output_path

    def verify_fragile_seal(self, image_path):
        """Checks if the image has been tampered with."""
        img = cv2.imread(image_path)
        if img is None: return False, "Could not load image."
        
        h, w, c = img.shape
        
        # 1. Extract Hash from Last Row
        extracted_bits = ""
        for col in range(w):
            pixel_val = img[h-1, col, 2] # Red Channel
            extracted_bits += str(pixel_val & 1)
            
            # SHA-256 is 64 hex chars * 8 bits = 512 bits
            if len(extracted_bits) >= 512: break
            
        # Convert bits to string
        extracted_hash = ""
        for i in range(0, len(extracted_bits), 8):
            byte = extracted_bits[i:i+8]
            try:
                extracted_hash += chr(int(byte, 2))
            except:
                break
            
        # 2. Recalculate Hash of current image content
        content_to_hash = img[:-1, :, :].tobytes()
        current_hash = hashlib.sha256(content_to_hash).hexdigest()
        
        print(f"    > Embedded Seal: {extracted_hash[:10]}...")
        print(f"    > Calculated:    {current_hash[:10]}...")
        
        if extracted_hash == current_hash:
            return True, "✅ INTEGRITY CONFIRMED: Image is authentic."
        else:
            return False, "❌ TAMPER DETECTED: Image has been modified!"
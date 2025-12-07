import cv2
import numpy as np
import math

class StegoMetrics:
    @staticmethod
    def calculate_psnr(original_path, stego_path):
        """Calculates Peak Signal-to-Noise Ratio (PSNR). Higher is better."""
        img1 = cv2.imread(original_path)
        img2 = cv2.imread(stego_path)
        
        if img1 is None or img2 is None:
            raise ValueError("One of the images could not be loaded.")

        # --- FIX START: Handle Dimension Mismatch ---
        # DWT sometimes crops 1 pixel to make dimensions even.
        # We must align both images to the smaller size to compare them fairly.
        h1, w1, _ = img1.shape
        h2, w2, _ = img2.shape
        
        h_min = min(h1, h2)
        w_min = min(w1, w2)
        
        # Crop both to the minimum common size
        img1 = img1[:h_min, :w_min]
        img2 = img2[:h_min, :w_min]
        # --- FIX END ---
        
        # Mean Squared Error (MSE)
        mse = np.mean((img1 - img2) ** 2)
        
        if mse == 0:
            return 100  # Images are identical
            
        max_pixel = 255.0
        psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
        return psnr

    @staticmethod
    def simulate_attack(image_path, output_path, attack_type="noise"):
        """Simulates cyber attacks on the image to test watermark robustness."""
        img = cv2.imread(image_path)
        
        if attack_type == "noise":
            print("[!] Simulating Salt & Pepper Noise Attack...")
            row, col, ch = img.shape
            s_vs_p = 0.5
            amount = 0.02
            out = np.copy(img)
            
            # Salt (White)
            num_salt = np.ceil(amount * img.size * s_vs_p)
            coords = [np.random.randint(0, i - 1, int(num_salt)) for i in img.shape]
            out[tuple(coords)] = 255

            # Pepper (Black)
            num_pepper = np.ceil(amount * img.size * (1. - s_vs_p))
            coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in img.shape]
            out[tuple(coords)] = 0
            
            cv2.imwrite(output_path, out)
            
        elif attack_type == "compression":
            print("[!] Simulating JPEG Compression Attack...")
            # Save with low quality (Quality=50)
            cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, 50])
            
        return output_path
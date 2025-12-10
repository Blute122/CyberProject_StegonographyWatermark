import cv2
import shutil
import os
import numpy as np
from core.steganography_dct import DCTSteganography
from core.metrics import StegoMetrics
from core.attacks import AttackSimulator

# --- Reuse helper functions ---
def calculate_ssim(img1_path, img2_path):
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE).astype(np.float64)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE).astype(np.float64)
    h_min = min(img1.shape[0], img2.shape[0])
    w_min = min(img1.shape[1], img2.shape[1])
    img1 = img1[:h_min, :w_min]
    img2 = img2[:h_min, :w_min]
    C1, C2 = 6.5025, 58.5225
    mu1 = cv2.GaussianBlur(img1, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(img2, (11, 11), 1.5)
    mu1_sq, mu2_sq = mu1**2, mu2**2
    mu1_mu2 = mu1 * mu2
    sigma1_sq = cv2.GaussianBlur(img1**2, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(img2**2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(img1 * img2, (11, 11), 1.5) - mu1_mu2
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    return np.mean(ssim_map)

def calculate_ber(original_text, recovered_text):
    def text_to_bin(text): return ''.join(format(ord(c), '08b') for c in text)
    bin_orig = text_to_bin(original_text)
    if not recovered_text or recovered_text == "Extraction Error": return 0.5 
    bin_rec = text_to_bin(recovered_text)
    min_len = min(len(bin_orig), len(bin_rec))
    errors = sum(1 for i in range(min_len) if bin_orig[i] != bin_rec[i])
    errors += abs(len(bin_orig) - len(bin_rec))
    return errors / max(len(bin_orig), len(bin_rec)) if max(len(bin_orig), len(bin_rec)) > 0 else 0.0

class ResearchStego(DCTSteganography):
    def dct_extract_robust(self, stego_path, use_adaptive=True, char_limit=1000):
        try: return self._fast_extract(cv2.imread(stego_path), use_adaptive, char_limit)
        except: return ""

    def _fast_extract(self, img, use_adaptive, char_limit):
        if img is None: return ""
        h, w, _ = img.shape
        h, w = h - (h % 8), w - (w % 8)
        if use_adaptive: texture_map = self.get_adaptive_map(img)
        B_float = np.float32(cv2.split(img)[0])
        bits = ""
        result = ""
        for r in range(0, h, 8):
            for c in range(0, w, 8):
                if use_adaptive and np.mean(texture_map[r:r+8, c:c+8]) < self.threshold: continue
                coeff = cv2.dct(B_float[r:r+8, c:c+8])[4, 4]
                bits += '1' if (self.Q/4) < (coeff % self.Q) < (3*self.Q/4) else '0'
                if len(bits) == 8:
                    try: result += chr(int(bits, 2))
                    except: result += "?"
                    bits = ""
                    if len(result) >= char_limit: return result
        return result

def run_baboon_test():
    stego = ResearchStego()
    secret = "ResearchPayload-" * 50
    image_name = "baboon"
    
    print(f"--- Benchmarking Texture Stress Test: {image_name} ---")
    cover = f"assets/{image_name}.png"
    
    if not os.path.exists(cover):
        print(f"[!] Error: 'assets/{image_name}.png' not found.")
        print("    Please ensure you have downloaded baboon.png into the assets folder.")
        return

    # Embed
    print("[1/3] Embedding Payload...")
    seq_out = f"assets/{image_name}_seq.png"
    adapt_out = f"assets/{image_name}_adapt.png"
    stego.dct_embed(cover, secret, seq_out, use_adaptive=False)
    stego.dct_embed(cover, secret, adapt_out, use_adaptive=True)
    
    # Metrics - FIXED: Added SSIM Calculation
    print("[2/3] Calculating Visual Quality (PSNR & SSIM)...")
    psnr_seq = StegoMetrics.calculate_psnr(cover, seq_out)
    psnr_adapt = StegoMetrics.calculate_psnr(cover, adapt_out)
    
    ssim_seq = calculate_ssim(cover, seq_out)      # <--- Added
    ssim_adapt = calculate_ssim(cover, adapt_out)  # <--- Added
    
    # Attack (JPEG Q=85)
    print("[3/3] Attacking (JPEG Q=85) & Measuring BER...")
    AttackSimulator.apply_jpeg_compression(seq_out, quality=85)
    shutil.move("assets/attacked_compressed.jpg", f"assets/{image_name}_seq_attacked.jpg")
    AttackSimulator.apply_jpeg_compression(adapt_out, quality=85)
    shutil.move("assets/attacked_compressed.jpg", f"assets/{image_name}_adapt_attacked.jpg")
    
    # BER
    rec_seq = stego.dct_extract_robust(f"assets/{image_name}_seq_attacked.jpg", False, len(secret))
    rec_adapt = stego.dct_extract_robust(f"assets/{image_name}_adapt_attacked.jpg", True, len(secret))
    
    ber_seq = calculate_ber(secret, rec_seq)
    ber_adapt = calculate_ber(secret, rec_adapt)
    
    print("\n" + "="*65)
    print(f"{'METRIC':<20} | {'SEQUENTIAL':<15} | {'ADAPTIVE (Ours)':<15}")
    print("="*65)
    print(f"{'PSNR (dB)':<20} | {psnr_seq:<15.2f} | {psnr_adapt:<15.2f}")
    print(f"{'SSIM (0-1)':<20} | {ssim_seq:<15.4f} | {ssim_adapt:<15.4f}") # <--- Added
    print("-" * 65)
    print(f"{'BER (JPEG Attack)':<20} | {ber_seq:<15.4f} | {ber_adapt:<15.4f}")
    print("="*65)

if __name__ == "__main__":
    run_baboon_test()
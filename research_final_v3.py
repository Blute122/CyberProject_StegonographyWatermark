import cv2
import numpy as np
import difflib
import shutil
import math
import os
from core.steganography_dct import DCTSteganography
from core.metrics import StegoMetrics
from core.steganalysis import SteganalysisScanner
from core.attacks import AttackSimulator

# --- METRIC HELPERS ---
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
    def calculate_max_capacity(self, image_path, use_adaptive=True):
        img = cv2.imread(image_path)
        if img is None: return 0
        h, w, _ = img.shape
        h, w = h - (h % 8), w - (w % 8)
        img = img[:h, :w]
        
        if not use_adaptive: return (h // 8) * (w // 8)
        
        texture_map = self.get_adaptive_map(img)
        return sum(1 for r in range(0, h, 8) for c in range(0, w, 8) if np.mean(texture_map[r:r+8, c:c+8]) >= self.threshold)

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

def run_comprehensive_benchmark():
    stego = ResearchStego() 
    cover = "assets/cover_image.png"
    secret = "ResearchPayload-" * 50 
    
    print(f"--- Comprehensive Research Benchmark (JPEG Q=85) ---")
    
    # 1. CAPACITY
    print("[1/4] Calculating Payload Capacity...")
    cap_seq = stego.calculate_max_capacity(cover, False)
    cap_adapt = stego.calculate_max_capacity(cover, True)
    
    # 2. EMBED
    print("[2/4] Embedding & Measuring Quality...")
    stego.dct_embed(cover, secret, "res_seq.png", use_adaptive=False)
    stego.dct_embed(cover, secret, "res_adapt.png", use_adaptive=True)
    
    psnr_seq = StegoMetrics.calculate_psnr(cover, "res_seq.png")
    psnr_adapt = StegoMetrics.calculate_psnr(cover, "res_adapt.png")
    ssim_seq = calculate_ssim(cover, "res_seq.png")
    ssim_adapt = calculate_ssim(cover, "res_adapt.png")
    
    # 3. ATTACK (SWITCHED TO JPEG)
    print("[3/4] Attacking (JPEG Quality=85) & Measuring BER...")
    
    # Apply JPEG Compression
    AttackSimulator.apply_jpeg_compression("res_seq.png", quality=85)
    shutil.move("assets/attacked_compressed.jpg", "attacked_seq.jpg") # Note extension change to .jpg
    
    AttackSimulator.apply_jpeg_compression("res_adapt.png", quality=85)
    shutil.move("assets/attacked_compressed.jpg", "attacked_adapt.jpg")
    
    # Recover
    rec_seq = stego.dct_extract_robust("attacked_seq.jpg", False, len(secret))
    rec_adapt = stego.dct_extract_robust("attacked_adapt.jpg", True, len(secret))
    
    ber_seq = calculate_ber(secret, rec_seq)
    ber_adapt = calculate_ber(secret, rec_adapt)

    # 4. FINAL TABLE
    print("\n" + "="*75)
    print(f"{'METRIC':<25} | {'SEQUENTIAL':<20} | {'ADAPTIVE (Ours)':<20}")
    print("="*75)
    print(f"{'Max Payload (bits)':<25} | {cap_seq:<20} | {cap_adapt:<20}")
    print(f"{'Payload Utilization':<25} | {'100% (Baseline)':<20} | {f'{(cap_adapt/cap_seq)*100:.1f}% (Selective)':<20}")
    print("-" * 75)
    print(f"{'PSNR (dB)':<25} | {f'{psnr_seq:.2f}':<20} | {f'{psnr_adapt:.2f}':<20}")
    print(f"{'SSIM (0-1.0)':<25} | {f'{ssim_seq:.4f}':<20} | {f'{ssim_adapt:.4f}':<20}")
    print("-" * 75)
    print(f"{'BER (JPEG Attack)':<25} | {f'{ber_seq:.4f}':<20} | {f'{ber_adapt:.4f}':<20}")
    print("="*75)
    
    print("\n[Analysis Guide]")
    print(f"* SSIM: Adaptive ({ssim_adapt:.4f}) should be higher.")
    print(f"* BER: Adaptive ({ber_adapt:.4f}) should now be COMPETITIVE or LOWER.")
    print("  (JPEG smooths the image, preserving the Edge Map synchronization!)")

if __name__ == "__main__":
    run_comprehensive_benchmark()
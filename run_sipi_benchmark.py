import os
import cv2
import numpy as np
import urllib.request
import matplotlib.pyplot as plt
import shutil

# Import your existing core modules
# (Assumes this script is placed in the root folder alongside 'core')
from core.steganography_dct import DCTSteganography
from core.metrics import StegoMetrics
from core.attacks import AttackSimulator

# --- CONFIGURATION ---
SIPI_IMAGES = [
    "lena", "baboon", "peppers", "airplane", 
    "fruits", "monarch", "cat", "pool"
]
BASE_URL = "https://homepages.cae.wisc.edu/~ece533/images/{}.png"
ASSET_DIR = "assets_sipi"
RESULTS_DIR = "results_benchmark"
PAYLOAD_STR = "CyberProject_Security_Test_Payload_" * 50  # Robust payload

# --- HELPER: SSIM CALCULATION ---
def calculate_ssim(img1_path, img2_path):
    """Calculates Structural Similarity Index (SSIM) manually."""
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE).astype(np.float64)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE).astype(np.float64)
    
    # Crop to match dimensions if needed
    h_min = min(img1.shape[0], img2.shape[0])
    w_min = min(img1.shape[1], img2.shape[1])
    img1 = img1[:h_min, :w_min]
    img2 = img2[:h_min, :w_min]
    
    # Constants for SSIM
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    
    # Gaussian Blur (simulate window)
    kernel = (11, 11)
    sigma = 1.5
    mu1 = cv2.GaussianBlur(img1, kernel, sigma)
    mu2 = cv2.GaussianBlur(img2, kernel, sigma)
    
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2
    
    sigma1_sq = cv2.GaussianBlur(img1 ** 2, kernel, sigma) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(img2 ** 2, kernel, sigma) - mu2_sq
    sigma12 = cv2.GaussianBlur(img1 * img2, kernel, sigma) - mu1_mu2
    
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
               ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    
    return np.mean(ssim_map)

# --- HELPER: BER CALCULATION ---
def calculate_ber(original_text, recovered_text):
    """Calculates Bit Error Rate (BER). Lower is better."""
    def text_to_bin(text): return ''.join(format(ord(c), '08b') for c in text)
    
    bin_orig = text_to_bin(original_text)
    
    if not recovered_text or recovered_text == "Extraction Error":
        # If extraction failed completely, BER is 0.5 (random guess equivalent) or 1.0
        return 0.5 
        
    bin_rec = text_to_bin(recovered_text)
    
    # Pad or truncate to match lengths
    min_len = min(len(bin_orig), len(bin_rec))
    max_len = max(len(bin_orig), len(bin_rec))
    
    if max_len == 0: return 0.0
    
    # Count bit mismatches
    errors = sum(1 for i in range(min_len) if bin_orig[i] != bin_rec[i])
    errors += abs(len(bin_orig) - len(bin_rec)) # Penalize length mismatch
    
    return errors / max_len

# --- STEP 1: DOWNLOAD DATABASE ---
def setup_environment():
    if not os.path.exists(ASSET_DIR): os.makedirs(ASSET_DIR)
    if not os.path.exists(RESULTS_DIR): os.makedirs(RESULTS_DIR)
    
    print(f"[*] Checking SIPI Image Database in '{ASSET_DIR}'...")
    for name in SIPI_IMAGES:
        path = os.path.join(ASSET_DIR, f"{name}.png")
        if not os.path.exists(path):
            print(f"   Downloading {name}...")
            try:
                urllib.request.urlretrieve(BASE_URL.format(name), path)
            except:
                print(f"   [!] Could not download {name}, skipping.")

# --- STEP 2: RUN BENCHMARK LOOP ---
def run_benchmark():
    stego = DCTSteganography()
    
    # Storage for plotting
    data = {
        "names": [],
        "psnr_seq": [], "psnr_adapt": [],
        "ssim_seq": [], "ssim_adapt": [],
        "ber_seq": [],  "ber_adapt": []
    }
    
    print("\n" + "="*80)
    print(f"{'IMAGE':<15} | {'METHOD':<12} | {'PSNR (dB)':<10} | {'SSIM':<8} | {'BER (Attack)':<12}")
    print("="*80)
    
    for name in SIPI_IMAGES:
        img_path = os.path.join(ASSET_DIR, f"{name}.png")
        if not os.path.exists(img_path): continue
        
        data["names"].append(name.capitalize())
        
        # Paths for outputs
        seq_out = os.path.join(RESULTS_DIR, f"{name}_seq.png")
        adapt_out = os.path.join(RESULTS_DIR, f"{name}_adapt.png")
        
        # 1. EMBEDDING
        # Sequential
        stego.dct_embed(img_path, PAYLOAD_STR, seq_out, use_adaptive=False)
        # Adaptive
        stego.dct_embed(img_path, PAYLOAD_STR, adapt_out, use_adaptive=True)
        
        # 2. VISUAL METRICS (PSNR & SSIM)
        # PSNR
        p_seq = StegoMetrics.calculate_psnr(img_path, seq_out)
        p_adp = StegoMetrics.calculate_psnr(img_path, adapt_out)
        
        # SSIM
        s_seq = calculate_ssim(img_path, seq_out)
        s_adp = calculate_ssim(img_path, adapt_out)
        
        # 3. ATTACK & RECOVERY (BER)
        # Apply JPEG Compression Attack (Quality=80)
        att_seq = AttackSimulator.apply_jpeg_compression(seq_out, quality=80)
        att_adp = AttackSimulator.apply_jpeg_compression(adapt_out, quality=80)
        
        # Since AttackSimulator saves to a fixed filename, rename them to avoid overwrites
        shutil.move(att_seq, os.path.join(RESULTS_DIR, f"{name}_seq_attacked.jpg"))
        shutil.move(att_adp, os.path.join(RESULTS_DIR, f"{name}_adapt_attacked.jpg"))
        
        # Extract
        # Note: We need a custom extraction call because the standard one might not handle the attack errors perfectly
        # We assume dct_extract returns the string or "No hidden message"
        
        # To make extraction robust for the script, we wrap it
        try: rec_seq = stego.dct_extract(os.path.join(RESULTS_DIR, f"{name}_seq_attacked.jpg"), use_adaptive=False)
        except: rec_seq = ""
        
        try: rec_adp = stego.dct_extract(os.path.join(RESULTS_DIR, f"{name}_adapt_attacked.jpg"), use_adaptive=True)
        except: rec_adp = ""
        
        # BER Calculation
        b_seq = calculate_ber(PAYLOAD_STR, rec_seq)
        b_adp = calculate_ber(PAYLOAD_STR, rec_adp)
        
        # Store Data
        data["psnr_seq"].append(p_seq)
        data["psnr_adapt"].append(p_adp)
        data["ssim_seq"].append(s_seq)
        data["ssim_adapt"].append(s_adp)
        data["ber_seq"].append(b_seq)
        data["ber_adapt"].append(b_adp)
        
        # Print Row
        print(f"{name.capitalize():<15} | {'Sequential':<12} | {p_seq:<10.2f} | {s_seq:<8.4f} | {b_seq:<12.4f}")
        print(f"{'':<15} | {'Adaptive':<12} | {p_adp:<10.2f} | {s_adp:<8.4f} | {b_adp:<12.4f}")
        print("-" * 80)

    return data

# --- STEP 3: GENERATE CHARTS ---
def generate_charts(data):
    print("[*] Generating Comparison Charts...")
    x = np.arange(len(data["names"]))
    width = 0.35
    
    # 1. PSNR Chart
    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, data["psnr_seq"], width, label='Sequential', color='gray')
    plt.bar(x + width/2, data["psnr_adapt"], width, label='Adaptive (Proposed)', color='#007acc')
    plt.xlabel('Image')
    plt.ylabel('PSNR (dB)')
    plt.title('PSNR Comparison (Higher is Better)')
    plt.xticks(x, data["names"])
    plt.legend()
    plt.savefig(os.path.join(RESULTS_DIR, 'comparison_psnr.png'))
    plt.close()
    
    # 2. SSIM Chart
    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, data["ssim_seq"], width, label='Sequential', color='gray')
    plt.bar(x + width/2, data["ssim_adapt"], width, label='Adaptive (Proposed)', color='#007acc')
    plt.xlabel('Image')
    plt.ylabel('SSIM (0.0 - 1.0)')
    plt.title('SSIM Structural Similarity (Higher is Better)')
    plt.xticks(x, data["names"])
    plt.ylim(0.8, 1.0) # Zoom in to show differences
    plt.legend()
    plt.savefig(os.path.join(RESULTS_DIR, 'comparison_ssim.png'))
    plt.close()
    
    # 3. BER Chart
    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, data["ber_seq"], width, label='Sequential', color='gray')
    plt.bar(x + width/2, data["ber_adapt"], width, label='Adaptive (Proposed)', color='#007acc')
    plt.xlabel('Image')
    plt.ylabel('Bit Error Rate (BER)')
    plt.title('BER after JPEG Attack (Lower is Better)')
    plt.xticks(x, data["names"])
    plt.legend()
    plt.savefig(os.path.join(RESULTS_DIR, 'comparison_ber.png'))
    plt.close()
    
    print(f"[+] Charts saved to '{RESULTS_DIR}/'")

if __name__ == "__main__":
    setup_environment()
    results = run_benchmark()
    generate_charts(results)
    print("\n[SUCCESS] Benchmark Complete.")
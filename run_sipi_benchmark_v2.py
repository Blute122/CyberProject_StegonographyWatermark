import os
import cv2
import numpy as np
import urllib.request
import matplotlib.pyplot as plt
import shutil
import ssl

# --- PROJECT IMPORTS ---
# Ensure this script is in the root folder (same level as 'core')
try:
    from core.steganography_dct import DCTSteganography
    from core.metrics import StegoMetrics
    from core.attacks import AttackSimulator
except ImportError:
    print("[!] Error: Could not import 'core' modules. Make sure this script is next to the 'core' folder.")
    exit()

# --- CONFIGURATION ---
# SIPI "Misc" Volume IDs for standard color images (512x512)
# 4.2.03 = Baboon, 4.2.04 = Lena, 4.2.05 = Airplane, 4.2.06 = Sailboat, 4.2.07 = Peppers
SIPI_IDS = {
    "Baboon": "4.2.03",
    "Lena": "4.2.04",
    "Airplane": "4.2.05",
    "Sailboat": "4.2.06",
    "Peppers": "4.2.07",
    "House": "4.1.05",    # House is often smaller/gray, we'll check handling
    "Splash": "4.1.07"
}

DOWNLOAD_URL = "https://sipi.usc.edu/database/download.php?vol=misc&img={}"
ASSET_DIR = "assets_sipi"
RESULTS_DIR = "results_sipi_benchmark"
PAYLOAD_STR = "Secure_Benchmark_Payload_Data_" * 50  # 1000+ chars

# Bypass SSL errors if they occur
ssl._create_default_https_context = ssl._create_unverified_context

# --- HELPER: ROBUST DOWNLOADER ---
def download_sipi_assets():
    if not os.path.exists(ASSET_DIR):
        os.makedirs(ASSET_DIR)
        
    print(f"[*] Starting download from USC-SIPI Database to '{ASSET_DIR}'...")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for name, img_id in SIPI_IDS.items():
        png_path = os.path.join(ASSET_DIR, f"{name}.png")
        tiff_path = os.path.join(ASSET_DIR, f"{name}.tiff")
        
        # Skip if already exists
        if os.path.exists(png_path):
            continue
            
        url = DOWNLOAD_URL.format(img_id)
        print(f"   > Downloading {name} (ID: {img_id})...")
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                with open(tiff_path, 'wb') as out_file:
                    out_file.write(response.read())
            
            # Convert TIFF to PNG for compatibility with your Core
            img = cv2.imread(tiff_path, cv2.IMREAD_COLOR) # Force 3-channel
            if img is None:
                print(f"     [!] Error reading {name}.tiff, skipping.")
                continue
                
            # Resize small images to 512x512 for consistent benchmarking if needed, 
            # but SIPI standard color images are usually 512x512.
            cv2.imwrite(png_path, img)
            print(f"     [+] Converted and saved to {name}.png")
            
            # Clean up tiff to save space
            if os.path.exists(tiff_path):
                os.remove(tiff_path)
                
        except Exception as e:
            print(f"     [!] Failed to download {name}: {e}")

# --- HELPER: METRICS ---
def calculate_ssim(img1_path, img2_path):
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE).astype(np.float64)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE).astype(np.float64)
    
    # Handle dimension mismatch (cropping)
    h = min(img1.shape[0], img2.shape[0])
    w = min(img1.shape[1], img2.shape[1])
    img1, img2 = img1[:h, :w], img2[:h, :w]
    
    # SSIM Constants
    C1, C2 = 6.5025, 58.5225
    kernel = (11, 11)
    sigma = 1.5
    
    mu1 = cv2.GaussianBlur(img1, kernel, sigma)
    mu2 = cv2.GaussianBlur(img2, kernel, sigma)
    mu1_sq, mu2_sq = mu1**2, mu2**2
    mu1_mu2 = mu1 * mu2
    
    sigma1_sq = cv2.GaussianBlur(img1**2, kernel, sigma) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(img2**2, kernel, sigma) - mu2_sq
    sigma12 = cv2.GaussianBlur(img1 * img2, kernel, sigma) - mu1_mu2
    
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    return np.mean(ssim_map)

def calculate_ber(original_text, recovered_text):
    if not recovered_text or recovered_text == "Extraction Error": return 0.5
    
    def to_bin(s): return ''.join(format(ord(c), '08b') for c in s)
    bin_orig = to_bin(original_text)
    bin_rec = to_bin(recovered_text)
    
    min_len = min(len(bin_orig), len(bin_rec))
    errors = sum(1 for i in range(min_len) if bin_orig[i] != bin_rec[i])
    errors += abs(len(bin_orig) - len(bin_rec)) # Length mismatch penalty
    
    return errors / max(len(bin_orig), len(bin_rec)) if len(bin_orig) > 0 else 0.0

# --- MAIN BENCHMARK LOOP ---
def run_benchmark():
    if not os.path.exists(RESULTS_DIR): os.makedirs(RESULTS_DIR)
    
    stego = DCTSteganography()
    
    # Data structure for plotting
    results = {
        "names": [],
        "psnr_seq": [], "psnr_adp": [],
        "ssim_seq": [], "ssim_adp": [],
        "ber_seq": [], "ber_adp": []
    }

    print(f"\n{'='*95}")
    print(f"{'IMAGE':<15} | {'METHOD':<12} | {'PSNR (dB)':<10} | {'SSIM':<8} | {'BER (JPEG Q=80)':<18}")
    print(f"{'='*95}")

    for name in SIPI_IDS.keys():
        src_path = os.path.join(ASSET_DIR, f"{name}.png")
        if not os.path.exists(src_path): continue

        results["names"].append(name)
        
        # Define output paths
        seq_path = os.path.join(RESULTS_DIR, f"{name}_seq.png")
        adp_path = os.path.join(RESULTS_DIR, f"{name}_adapt.png")
        
        # 1. EMBED
        # Sequential
        try: stego.dct_embed(src_path, PAYLOAD_STR, seq_path, use_adaptive=False)
        except Exception as e: 
            print(f"[!] Embed Seq failed for {name}: {e}")
            continue
            
        # Adaptive
        try: stego.dct_embed(src_path, PAYLOAD_STR, adp_path, use_adaptive=True)
        except Exception as e:
            print(f"[!] Embed Adapt failed for {name}: {e}")
            continue

        # 2. VISUAL METRICS
        p_seq = StegoMetrics.calculate_psnr(src_path, seq_path)
        p_adp = StegoMetrics.calculate_psnr(src_path, adp_path)
        s_seq = calculate_ssim(src_path, seq_path)
        s_adp = calculate_ssim(src_path, adp_path)

        # 3. ATTACK (JPEG)
        # Use AttackSimulator but handle file renaming so we don't overwrite
        AttackSimulator.apply_jpeg_compression(seq_path, quality=80)
        att_seq = os.path.join(RESULTS_DIR, f"{name}_seq_attacked.jpg")
        shutil.move("assets/attacked_compressed.jpg", att_seq)

        AttackSimulator.apply_jpeg_compression(adp_path, quality=80)
        att_adp = os.path.join(RESULTS_DIR, f"{name}_adp_attacked.jpg")
        shutil.move("assets/attacked_compressed.jpg", att_adp)

        # 4. RECOVERY & BER
        try: rec_seq = stego.dct_extract(att_seq, use_adaptive=False)
        except: rec_seq = "Extraction Error"
        
        try: rec_adp = stego.dct_extract(att_adp, use_adaptive=True)
        except: rec_adp = "Extraction Error"

        ber_seq = calculate_ber(PAYLOAD_STR, rec_seq)
        ber_adp = calculate_ber(PAYLOAD_STR, rec_adp)

        # Store
        results["psnr_seq"].append(p_seq)
        results["psnr_adp"].append(p_adp)
        results["ssim_seq"].append(s_seq)
        results["ssim_adp"].append(s_adp)
        results["ber_seq"].append(ber_seq)
        results["ber_adp"].append(ber_adp)

        # Print Table Row
        print(f"{name:<15} | {'Sequential':<12} | {p_seq:<10.2f} | {s_seq:<8.4f} | {ber_seq:<18.4f}")
        print(f"{'':<15} | {'Adaptive':<12} | {p_adp:<10.2f} | {s_adp:<8.4f} | {ber_adp:<18.4f}")
        print(f"{'-'*95}")

    return results

# --- HELPER: PLOTTING ---
def save_charts(res):
    if not res["names"]: return
    
    x = np.arange(len(res["names"]))
    width = 0.35
    
    # Setup styles
    colors = ['#bdc3c7', '#2ecc71'] # Gray for Seq, Green for Adaptive
    
    def plot_metric(metric_seq, metric_adp, title, ylabel, filename, low_limit=None):
        plt.figure(figsize=(12, 6))
        plt.bar(x - width/2, metric_seq, width, label='Sequential', color=colors[0])
        plt.bar(x + width/2, metric_adp, width, label='Adaptive (Proposed)', color=colors[1])
        plt.xlabel('SIPI Database Images')
        plt.ylabel(ylabel)
        plt.title(title)
        plt.xticks(x, res["names"])
        if low_limit: plt.ylim(low_limit, 1.0)
        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.savefig(os.path.join(RESULTS_DIR, filename))
        plt.close()

    print("[*] Generating comparison charts...")
    plot_metric(res["psnr_seq"], res["psnr_adp"], "Peak Signal-to-Noise Ratio (PSNR)", "dB", "chart_psnr.png")
    plot_metric(res["ssim_seq"], res["ssim_adp"], "Structural Similarity Index (SSIM)", "Index (0-1)", "chart_ssim.png", low_limit=0.8)
    plot_metric(res["ber_seq"], res["ber_adp"], "Bit Error Rate (BER) after JPEG Attack", "Error Rate (Lower is Better)", "chart_ber.png")
    print(f"[+] All charts saved in '{RESULTS_DIR}/'")

if __name__ == "__main__":
    download_sipi_assets()
    data = run_benchmark()
    save_charts(data)
    print("\n[SUCCESS] SIPI Database Benchmark Completed.")
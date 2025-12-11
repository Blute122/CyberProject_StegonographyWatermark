import os
import cv2
import numpy as np
import urllib.request
import ssl
import matplotlib.pyplot as plt
import shutil

# --- PROJECT IMPORTS ---
# Ensure this script is running in the project root
try:
    from core.steganography_dct import DCTSteganography
    from core.metrics import StegoMetrics
    from core.attacks import AttackSimulator
except ImportError:
    print("[!] Error: Could not import 'core'. Run this script from the project root directory.")
    exit()

# --- CONFIGURATION ---
ASSET_DIR = "assets_sipi_misc"
RESULTS_DIR = "results_sipi_misc"
PAYLOAD = "SIPI_BENCHMARK_TEST_PAYLOAD_" * 50  # 1000+ chars for robust testing

# SIPI 'Misc' Volume IDs (Common 512x512 and 256x256 images)
# Format: "Name": "Image ID"
SIPI_IMAGES = {
    "Gray_Girl": "4.1.01",
    "Gray_Couple": "4.1.02",
    "Gray_Splash": "4.1.07",
    "Color_Baboon": "4.2.03",
    "Color_Lena": "4.2.04",
    "Color_Airplane": "4.2.05",
    "Color_Sailboat": "4.2.06",
    "Color_Peppers": "4.2.07"
}

# --- HELPER: ROBUST DOWNLOADER ---
def setup_database():
    if not os.path.exists(ASSET_DIR):
        os.makedirs(ASSET_DIR)
    
    # Bypass SSL verification errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Headers to look like a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f"[*] Downloading SIPI 'Misc' images to '{ASSET_DIR}'...")
    
    for name, img_id in SIPI_IMAGES.items():
        png_path = os.path.join(ASSET_DIR, f"{name}.png")
        if os.path.exists(png_path):
            continue # Skip if already exists
            
        url = f"https://sipi.usc.edu/database/download.php?vol=misc&img={img_id}"
        tiff_path = os.path.join(ASSET_DIR, f"{name}.tiff")
        
        try:
            # 1. Download
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx) as response:
                with open(tiff_path, 'wb') as f:
                    f.write(response.read())
            
            # 2. Convert TIFF -> PNG (OpenCV handles this)
            img = cv2.imread(tiff_path)
            if img is None:
                print(f"   [!] Failed to read downloaded file for {name}")
                continue
                
            cv2.imwrite(png_path, img)
            print(f"   [+] Downloaded & Converted: {name}.png")
            
            # 3. Cleanup
            os.remove(tiff_path)
            
        except Exception as e:
            print(f"   [!] Error downloading {name}: {e}")

# --- HELPER: METRICS ---
def calculate_ssim(img1_path, img2_path):
    # Manual SSIM implementation using OpenCV
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE).astype(np.float64)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE).astype(np.float64)
    
    # Crop to match
    h = min(img1.shape[0], img2.shape[0])
    w = min(img1.shape[1], img2.shape[1])
    img1, img2 = img1[:h, :w], img2[:h, :w]
    
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

def calculate_ber(original, recovered):
    if not recovered or recovered == "Extraction Error": return 0.5
    
    def to_bin(s): return ''.join(format(ord(c), '08b') for c in s)
    bin_orig = to_bin(original)
    bin_rec = to_bin(recovered)
    
    min_len = min(len(bin_orig), len(bin_rec))
    errors = sum(1 for i in range(min_len) if bin_orig[i] != bin_rec[i])
    errors += abs(len(bin_orig) - len(bin_rec))
    
    return errors / max(len(bin_orig), len(bin_rec)) if len(bin_orig) > 0 else 0.0

# --- MAIN BENCHMARK ---
def run_benchmark():
    if not os.path.exists(RESULTS_DIR): os.makedirs(RESULTS_DIR)
    
    stego = DCTSteganography()
    
    # Results storage
    data = {
        "names": [],
        "psnr_seq": [], "psnr_adapt": [],
        "ssim_seq": [], "ssim_adapt": [],
        "ber_seq": [], "ber_adapt": []
    }
    
    print("\n" + "="*85)
    print(f"{'IMAGE':<20} | {'METHOD':<10} | {'PSNR (dB)':<10} | {'SSIM':<8} | {'BER (JPEG)':<10}")
    print("="*85)
    
    for name in SIPI_IMAGES.keys():
        src = os.path.join(ASSET_DIR, f"{name}.png")
        if not os.path.exists(src): continue
        
        data["names"].append(name)
        
        # Paths
        seq_out = os.path.join(RESULTS_DIR, f"{name}_seq.png")
        adp_out = os.path.join(RESULTS_DIR, f"{name}_adapt.png")
        
        # 1. Embed
        try:
            stego.dct_embed(src, PAYLOAD, seq_out, use_adaptive=False)
            stego.dct_embed(src, PAYLOAD, adp_out, use_adaptive=True)
        except Exception as e:
            print(f"[!] Embedding failed for {name}: {e}")
            # Fill with zeros to keep arrays aligned
            for k in data.keys(): 
                if k != "names": data[k].append(0)
            continue

        # 2. Metrics (Visual)
        p_seq = StegoMetrics.calculate_psnr(src, seq_out)
        p_adp = StegoMetrics.calculate_psnr(src, adp_out)
        s_seq = calculate_ssim(src, seq_out)
        s_adp = calculate_ssim(src, adp_out)
        
        # 3. Attack (JPEG Compression Q=80) & Recovery
        # Use AttackSimulator, then move/rename result
        AttackSimulator.apply_jpeg_compression(seq_out, quality=80)
        shutil.move("assets/attacked_compressed.jpg", os.path.join(RESULTS_DIR, f"{name}_seq_att.jpg"))
        
        AttackSimulator.apply_jpeg_compression(adp_out, quality=80)
        shutil.move("assets/attacked_compressed.jpg", os.path.join(RESULTS_DIR, f"{name}_adp_att.jpg"))
        
        # Extract
        try: rec_seq = stego.dct_extract(os.path.join(RESULTS_DIR, f"{name}_seq_att.jpg"), use_adaptive=False)
        except: rec_seq = ""
        
        try: rec_adp = stego.dct_extract(os.path.join(RESULTS_DIR, f"{name}_adp_att.jpg"), use_adaptive=True)
        except: rec_adp = ""
        
        # BER
        b_seq = calculate_ber(PAYLOAD, rec_seq)
        b_adp = calculate_ber(PAYLOAD, rec_adp)
        
        # Store
        data["psnr_seq"].append(p_seq)
        data["psnr_adapt"].append(p_adp)
        data["ssim_seq"].append(s_seq)
        data["ssim_adapt"].append(s_adp)
        data["ber_seq"].append(b_seq)
        data["ber_adapt"].append(b_adp)
        
        # Print Table
        print(f"{name:<20} | {'Sequential':<10} | {p_seq:<10.2f} | {s_seq:<8.4f} | {b_seq:<10.4f}")
        print(f"{'':<20} | {'Adaptive':<10} | {p_adp:<10.2f} | {s_adp:<8.4f} | {b_adp:<10.4f}")
        print("-" * 85)
        
    return data

# --- PLOTTING ---
def generate_charts(data):
    if not data["names"]:
        print("[!] No data to plot.")
        return

    x = np.arange(len(data["names"]))
    width = 0.35
    
    # 1. PSNR
    plt.figure(figsize=(12, 6))
    plt.bar(x - width/2, data["psnr_seq"], width, label='Sequential', color='gray')
    plt.bar(x + width/2, data["psnr_adapt"], width, label='Adaptive (Proposed)', color='#2ecc71')
    plt.ylabel('PSNR (dB)')
    plt.title('PSNR Visual Quality Comparison')
    plt.xticks(x, data["names"], rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "chart_psnr.png"))
    plt.close()
    
    # 2. SSIM
    plt.figure(figsize=(12, 6))
    plt.bar(x - width/2, data["ssim_seq"], width, label='Sequential', color='gray')
    plt.bar(x + width/2, data["ssim_adapt"], width, label='Adaptive (Proposed)', color='#3498db')
    plt.ylabel('SSIM (0-1)')
    plt.title('Structural Similarity Comparison')
    plt.xticks(x, data["names"], rotation=45)
    plt.ylim(0.8, 1.0)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "chart_ssim.png"))
    plt.close()

    # 3. BER
    plt.figure(figsize=(12, 6))
    plt.bar(x - width/2, data["ber_seq"], width, label='Sequential', color='gray')
    plt.bar(x + width/2, data["ber_adapt"], width, label='Adaptive (Proposed)', color='#e74c3c')
    plt.ylabel('Bit Error Rate (BER)')
    plt.title('Error Rate after JPEG Attack (Lower is Better)')
    plt.xticks(x, data["names"], rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "chart_ber.png"))
    plt.close()
    
    print(f"[+] Charts saved to '{RESULTS_DIR}/'")

if __name__ == "__main__":
    setup_database()
    results = run_benchmark()
    generate_charts(results)
    print("\n[SUCCESS] Benchmark Complete.")
import os
import cv2
import numpy as np
import urllib.request
import ssl
import matplotlib.pyplot as plt
import pandas as pd 
import shutil
import time

# --- PROJECT IMPORTS ---
try:
    from core.steganography_dct import DCTSteganography
    from core.metrics import StegoMetrics
    from core.attacks import AttackSimulator
except ImportError:
    print("[!] Error: Could not import 'core'. Run this script from the project root.")
    exit()

# --- CONFIGURATION ---
ASSET_DIR = "assets_sipi_full"
RESULTS_DIR = "results_sipi_full"
CSV_FILE = os.path.join(RESULTS_DIR, "benchmark_report.csv")
PAYLOAD = "FULL_BENCHMARK_PAYLOAD_" * 100  # 2000+ chars

# --- SIPI MISC VOLUME ID RANGES ---
ID_RANGES = [
    ("4.1", 1, 9),   # 4.1.01 - 4.1.08 (256x256 Color)
    ("4.2", 1, 8),   # 4.2.01 - 4.2.07 (512x512 Color)
    ("5.1", 1, 15),  # 5.1.01 - 5.1.14 (256x256 Mono)
    ("5.2", 1, 11),  # 5.2.01 - 5.2.10 (512x512 Mono)
    ("5.3", 1, 3),   # 5.3.01 - 5.3.02 (1024x1024 Mono)
    ("7.1", 1, 11),  # Misc sequences
    ("elaine", 0, 0) # Special named file
]

# --- HELPERS ---

def get_sipi_url(prefix, index):
    if prefix == "elaine": 
        return "https://sipi.usc.edu/database/download.php?vol=misc&img=elaine.512", "elaine.512"
    
    # Format ID as X.Y.ZZ (e.g., 4.1.01)
    img_id = f"{prefix}.{index:02d}"
    return f"https://sipi.usc.edu/database/download.php?vol=misc&img={img_id}", img_id

def download_all_images():
    if not os.path.exists(ASSET_DIR): os.makedirs(ASSET_DIR)
    
    # SSL Context to ignore cert errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {'User-Agent': 'Mozilla/5.0'}

    print(f"[*] Scanning & Downloading USC-SIPI Misc Volume (~40 images)...")
    
    valid_images = []

    for prefix, start, end in ID_RANGES:
        if prefix == "elaine":
            loop_range = [0]
        else:
            loop_range = range(start, end)

        for i in loop_range:
            url, name = get_sipi_url(prefix, i)
            save_path_tiff = os.path.join(ASSET_DIR, f"{name}.tiff")
            save_path_png = os.path.join(ASSET_DIR, f"{name}.png")

            # Skip if PNG already exists
            if os.path.exists(save_path_png):
                valid_images.append(name)
                continue

            try:
                # 1. Download
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=ctx) as response:
                    data = response.read()
                    
                # Filter: If file is too small (< 2KB), it's likely an error page/404
                if len(data) < 2000:
                    continue 

                with open(save_path_tiff, 'wb') as f:
                    f.write(data)

                # 2. Convert to PNG
                img = cv2.imread(save_path_tiff)
                if img is None:
                    os.remove(save_path_tiff)
                    continue

                cv2.imwrite(save_path_png, img)
                valid_images.append(name)
                os.remove(save_path_tiff) # Clean up tiff
                print(f"   [+] Acquired: {name}")
                time.sleep(0.5) # Be nice to the server

            except Exception as e:
                pass # Silent fail for missing IDs

    print(f"[*] Total valid images found: {len(valid_images)}")
    return valid_images

def calculate_ssim_manual(img1_path, img2_path):
    # Robust SSIM calculation
    i1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
    i2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
    if i1 is None or i2 is None: return 0.0
    
    i1 = i1.astype(np.float64)
    i2 = i2.astype(np.float64)
    
    # Resize to match smallest
    h = min(i1.shape[0], i2.shape[0])
    w = min(i1.shape[1], i2.shape[1])
    i1, i2 = i1[:h, :w], i2[:h, :w]
    
    C1, C2 = 6.5025, 58.5225
    k = (11, 11); s = 1.5
    mu1 = cv2.GaussianBlur(i1, k, s); mu2 = cv2.GaussianBlur(i2, k, s)
    sigma1_sq = cv2.GaussianBlur(i1**2, k, s) - mu1**2
    sigma2_sq = cv2.GaussianBlur(i2**2, k, s) - mu2**2
    sigma12 = cv2.GaussianBlur(i1*i2, k, s) - mu1*mu2
    
    ssim_map = ((2*mu1*mu2 + C1)*(2*sigma12 + C2)) / ((mu1**2 + mu2**2 + C1)*(sigma1_sq + sigma2_sq + C2))
    return np.mean(ssim_map)

def calculate_ber(orig, rec):
    if not rec or rec.startswith("Extraction Error") or rec == "No hidden message found.":
        return 0.5
    
    def to_bin(s): return ''.join(format(ord(c), '08b') for c in s)
    try:
        b_orig = to_bin(orig)
        b_rec = to_bin(rec)
    except: return 0.5
    
    l = min(len(b_orig), len(b_rec))
    errs = sum(1 for i in range(l) if b_orig[i] != b_rec[i])
    errs += abs(len(b_orig) - len(b_rec))
    return errs / max(len(b_orig), len(b_rec), 1)

# --- MAIN BENCHMARK ---
def run_benchmark():
    if not os.path.exists(RESULTS_DIR): os.makedirs(RESULTS_DIR)
    
    images = download_all_images()
    stego = DCTSteganography()
    
    results = []

    print("\n" + "="*80)
    print(f"Starting Benchmark on {len(images)} images...")
    print("="*80)

    for idx, name in enumerate(images):
        src = os.path.join(ASSET_DIR, f"{name}.png")
        row = {"Image": name}
        
        # Paths
        seq_out = os.path.join(RESULTS_DIR, f"{name}_seq.png")
        adp_out = os.path.join(RESULTS_DIR, f"{name}_adp.png")
        
        print(f"[{idx+1}/{len(images)}] Processing {name}...", end="\r")

        try:
            # 1. EMBED
            stego.dct_embed(src, PAYLOAD, seq_out, use_adaptive=False)
            stego.dct_embed(src, PAYLOAD, adp_out, use_adaptive=True)
            
            # 2. METRICS (PSNR, SSIM)
            row["PSNR_Seq"] = StegoMetrics.calculate_psnr(src, seq_out)
            row["PSNR_Adp"] = StegoMetrics.calculate_psnr(src, adp_out)
            row["SSIM_Seq"] = calculate_ssim_manual(src, seq_out)
            row["SSIM_Adp"] = calculate_ssim_manual(src, adp_out)
            
            # 3. ATTACK (JPEG Q=70)
            AttackSimulator.apply_jpeg_compression(seq_out, quality=70)
            att_seq = os.path.join(RESULTS_DIR, f"{name}_seq_att.jpg")
            shutil.move("assets/attacked_compressed.jpg", att_seq)
            
            AttackSimulator.apply_jpeg_compression(adp_out, quality=70)
            att_adp = os.path.join(RESULTS_DIR, f"{name}_adp_att.jpg")
            shutil.move("assets/attacked_compressed.jpg", att_adp)
            
            # 4. RECOVERY & BER
            try: r_seq = stego.dct_extract(att_seq, use_adaptive=False)
            except: r_seq = ""
            try: r_adp = stego.dct_extract(att_adp, use_adaptive=True)
            except: r_adp = ""
            
            row["BER_Seq"] = calculate_ber(PAYLOAD, r_seq)
            row["BER_Adp"] = calculate_ber(PAYLOAD, r_adp)
            
            results.append(row)

        except Exception as e:
            print(f"\n[!] Failed on {name}: {e}")

    # Save to CSV
    df = pd.DataFrame(results)
    df.to_csv(CSV_FILE, index=False)
    print(f"\n\n[+] Benchmark Complete. Data saved to {CSV_FILE}")
    return df

# --- CHART GENERATION ---
def generate_summary_charts(df):
    if df.empty: return

    # Calculate Averages for the Bar Charts
    avg_psnr_seq = df["PSNR_Seq"].mean()
    avg_psnr_adp = df["PSNR_Adp"].mean()
    
    avg_ssim_seq = df["SSIM_Seq"].mean()
    avg_ssim_adp = df["SSIM_Adp"].mean()
    
    avg_ber_seq = df["BER_Seq"].mean()
    avg_ber_adp = df["BER_Adp"].mean()

    # --- Chart 1: PSNR Distribution ---
    plt.figure(figsize=(12, 6))
    plt.plot(df["Image"], df["PSNR_Seq"], label="Sequential", marker='o', linestyle='--')
    plt.plot(df["Image"], df["PSNR_Adp"], label="Adaptive", marker='s')
    plt.xticks(rotation=90)
    plt.title("PSNR Comparison per Image (Higher is Better)")
    plt.ylabel("dB")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "result_psnr_all.png"))
    plt.close()

    # --- Chart 2: SSIM Comparison (ADDED) ---
    plt.figure(figsize=(12, 6))
    # We use a line chart because values are very close (0.9x), lines show trends better
    plt.plot(df["Image"], df["SSIM_Seq"], label="Sequential", marker='o', linestyle='--', color='gray')
    plt.plot(df["Image"], df["SSIM_Adp"], label="Adaptive", marker='s', color='blue')
    plt.xticks(rotation=90)
    plt.title("SSIM Structural Similarity (Higher is Better)")
    plt.ylabel("SSIM Index (0.0 - 1.0)")
    plt.ylim(0.85, 1.0) # Zoom in to show differences
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "result_ssim_all.png"))
    plt.close()

    # --- Chart 3: BER Comparison ---
    plt.figure(figsize=(12, 6))
    plt.bar(df["Image"], df["BER_Seq"], alpha=0.6, label="Sequential", color='red')
    plt.bar(df["Image"], df["BER_Adp"], alpha=0.8, label="Adaptive", color='green')
    plt.xticks(rotation=90)
    plt.title("BER after Attack (Lower is Better)")
    plt.ylabel("Bit Error Rate")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "result_ber_all.png"))
    plt.close()

    print(f"[+] Charts saved to {RESULTS_DIR}")
    
    # Print Summary Table
    print("\n" + "="*50)
    print("FINAL AGGREGATE RESULTS (Average of 40+ Images)")
    print("="*50)
    print(f"{'Metric':<15} | {'Sequential':<12} | {'Adaptive':<12}")
    print("-" * 50)
    print(f"{'PSNR':<15} | {avg_psnr_seq:<12.2f} | {avg_psnr_adp:<12.2f}")
    print(f"{'SSIM':<15} | {avg_ssim_seq:<12.4f} | {avg_ssim_adp:<12.4f}")
    print(f"{'BER (Attack)':<15} | {avg_ber_seq:<12.4f} | {avg_ber_adp:<12.4f}")
    print("="*50)

if __name__ == "__main__":
    df_results = run_benchmark()
    generate_summary_charts(df_results)
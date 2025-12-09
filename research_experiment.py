import os
import requests
import cv2
import pandas as pd
import numpy as np
from core.steganography_dct import DCTSteganography
from core.metrics import StegoMetrics
from core.attacks import AttackSimulator

# --- CONFIGURATION ---
DATASET_URLS = {
    "Lena": "https://raw.githubusercontent.com/mikolalysenko/lena/master/lena.png",
    "Baboon": "https://raw.githubusercontent.com/scijs/baboon-image/master/baboon.png",
    # FIXED: Reliable Peppers URL from a standard image repo
    "Peppers": "https://raw.githubusercontent.com/mohammadimtiazz/standard-test-images-for-Image-Processing/master/standard_test_images/peppers.png"
}
DATA_DIR = "research_data"
RESULTS_FILE = "research_results.csv"

# Short message to fit in "Safe Zones" easily
SECRET_MESSAGE = "SECRET_DATA_2025" 

def download_images():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    print(f"[*] Downloading Standard Test Images to {DATA_DIR}...")
    headers = {'User-Agent': 'Mozilla/5.0'}

    for name, url in DATASET_URLS.items():
        path = os.path.join(DATA_DIR, f"{name}.png")
        if not os.path.exists(path):
            try:
                print(f"    [...] Fetching {name}...")
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    with open(path, 'wb') as f:
                        f.write(response.content)
                    print(f"    [+] Successfully downloaded {name}")
                else:
                    print(f"    [!] Failed {name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"    [!] Error downloading {name}: {e}")
        else:
            print(f"    [.] {name} already exists.")

def run_experiment():
    stego = DCTSteganography()
    results = []
    
    available_images = [f for f in os.listdir(DATA_DIR) if f.endswith(".png") and "stego" not in f and "attack" not in f]
    
    # We test two modes:
    # 1. Adaptive AI (Secure/Invisible) - Expected to be Fragile
    # 2. Sequential (Robust) - Expected to survive attacks
    modes = [
        ("AI_Mode", True), 
        ("Robust_Mode", False)
    ]
    
    attacks = [
        ("No Attack", None, None),
        ("JPEG Q=90", AttackSimulator.apply_jpeg_compression, {"quality": 90}),
        ("JPEG Q=70", AttackSimulator.apply_jpeg_compression, {"quality": 70}),
        ("Noise (Gauss)", AttackSimulator.apply_noise_gaussian, {"var": 10}),
        ("Crop 5%", AttackSimulator.apply_crop, {"crop_percent": 5})
    ]

    print("\n[*] Starting Scientific Validation Loop...")
    
    for img_file in available_images:
        img_name = img_file.split('.')[0]
        original_path = os.path.join(DATA_DIR, img_file)
        
        for mode_name, use_ai in modes:
            print(f"\n--- Testing {img_name} [{mode_name}] ---")
            stego_path = os.path.join(DATA_DIR, f"{img_name}_{mode_name}_stego.png")
            
            # 1. Embed
            try:
                stego.dct_embed(original_path, SECRET_MESSAGE, stego_path, use_adaptive=use_ai)
            except Exception as e:
                print(f"    [!] Embedding failed: {e}")
                continue

            # 2. Attacks
            for attack_name, attack_func, kwargs in attacks:
                attacked_path = stego_path 
                if attack_func:
                    try:
                        attacked_path = attack_func(stego_path, **kwargs)
                    except:
                        continue
                
                # 3. Extract (Must use same mode!)
                try:
                    extracted_msg = stego.dct_extract(attacked_path, use_adaptive=use_ai)
                except:
                    extracted_msg = ""
                
                ber = StegoMetrics.calculate_ber(SECRET_MESSAGE, extracted_msg)
                psnr = StegoMetrics.calculate_psnr(original_path, attacked_path)
                ssim = StegoMetrics.calculate_ssim(original_path, attacked_path)
                
                status = "PASS" if ber < 0.05 else "FAIL"
                
                print(f"    > {attack_name: <15} | PSNR: {psnr:.2f} | BER: {ber:.4f} [{status}]")
                
                results.append({
                    "Image": img_name,
                    "Mode": mode_name,
                    "Attack": attack_name,
                    "PSNR": round(psnr, 2),
                    "SSIM": round(ssim, 4),
                    "BER": round(ber, 4),
                    "Result": status
                })

    if results:
        df = pd.DataFrame(results)
        df.to_csv(RESULTS_FILE, index=False)
        print(f"\n[+] Results saved to {RESULTS_FILE}")
        # Display summary of Robust Mode (Sequential) which should perform better
        print("\n--- Summary: Robust Mode Performance ---")
        print(df[df["Mode"] == "Robust_Mode"][["Image", "Attack", "BER", "Result"]])

if __name__ == "__main__":
    download_images()
    run_experiment()
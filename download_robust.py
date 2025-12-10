import urllib.request
import os
import shutil

# List of Mirrors (If one fails, it tries the next)
MIRRORS = {
    "baboon": [
        "https://raw.githubusercontent.com/scijs/baboon-image/master/baboon.png",
        "https://homepages.cae.wisc.edu/~ece533/images/baboon.png",
        "https://raw.githubusercontent.com/yoyowz/SRGAN/master/data/Set14/baboon.png"
    ],
    "peppers": [
        "https://raw.githubusercontent.com/yoyowz/SRGAN/master/data/Set14/pepper.png", # Note: sometimes named 'pepper.png'
        "https://homepages.cae.wisc.edu/~ece533/images/peppers.png",
        "https://raw.githubusercontent.com/mathworks/embedded-coder-examples/master/matlab/test_images/peppers.png"
    ]
}

def download_robust(name):
    print(f"--- Attempting to download: {name} ---")
    save_path = f"assets/{name}.png"
    
    # Create assets folder if missing
    if not os.path.exists("assets"):
        os.makedirs("assets")

    for url in MIRRORS[name]:
        try:
            print(f"  Trying: {url} ...")
            # Fake a browser user-agent to bypass firewall blocks
            req = urllib.request.Request(
                url, 
                data=None, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response, open(save_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            
            print(f"  [+] Success! Saved to {save_path}")
            return True
        except Exception as e:
            print(f"  [!] Failed ({e})")
            continue
    
    print(f"  [X] All mirrors failed for {name}. Please download manually.")
    return False

if __name__ == "__main__":
    download_robust("baboon")
    download_robust("peppers")
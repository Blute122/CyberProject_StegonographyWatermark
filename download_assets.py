import urllib.request
import os

def download_image(name):
    url = f"https://homepages.cae.wisc.edu/~ece533/images/{name}.png"
    save_path = f"assets/{name}.png"
    
    if not os.path.exists("assets"):
        os.makedirs("assets")
        
    print(f"Downloading {name}...")
    try:
        urllib.request.urlretrieve(url, save_path)
        print(f"  [+] Saved to {save_path}")
    except Exception as e:
        print(f"  [!] Failed: {e}")

# Download the "Big Three"
images = ["lena", "peppers", "baboon"]

print("--- Downloading Standard Benchmarks ---")
for img in images:
    download_image(img)
print("Done. You can now run the research script.")
# Hybrid Steganography & Watermarking System (Enterprise Edition)

## 📌 Project Overview
This project implements a sophisticated **Dual-Layer Cybersecurity System** designed to protect digital media through a hybrid approach. [cite_start]It combines **Adaptive DCT Steganography** for covert communication with **DWT-based Digital Watermarking** for copyright protection and tamper detection[cite: 31, 37, 54].

[cite_start]Unlike traditional systems that use fragile LSB hiding, this architecture employs **AI-driven Texture Analysis** to hide data only in high-entropy (busy) regions, making the secret message statistically invisible to forensic tools[cite: 80, 124]. [cite_start]Furthermore, it integrates **RSA-2048 Asymmetric Encryption** to solve the key distribution problem, ensuring secure message exchange[cite: 81, 120].

## 🚀 Key Features

### 1. 🧠 AI-Driven Adaptive Steganography
* [cite_start]**Intelligent Embedding:** Uses **Canny Edge Detection** and Gaussian Blur to generate a "Complexity Map" of the image[cite: 80, 165].
* **Adaptive Logic:** Hides data *only* in complex image regions (edges/textures) where human vision is less sensitive, ignoring smooth areas like skies or walls.
* [cite_start]**Technology:** Discrete Cosine Transform (DCT) with Quantization (`Q=25`)[cite: 51, 194].

### 2. 🛡️ Dual-Layer Watermarking
[cite_start]The system implements the "Hybrid Approach" suggested in modern research[cite: 37, 54]:
* **Robust Layer (Ownership):** Embeds a visible-invisible watermark into the **High-High (HH)** frequency band using **Discrete Wavelet Transform (DWT)**. [cite_start]This survives attacks like compression and cropping[cite: 52, 168].
* **Fragile Layer (Integrity):** Embeds a SHA-256 hash of the image into the LSB of the last pixel row. [cite_start]This "Digital Seal" shatters if a single bit is altered[cite: 16, 82].

### 3. 🔐 Enterprise-Grade Cryptography
* **RSA-2048:** Uses asymmetric encryption to exchange session keys. [cite_start]You only need the recipient's **Public Key** to send a message[cite: 120].
* [cite_start]**AES-256:** Encrypts the actual payload using a randomized session key for military-grade security[cite: 81, 93].

### 4. ⚔️ Threat Simulation & Forensics
* [cite_start]**Attack Simulator:** Built-in module to subject images to JPEG Compression, Noise Injection, and Cropping to prove watermark robustness[cite: 167, 196].
* [cite_start]**Steganalysis Tool:** Includes a Chi-Square statistical scanner to verify that the steganography is undetectable (0.00% detection probability)[cite: 164, 199].

---

## 🏗️ System Architecture

[cite_start]The pipeline follows the **Multi-Layer Security Architecture**[cite: 115]:

1.  **Preprocessing:** Image is analyzed for texture density.
2.  **Watermarking:** Inverted Logo is embedded via DWT-HH band.
3.  **Encryption:** Message is encrypted (AES) -> Session Key is encrypted (RSA).
4.  **Embedding:** Encrypted payload is injected into DCT coefficients of "busy" blocks.
5.  **Sealing:** Fragile Hash is applied to the final pixel row.

---

## 🛠️ Technology Stack
* [cite_start]**Language:** Python 3.x [cite: 117]
* **GUI:** Tkinter (Custom Dashboard)
* [cite_start]**Computer Vision:** OpenCV (`cv2`), NumPy [cite: 118, 121]
* **Signal Processing:** PyWavelets (`pywt`), SciPy
* [cite_start]**Cryptography:** PyCryptodome (RSA, AES, SHA-256) [cite: 120]

---

## ⚙️ Installation

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/yourusername/cyber-stego-project.git](https://github.com/yourusername/cyber-stego-project.git)
    cd cyber-stego-project
    ```

2.  **Install Dependencies:**
    ```bash
    pip install opencv-python numpy PyWavelets pycryptodome scipy
    ```

3.  **Prepare Assets:**
    * Ensure a `watermark.png` (black logo on white background) is inside the `assets/` folder.
    * Ensure a `cover_image.png` is available for testing.

---

## 🖥️ Usage Guide

Run the main application:
```bash
python gui.py
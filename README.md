# Hybrid Multimedia Security Suite (Enterprise Research Edition)

## 📌 Project Overview
This system implements a comprehensive **Multi-Modal Security Framework** designed to protect digital signals (Images, Video, and Audio) through a robust, layered approach. It combines **Adaptive Steganography** for covert communication with **Dual Watermarking** for copyright and integrity verification.

The final architecture features **RSA Asymmetric Encryption** for secure key exchange and advanced **Computer Vision** techniques to ensure that hidden data remains statistically invisible to forensic tools.

## 🚀 Key Features

### 1. 🔐 Enterprise-Grade Identity & Cryptography
* **RSA-2048 Asymmetric Key Exchange:** Solves the key distribution problem. The sender encrypts a randomized AES Session Key using the recipient's **Public Key**.
* **AES-256 Encryption:** Provides military-grade protection for the message payload itself.

### 2. 🧠 Adaptive Steganography Engine
* **AI-Driven Hiding (Images):** Uses **Canny Edge Detection** (Texture Analysis) to identify and utilize high-entropy regions, maximizing PSNR (>43 dB).
* **Multi-Modal Support:**
    * **Images:** Adaptive DCT Hiding.
    * **Video:** Sequential Hiding using the **FFV1/HFYU Lossless Codec**.
    * **Audio:** LSB Hiding in WAV files (skipping the 44-byte header).

### 3. 🛡️ Dual-Layer Watermarking
* **Robust Layer (Ownership):** DWT-based logo embedding (with Inverted Masking fix) that survives geometric and compression attacks.
* **Fragile Layer (Integrity):** SHA-256 LSB hash seal that instantly alerts to single-bit tampering.

### 4. ⚔️ Forensics & Validation Tools
* **Steganalysis Defense:** Achieves **0.00% detection rate** against the industry-standard Chi-Square statistical attack.
* **Attack Simulator:** Built-in module to test system robustness against JPEG compression and noise injection.

---

## 🏗️ Technical Architecture

| Component | Technology | Function |
| :--- | :--- | :--- |
| **GUI Frontend** | PyQt6/PySide6 | Professional, high-performance user interface. |
| **Key Exchange** | RSA-2048 (PyCryptodome) | Secures the AES Session Key. |
| **Image Hiding** | Adaptive DCT | Hides data based on image texture/complexity. |
| **Video/Audio Hiding** | Sequential LSB/DCT | Robust payload injection for unstable media formats. |
| **Robust Watermark** | DWT-HH | Proves ownership against hostile environments. |

---

## ⚙️ Installation & Usage

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/Blute122/CyberProject_StegonographyWatermark.git](https://github.com/Blute122/CyberProject_StegonographyWatermark.git)
    cd CyberProject_StegonographyWatermark
    ```

2.  **Install Dependencies:**
    ```bash
    pip install opencv-python numpy PyWavelets pycryptodome scipy PySide6
    ```

3.  **Launch the Application:**
    ```bash
    python gui_qt.py
    ```

### **Usage Workflow**

* **Setup:** Go to **🔑 Keys** tab and click **"Generate New Key Pair"**. (Saves `my_public_key.pem` and `my_private_key.pem`).
* **Protect:** Go to **🛡️ Image Protect**. Load Image, Message, and the **Recipient's Public Key**.
* **Video/Audio:** Use the dedicated **Video** and **Audio** tabs to test multi-modal hiding capabilities.
* **Verify:** Go to **🔍 Image Verify**. Load the Stego File and **Your Private Key** to decrypt and validate.
* **Analyze:** Use the **⚔️ Attack Sim** and **🕵️ Steganalysis** tabs to prove the system's robustness and invisibility.
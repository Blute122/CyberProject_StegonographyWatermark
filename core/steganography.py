import cv2
import numpy as np

class LSBSteganography:
    def __init__(self):
        self.delimiter = "$$$"  # Secret marker to know where message ends

    def to_binary(self, data):
        """Convert string data to binary format"""
        if isinstance(data, str):
            return ''.join([format(ord(i), "08b") for i in data])
        elif isinstance(data, bytes):
            return ''.join([format(i, "08b") for i in data])
        elif isinstance(data, np.ndarray):
            return [format(i, "08b") for i in data]
        elif isinstance(data, int) or isinstance(data, np.uint8):
            return format(data, "08b")
        else:
            raise TypeError("Input type not supported")

    def encode(self, image_path, secret_message, output_path):
        """Encodes a secret message into an image using LSB"""
        # 1. Read the image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Image not found at {image_path}")
        
        # 2. Append delimiter to message so we know when to stop reading later
        secret_message += self.delimiter
        
        # 3. Convert message to binary
        binary_message = self.to_binary(secret_message)
        data_len = len(binary_message)
        
        # 4. Check if image is big enough
        max_bytes = image.shape[0] * image.shape[1] * 3 // 8
        if len(secret_message) > max_bytes:
            raise ValueError(f"Error: Insufficient bytes, need bigger image or less data.")
        
        print(f"[*] Encoding {data_len} bits into image...")

        data_index = 0
        
        # 5. Iterate over pixels and modify LSB
        # image.shape gives (height, width, channels)
        for row in image:
            for pixel in row:
                # Modify Red, Green, Blue values (0, 1, 2)
                for channel in range(3): 
                    if data_index < data_len:
                        # Get current pixel value binary
                        pixel_bin = self.to_binary(pixel[channel])
                        
                        # Replace last bit with message bit
                        # pixel_bin[:-1] takes all bits except last
                        # binary_message[data_index] is the new bit
                        new_bit = binary_message[data_index]
                        new_pixel_bin = pixel_bin[:-1] + new_bit
                        
                        # Update pixel with new binary value
                        pixel[channel] = int(new_pixel_bin, 2)
                        data_index += 1
                    else:
                        break
                if data_index >= data_len:
                    break
            if data_index >= data_len:
                break
                
        # 6. Save the result
        cv2.imwrite(output_path, image)
        print(f"[+] Saved encoded image to {output_path}")

    def decode(self, image_path):
        """Decodes the secret message from the stego-image"""
        print("[*] Decoding...")
        image = cv2.imread(image_path)
        binary_data = ""
        
        for row in image:
            for pixel in row:
                for channel in range(3):
                    binary_val = self.to_binary(pixel[channel])
                    binary_data += binary_val[-1] # Extract the last bit

        # Group bits into 8 (bytes)
        all_bytes = [binary_data[i: i+8] for i in range(0, len(binary_data), 8)]
        
        decoded_data = ""
        for byte in all_bytes:
            decoded_data += chr(int(byte, 2))
            # Check if we found the delimiter
            if decoded_data[-len(self.delimiter):] == self.delimiter:
                # Return data without the delimiter
                return decoded_data[:-len(self.delimiter)]
                
        return "No hidden message found (or delimiter missing)."
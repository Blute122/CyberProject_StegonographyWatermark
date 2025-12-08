import wave
import os

class AudioStego:
    
    def embed_audio(self, audio_path, message, output_path):
        """
        Hides a message into a .wav file using LSB Steganography.
        FIX: Skips the 44-byte WAV header.
        """
        if not os.path.exists(audio_path): raise ValueError("Audio file not found.")
        
        song = wave.open(audio_path, mode='rb')
        n_frames = song.getnframes()
        frames = song.readframes(n_frames)
        frame_bytes = bytearray(frames)
        
        # --- FIX 1: Define Header Size ---
        HEADER_SIZE = 44 
        
        message += "$$$" # Delimiter
        binary_msg = ''.join([format(ord(i), "08b") for i in message])
        
        print(f"[*] Embedding {len(binary_msg)} bits...")
        
        if len(binary_msg) > len(frame_bytes) - HEADER_SIZE:
            raise ValueError("Message too large for this audio file (after skipping header)!")
            
        # Embed bits into the LSB of audio bytes
        for i in range(len(binary_msg)):
            # --- FIX 2: Start embedding after the header ---
            byte_index = i + HEADER_SIZE
            
            # Clear last bit (AND 254) then set new bit (OR bit)
            frame_bytes[byte_index] = (frame_bytes[byte_index] & 254) | int(binary_msg[i])
            
        frame_modified = bytes(frame_bytes)
        
        # Write Output
        with wave.open(output_path, 'wb') as fd:
            fd.setparams(song.getparams())
            fd.writeframes(frame_modified)
            
        song.close()
        return len(binary_msg)

    def extract_audio(self, audio_path):
        """
        Extracts hidden LSB message from .wav file.
        FIX: Starts extraction after the 44-byte WAV header.
        """
        if not os.path.exists(audio_path): raise ValueError("Audio file not found.")
        
        song = wave.open(audio_path, mode='rb')
        n_frames = song.getnframes()
        frames = song.readframes(n_frames)
        frame_bytes = bytearray(frames)
        
        HEADER_SIZE = 44
        
        extracted_bits = ""
        delimiter = "$$$"
        delimiter_bin = ''.join([format(ord(i), "08b") for i in delimiter])
        
        print("[*] Scanning Audio Stream...")
        
        # Extract LSBs starting after header
        # Iterate over only the possible message space (after 44)
        for i in range(HEADER_SIZE, len(frame_bytes)):
            extracted_bits += str(frame_bytes[i] & 1)
            
            # Check for delimiter only when full bytes are available
            if (i - HEADER_SIZE) % 8 == 7 and len(extracted_bits) >= len(delimiter_bin):
                if extracted_bits.endswith(delimiter_bin):
                    # Convert bits to string
                    raw_bits = extracted_bits[:-len(delimiter_bin)]
                    chars = []
                    for b in range(0, len(raw_bits), 8):
                        byte = raw_bits[b:b+8]
                        chars.append(chr(int(byte, 2)))
                    return "".join(chars)
                    
        song.close()
        return "No hidden message found."
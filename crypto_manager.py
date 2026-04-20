import subprocess
import time
import os
import psutil
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

OPENSSL_PATH = r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe"

class CryptoManager:
    @staticmethod
    def get_memory_usage():
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)

    @staticmethod
    def encrypt_openssl_aes(input_file, output_file, password):
        mem_start = CryptoManager.get_memory_usage()
        start_time = time.time()
        cmd = [OPENSSL_PATH, "enc", "-aes-256-cbc", "-salt", "-in", input_file, 
               "-out", output_file, "-k", password, "-pbkdf2"]
        subprocess.run(cmd, check=True, capture_output=True)
        return time.time() - start_time, CryptoManager.get_memory_usage() - mem_start

    @staticmethod
    def decrypt_openssl_aes(input_file, output_file, password):
        cmd = [OPENSSL_PATH, "enc", "-d", "-aes-256-cbc", "-in", input_file, 
               "-out", output_file, "-k", password, "-pbkdf2"]
        subprocess.run(cmd, check=True)

    @staticmethod
    def encrypt_pyca_aes(input_file, output_file, key):
        mem_start = CryptoManager.get_memory_usage()
        start_time = time.time()
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()

        with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
            f_out.write(iv)
            padded_data = padder.update(f_in.read()) + padder.finalize()
            f_out.write(encryptor.update(padded_data) + encryptor.finalize())
        return time.time() - start_time, CryptoManager.get_memory_usage() - mem_start

    @staticmethod
    def generate_rsa_keys():
        subprocess.run([OPENSSL_PATH, "genpkey", "-algorithm", "RSA", "-out", "private.pem", 
                        "-pkeyopt", "rsa_keygen_bits:2048"], check=True, capture_output=True)
        subprocess.run([OPENSSL_PATH, "rsa", "-pubout", "-in", "private.pem", "-out", "public.pem"], 
                        check=True, capture_output=True)

    @staticmethod
    def encrypt_openssl_rsa(input_file, output_file, key_path):
        mem_start = CryptoManager.get_memory_usage()
        start_time = time.time()
        cmd = [OPENSSL_PATH, "pkeyutl", "-encrypt", "-pubin", "-inkey", key_path, 
               "-in", input_file, "-out", output_file]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Eroare OpenSSL: {e.stderr}")
            
        return time.time() - start_time, CryptoManager.get_memory_usage() - mem_start
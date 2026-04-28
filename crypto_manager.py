import base64
import json
import os
import shutil
import struct
import subprocess
import tempfile
import time
from pathlib import Path

import psutil
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

try:
    from Crypto.Cipher import AES as PyCryptoAES
    from Crypto.Cipher import PKCS1_OAEP
    from Crypto.Hash import SHA256 as PyCryptoSHA256
    from Crypto.Protocol.KDF import PBKDF2 as PyCryptoPBKDF2
    from Crypto.PublicKey import RSA as PyCryptoRSA
    from Crypto.Util.Padding import pad as pycrypto_pad, unpad as pycrypto_unpad

    HAS_PYCRYPTODOME = True
    PYCRYPTODOME_IMPORT_ERROR = None
except ImportError as exc:
    HAS_PYCRYPTODOME = False
    PYCRYPTODOME_IMPORT_ERROR = exc

DEFAULT_OPENSSL_PATH = Path(r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe")
PYCA_AES_MAGIC = b"PYAES1"
PYCRYPTODOME_AES_MAGIC = b"PCDAES1"
HYBRID_MAGIC = b"HYBRID1"


class CryptoManager:
    @staticmethod
    def get_memory_usage():
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)

    @staticmethod
    def has_pycryptodome():
        return HAS_PYCRYPTODOME

    @staticmethod
    def _ensure_pycryptodome_available():
        if not HAS_PYCRYPTODOME:
            raise RuntimeError(
                f"PyCryptodome nu este disponibil in mediu: {PYCRYPTODOME_IMPORT_ERROR}"
            )

    @staticmethod
    def compute_hash(file_path):
        digest = hashes.Hash(hashes.SHA256())
        with open(file_path, "rb") as handle:
            while True:
                chunk = handle.read(4096)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.finalize().hex()

    @staticmethod
    def _measure(operation):
        mem_start = CryptoManager.get_memory_usage()
        start = time.perf_counter()
        operation()
        elapsed = time.perf_counter() - start
        mem_used = max(0.0, CryptoManager.get_memory_usage() - mem_start)
        return elapsed, mem_used

    @staticmethod
    def _resolve_openssl_path():
        env_path = os.environ.get("OPENSSL_PATH")
        if env_path and Path(env_path).exists():
            return str(Path(env_path))
        if DEFAULT_OPENSSL_PATH.exists():
            return str(DEFAULT_OPENSSL_PATH)
        discovered = shutil.which("openssl")
        if discovered:
            return discovered
        raise FileNotFoundError(
            "OpenSSL nu a fost gasit. Seteaza variabila OPENSSL_PATH sau instaleaza OpenSSL."
        )

    @staticmethod
    def _run_openssl(arguments):
        command = [CryptoManager._resolve_openssl_path(), *arguments]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            error_message = result.stderr.strip() or result.stdout.strip() or "Comanda OpenSSL a esuat."
            raise RuntimeError(error_message)

    @staticmethod
    def _derive_key_from_password(password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390000,
            backend=default_backend(),
        )
        return kdf.derive(password.encode("utf-8"))

    @staticmethod
    def _write_hybrid_package(output_file, metadata, payload_file):
        metadata_bytes = json.dumps(metadata, ensure_ascii=True).encode("utf-8")
        with open(output_file, "wb") as destination:
            destination.write(HYBRID_MAGIC)
            destination.write(struct.pack(">I", len(metadata_bytes)))
            destination.write(metadata_bytes)
            with open(payload_file, "rb") as payload_handle:
                shutil.copyfileobj(payload_handle, destination)

    @staticmethod
    def _extract_hybrid_package(package_file, payload_output):
        with open(package_file, "rb") as source:
            magic = source.read(len(HYBRID_MAGIC))
            if magic != HYBRID_MAGIC:
                raise ValueError("Fisierul nu este un pachet RSA hibrid valid.")

            metadata_length_bytes = source.read(4)
            if len(metadata_length_bytes) != 4:
                raise ValueError("Antetul fisierului RSA este corupt.")

            metadata_length = struct.unpack(">I", metadata_length_bytes)[0]
            metadata_raw = source.read(metadata_length)
            metadata = json.loads(metadata_raw.decode("utf-8"))

            with open(payload_output, "wb") as payload_handle:
                shutil.copyfileobj(source, payload_handle)

        return metadata

    @staticmethod
    def encrypt_openssl_aes(input_file, output_file, password):
        def operation():
            CryptoManager._run_openssl(
                [
                    "enc",
                    "-aes-256-cbc",
                    "-salt",
                    "-pbkdf2",
                    "-in",
                    str(input_file),
                    "-out",
                    str(output_file),
                    "-k",
                    password,
                ]
            )

        return CryptoManager._measure(operation)

    @staticmethod
    def decrypt_openssl_aes(input_file, output_file, password):
        def operation():
            CryptoManager._run_openssl(
                [
                    "enc",
                    "-d",
                    "-aes-256-cbc",
                    "-pbkdf2",
                    "-in",
                    str(input_file),
                    "-out",
                    str(output_file),
                    "-k",
                    password,
                ]
            )

        return CryptoManager._measure(operation)

    @staticmethod
    def encrypt_pyca_aes(input_file, output_file, password):
        def operation():
            salt = os.urandom(16)
            iv = os.urandom(16)
            key = CryptoManager._derive_key_from_password(password, salt)
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            padder = padding.PKCS7(128).padder()

            with open(input_file, "rb") as source:
                plain_bytes = source.read()

            padded = padder.update(plain_bytes) + padder.finalize()
            encrypted = encryptor.update(padded) + encryptor.finalize()

            with open(output_file, "wb") as destination:
                destination.write(PYCA_AES_MAGIC)
                destination.write(salt)
                destination.write(iv)
                destination.write(encrypted)

        return CryptoManager._measure(operation)

    @staticmethod
    def decrypt_pyca_aes(input_file, output_file, password):
        def operation():
            with open(input_file, "rb") as source:
                magic = source.read(len(PYCA_AES_MAGIC))
                if magic != PYCA_AES_MAGIC:
                    raise ValueError("Fisierul nu este criptat in formatul PyCa AES asteptat.")

                salt = source.read(16)
                iv = source.read(16)
                encrypted = source.read()

            key = CryptoManager._derive_key_from_password(password, salt)
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            unpadder = padding.PKCS7(128).unpadder()

            padded = decryptor.update(encrypted) + decryptor.finalize()
            plain = unpadder.update(padded) + unpadder.finalize()

            with open(output_file, "wb") as destination:
                destination.write(plain)

        return CryptoManager._measure(operation)

    @staticmethod
    def encrypt_pycryptodome_aes(input_file, output_file, password):
        def operation():
            CryptoManager._ensure_pycryptodome_available()
            salt = os.urandom(16)
            iv = os.urandom(16)
            key = PyCryptoPBKDF2(
                password.encode("utf-8"),
                salt,
                dkLen=32,
                count=390000,
                hmac_hash_module=PyCryptoSHA256,
            )

            with open(input_file, "rb") as source:
                plain_bytes = source.read()

            cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_CBC, iv)
            encrypted = cipher.encrypt(pycrypto_pad(plain_bytes, PyCryptoAES.block_size))

            with open(output_file, "wb") as destination:
                destination.write(PYCRYPTODOME_AES_MAGIC)
                destination.write(salt)
                destination.write(iv)
                destination.write(encrypted)

        return CryptoManager._measure(operation)

    @staticmethod
    def decrypt_pycryptodome_aes(input_file, output_file, password):
        def operation():
            CryptoManager._ensure_pycryptodome_available()
            with open(input_file, "rb") as source:
                magic = source.read(len(PYCRYPTODOME_AES_MAGIC))
                if magic != PYCRYPTODOME_AES_MAGIC:
                    raise ValueError(
                        "Fisierul nu este criptat in formatul PyCryptodome AES asteptat."
                    )

                salt = source.read(16)
                iv = source.read(16)
                encrypted = source.read()

            key = PyCryptoPBKDF2(
                password.encode("utf-8"),
                salt,
                dkLen=32,
                count=390000,
                hmac_hash_module=PyCryptoSHA256,
            )
            cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_CBC, iv)
            plain_bytes = pycrypto_unpad(cipher.decrypt(encrypted), PyCryptoAES.block_size)

            with open(output_file, "wb") as destination:
                destination.write(plain_bytes)

        return CryptoManager._measure(operation)

    @staticmethod
    def generate_rsa_keys(private_path="private.pem", public_path="public.pem"):
        private_path = str(Path(private_path).resolve())
        public_path = str(Path(public_path).resolve())
        Path(private_path).parent.mkdir(parents=True, exist_ok=True)
        Path(public_path).parent.mkdir(parents=True, exist_ok=True)

        CryptoManager._run_openssl(
            [
                "genpkey",
                "-algorithm",
                "RSA",
                "-out",
                private_path,
                "-pkeyopt",
                "rsa_keygen_bits:2048",
            ]
        )
        CryptoManager._run_openssl(
            [
                "rsa",
                "-pubout",
                "-in",
                private_path,
                "-out",
                public_path,
            ]
        )

    @staticmethod
    def encrypt_openssl_rsa(input_file, output_file, key_path):
        def operation():
            aes_key = os.urandom(32)
            iv = os.urandom(16)

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                payload_path = temp_dir_path / "payload.bin"
                secret_path = temp_dir_path / "secret.bin"
                wrapped_secret_path = temp_dir_path / "secret.enc"

                with open(secret_path, "wb") as handle:
                    handle.write(aes_key + iv)

                CryptoManager._run_openssl(
                    [
                        "enc",
                        "-aes-256-cbc",
                        "-in",
                        str(input_file),
                        "-out",
                        str(payload_path),
                        "-K",
                        aes_key.hex(),
                        "-iv",
                        iv.hex(),
                    ]
                )

                CryptoManager._run_openssl(
                    [
                        "pkeyutl",
                        "-encrypt",
                        "-pubin",
                        "-inkey",
                        str(key_path),
                        "-in",
                        str(secret_path),
                        "-out",
                        str(wrapped_secret_path),
                        "-pkeyopt",
                        "rsa_padding_mode:oaep",
                        "-pkeyopt",
                        "rsa_oaep_md:sha256",
                    ]
                )

                wrapped_secret = base64.b64encode(wrapped_secret_path.read_bytes()).decode("ascii")
                metadata = {
                    "algorithm": "RSA",
                    "framework": "OpenSSL",
                    "mode": "hybrid",
                    "wrapped_key": wrapped_secret,
                }
                CryptoManager._write_hybrid_package(output_file, metadata, payload_path)

        return CryptoManager._measure(operation)

    @staticmethod
    def decrypt_openssl_rsa(input_file, output_file, key_path):
        def operation():
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                payload_path = temp_dir_path / "payload.bin"
                wrapped_secret_path = temp_dir_path / "secret.enc"
                secret_path = temp_dir_path / "secret.bin"

                metadata = CryptoManager._extract_hybrid_package(input_file, payload_path)
                wrapped_secret_path.write_bytes(base64.b64decode(metadata["wrapped_key"]))

                CryptoManager._run_openssl(
                    [
                        "pkeyutl",
                        "-decrypt",
                        "-inkey",
                        str(key_path),
                        "-in",
                        str(wrapped_secret_path),
                        "-out",
                        str(secret_path),
                        "-pkeyopt",
                        "rsa_padding_mode:oaep",
                        "-pkeyopt",
                        "rsa_oaep_md:sha256",
                    ]
                )

                secret_blob = secret_path.read_bytes()
                aes_key = secret_blob[:32]
                iv = secret_blob[32:48]
                if len(aes_key) != 32 or len(iv) != 16:
                    raise ValueError("Cheia RSA decriptata este invalida.")

                CryptoManager._run_openssl(
                    [
                        "enc",
                        "-d",
                        "-aes-256-cbc",
                        "-in",
                        str(payload_path),
                        "-out",
                        str(output_file),
                        "-K",
                        aes_key.hex(),
                        "-iv",
                        iv.hex(),
                    ]
                )

        return CryptoManager._measure(operation)

    @staticmethod
    def encrypt_pyca_rsa(input_file, output_file, key_path):
        def operation():
            with open(key_path, "rb") as key_handle:
                public_key = serialization.load_pem_public_key(
                    key_handle.read(), backend=default_backend()
                )

            aes_key = os.urandom(32)
            iv = os.urandom(16)
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            padder = padding.PKCS7(128).padder()

            with open(input_file, "rb") as source:
                plain_bytes = source.read()

            padded = padder.update(plain_bytes) + padder.finalize()
            encrypted_payload = encryptor.update(padded) + encryptor.finalize()
            wrapped_secret = public_key.encrypt(
                aes_key + iv,
                asym_padding.OAEP(
                    mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            with tempfile.NamedTemporaryFile(delete=False) as payload_handle:
                payload_handle.write(encrypted_payload)
                payload_path = payload_handle.name

            try:
                metadata = {
                    "algorithm": "RSA",
                    "framework": "PyCa",
                    "mode": "hybrid",
                    "wrapped_key": base64.b64encode(wrapped_secret).decode("ascii"),
                }
                CryptoManager._write_hybrid_package(output_file, metadata, payload_path)
            finally:
                Path(payload_path).unlink(missing_ok=True)

        return CryptoManager._measure(operation)

    @staticmethod
    def decrypt_pyca_rsa(input_file, output_file, key_path):
        def operation():
            with open(key_path, "rb") as key_handle:
                private_key = serialization.load_pem_private_key(
                    key_handle.read(), password=None, backend=default_backend()
                )

            with tempfile.NamedTemporaryFile(delete=False) as payload_handle:
                payload_path = payload_handle.name

            try:
                metadata = CryptoManager._extract_hybrid_package(input_file, payload_path)
                wrapped_secret = base64.b64decode(metadata["wrapped_key"])
                secret_blob = private_key.decrypt(
                    wrapped_secret,
                    asym_padding.OAEP(
                        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None,
                    ),
                )

                aes_key = secret_blob[:32]
                iv = secret_blob[32:48]
                if len(aes_key) != 32 or len(iv) != 16:
                    raise ValueError("Cheia RSA decriptata este invalida.")

                cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
                decryptor = cipher.decryptor()
                unpadder = padding.PKCS7(128).unpadder()

                encrypted_payload = Path(payload_path).read_bytes()
                padded = decryptor.update(encrypted_payload) + decryptor.finalize()
                plain_bytes = unpadder.update(padded) + unpadder.finalize()

                with open(output_file, "wb") as destination:
                    destination.write(plain_bytes)
            finally:
                Path(payload_path).unlink(missing_ok=True)

        return CryptoManager._measure(operation)

    @staticmethod
    def encrypt_pycryptodome_rsa(input_file, output_file, key_path):
        def operation():
            CryptoManager._ensure_pycryptodome_available()
            with open(key_path, "rb") as key_handle:
                public_key = PyCryptoRSA.import_key(key_handle.read())

            aes_key = os.urandom(32)
            iv = os.urandom(16)
            cipher = PyCryptoAES.new(aes_key, PyCryptoAES.MODE_CBC, iv)

            with open(input_file, "rb") as source:
                plain_bytes = source.read()

            encrypted_payload = cipher.encrypt(pycrypto_pad(plain_bytes, PyCryptoAES.block_size))
            wrapped_secret = PKCS1_OAEP.new(public_key, hashAlgo=PyCryptoSHA256).encrypt(
                aes_key + iv
            )

            with tempfile.NamedTemporaryFile(delete=False) as payload_handle:
                payload_handle.write(encrypted_payload)
                payload_path = payload_handle.name

            try:
                metadata = {
                    "algorithm": "RSA",
                    "framework": "PyCryptodome",
                    "mode": "hybrid",
                    "wrapped_key": base64.b64encode(wrapped_secret).decode("ascii"),
                }
                CryptoManager._write_hybrid_package(output_file, metadata, payload_path)
            finally:
                Path(payload_path).unlink(missing_ok=True)

        return CryptoManager._measure(operation)

    @staticmethod
    def decrypt_pycryptodome_rsa(input_file, output_file, key_path):
        def operation():
            CryptoManager._ensure_pycryptodome_available()
            with open(key_path, "rb") as key_handle:
                private_key = PyCryptoRSA.import_key(key_handle.read())

            with tempfile.NamedTemporaryFile(delete=False) as payload_handle:
                payload_path = payload_handle.name

            try:
                metadata = CryptoManager._extract_hybrid_package(input_file, payload_path)
                wrapped_secret = base64.b64decode(metadata["wrapped_key"])
                secret_blob = PKCS1_OAEP.new(
                    private_key, hashAlgo=PyCryptoSHA256
                ).decrypt(wrapped_secret)

                aes_key = secret_blob[:32]
                iv = secret_blob[32:48]
                if len(aes_key) != 32 or len(iv) != 16:
                    raise ValueError("Cheia RSA decriptata este invalida.")

                encrypted_payload = Path(payload_path).read_bytes()
                cipher = PyCryptoAES.new(aes_key, PyCryptoAES.MODE_CBC, iv)
                plain_bytes = pycrypto_unpad(
                    cipher.decrypt(encrypted_payload), PyCryptoAES.block_size
                )

                with open(output_file, "wb") as destination:
                    destination.write(plain_bytes)
            finally:
                Path(payload_path).unlink(missing_ok=True)

        return CryptoManager._measure(operation)

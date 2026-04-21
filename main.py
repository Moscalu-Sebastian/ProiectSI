from pathlib import Path

import tkinter as tk

from crypto_manager import CryptoManager
from database import get_or_create_algoritm, upsert_key


def init_database():
    print("Se initializeaza baza de date...")

    get_or_create_algoritm("AES", "Simetric")
    get_or_create_algoritm("RSA", "Asimetric")

    upsert_key("Parola_AES", "pass123", "AES", "secret")

    private_path = Path("private.pem").resolve()
    public_path = Path("public.pem").resolve()

    if not private_path.exists() or not public_path.exists():
        print("Se genereaza perechea de chei RSA implicita...")
        CryptoManager.generate_rsa_keys(private_path, public_path)

    upsert_key("RSA_Public_Default", str(public_path), "RSA", "public")
    upsert_key("RSA_Private_Default", str(private_path), "RSA", "private")

    print("Baza de date este gata.")


def main():
    init_database()

    from gui import CryptoApp

    root = tk.Tk()
    CryptoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

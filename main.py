import os
from database import session, Algoritm, Cheie, create_record
from crypto_manager import CryptoManager

def init_database():
    print("Se initializeaza baza de date...")
    
    for n, t in [("AES", "Simetric"), ("RSA", "Asimetric")]:
        if not session.query(Algoritm).filter_by(nume=n).first():
            create_record(Algoritm(nume=n, tip=t))
    
    aes_ref = session.query(Algoritm).filter_by(nume="AES").first()
    rsa_ref = session.query(Algoritm).filter_by(nume="RSA").first()

    if not session.query(Cheie).filter_by(nume_cheie="Parola_AES").first():
        create_record(Cheie(nume_cheie="Parola_AES", path_cheie="pass123", algoritm_id=aes_ref.id))

    if not session.query(Cheie).filter_by(nume_cheie="RSA_Public").first():
        print("Se genereaza perechea de chei RSA...")
        CryptoManager.generate_rsa_keys()
        create_record(Cheie(nume_cheie="RSA_Public", path_cheie="public.pem", algoritm_id=rsa_ref.id))

    print("Baza de date este gata!")

if __name__ == "__main__":
    init_database()
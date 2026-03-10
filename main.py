import os
from database import session, Algoritm, Cheie, FisierManagement, Performanta
from crypto_manager import CryptoManager

def init_db():
    for n, t in [("AES", "Simetric"), ("RSA", "Asimetric")]:
        if not session.query(Algoritm).filter_by(nume=n).first():
            session.add(Algoritm(nume=n, tip=t))
    session.commit()

def run_full_project():
    init_db()
    aes_ref = session.query(Algoritm).filter_by(nume="AES").first()
    rsa_ref = session.query(Algoritm).filter_by(nume="RSA").first()

    f_mare = "date_simetrice.txt"
    with open(f_mare, "w") as f: f.write("Date importante " * 10000)
    
    print("Executie AES OpenSSL...")
    t_ssl, m_ssl = CryptoManager.encrypt_openssl_aes(f_mare, "date.enc_ssl", "pass123")
    
    print("Executie AES PyCa...")
    t_py, m_py = CryptoManager.encrypt_pyca_aes(f_mare, "date.enc_pyca", b'01234567890123456789012345678901')

    fisier_db = FisierManagement(nume_original=f_mare, path_criptat="date.enc_ssl", dimensiune_bytes=os.path.getsize(f_mare))
    session.add(fisier_db)
    session.commit()

    perf_data = [
        Performanta(framework="OpenSSL", operatie="Criptare", timp_executie=t_ssl, memorie_utilizata=m_ssl, fisier_id=fisier_db.id, algoritm_id=aes_ref.id),
        Performanta(framework="PyCa", operatie="Criptare", timp_executie=t_py, memorie_utilizata=m_py, fisier_id=fisier_db.id, algoritm_id=aes_ref.id)
    ]
    session.add_all(perf_data)

    print("Decriptare fisier OpenSSL pentru verificare...")
    CryptoManager.decrypt_openssl_aes("date.enc_ssl", "reconstituire.txt", "pass123")

    print("Generare chei si criptare RSA...")
    CryptoManager.generate_rsa_keys()
    session.add(Cheie(nume_cheie="RSA_Public", path_cheie="public.pem", algoritm_id=rsa_ref.id))
    
    f_mic = "secret_rsa.txt"
    with open(f_mic, "w") as f: f.write("Top Secret RSA")
    t_rsa, m_rsa = CryptoManager.encrypt_openssl_rsa(f_mic, "secret.rsa_enc")
    
    session.add(Performanta(framework="OpenSSL", operatie="Criptare RSA", timp_executie=t_rsa, memorie_utilizata=m_rsa, fisier_id=fisier_db.id, algoritm_id=rsa_ref.id))
    
    session.commit()
    print("\n--- RAPORT FINAL ---")
    print(f"AES OpenSSL: {t_ssl:.4f}s | Memorie: {m_ssl:.4f}MB")
    print(f"AES PyCa:    {t_py:.4f}s | Memorie: {m_py:.4f}MB")
    print(f"RSA OpenSSL: {t_rsa:.4f}s | Memorie: {m_rsa:.4f}MB")
    print("\nToate cerintele au fost indeplinite si salvate in DB.")

if __name__ == "__main__":
    run_full_project()
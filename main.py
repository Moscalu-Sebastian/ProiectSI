import os
from database import (
    session, Algoritm, Cheie, FisierManagement, Performanta,
    create_record, read_all, update_performance_time, delete_record
)
from crypto_manager import CryptoManager

def db_interaction_tests():
    """Teste simple pentru a verifica operatiile CRUD in DB."""
    print("\n--- INCEPUT TESTE CRUD DB ---")
    
    test_alg = create_record(Algoritm(nume="ALG_TEST", tip="Simetric"))
    print(f"[CREATE] Am adaugat algoritmul de test: {test_alg.nume}")
    
    toate_algs = read_all(Algoritm)
    print(f"[READ] Numar total algoritmi in DB: {len(toate_algs)}")
    
    dummy_perf = create_record(Performanta(framework="Test", operatie="Test", timp_executie=1.0, memorie_utilizata=0.1, algoritm_id=test_alg.id))
    updated_perf = update_performance_time(dummy_perf.id, 5.55)
    print(f"[UPDATE] Timp actualizat in DB: {updated_perf.timp_executie}s")
    
    delete_record(test_alg)
    delete_record(dummy_perf)
    print("[DELETE] Inregistrarile de test au fost sterse cu succes.")
    print("--- SFARSIT TESTE CRUD DB ---\n")

def run_full_project():
    for n, t in [("AES", "Simetric"), ("RSA", "Asimetric")]:
        if not session.query(Algoritm).filter_by(nume=n).first():
            create_record(Algoritm(nume=n, tip=t))
    
    aes_ref = session.query(Algoritm).filter_by(nume="AES").first()
    rsa_ref = session.query(Algoritm).filter_by(nume="RSA").first()

    f_mare = "date_simetrice.txt"
    with open(f_mare, "w") as f: f.write("Date importante " * 10000)
    
    print("Executie AES OpenSSL...")
    t_ssl, m_ssl = CryptoManager.encrypt_openssl_aes(f_mare, "date.enc_ssl", "pass123")
    
    print("Executie AES PyCa...")
    t_py, m_py = CryptoManager.encrypt_pyca_aes(f_mare, "date.enc_pyca", b'01234567890123456789012345678901')

    fisier_db = create_record(FisierManagement(nume_original=f_mare, path_criptat="date.enc_ssl", dimensiune_bytes=os.path.getsize(f_mare)))
    
    create_record(Performanta(framework="OpenSSL", operatie="Criptare", timp_executie=t_ssl, memorie_utilizata=m_ssl, fisier_id=fisier_db.id, algoritm_id=aes_ref.id))
    create_record(Performanta(framework="PyCa", operatie="Criptare", timp_executie=t_py, memorie_utilizata=m_py, fisier_id=fisier_db.id, algoritm_id=aes_ref.id))

    print("Decriptare OpenSSL pentru verificare...")
    CryptoManager.decrypt_openssl_aes("date.enc_ssl", "reconstituire.txt", "pass123")

    print("Generare chei si criptare RSA...")
    CryptoManager.generate_rsa_keys()
    create_record(Cheie(nume_cheie="RSA_Public", path_cheie="public.pem", algoritm_id=rsa_ref.id))
    
    f_mic = "secret_rsa.txt"
    with open(f_mic, "w") as f: f.write("Top Secret RSA")
    t_rsa, m_rsa = CryptoManager.encrypt_openssl_rsa(f_mic, "secret.rsa_enc")
    
    create_record(Performanta(framework="OpenSSL", operatie="Criptare RSA", timp_executie=t_rsa, memorie_utilizata=m_rsa, fisier_id=fisier_db.id, algoritm_id=rsa_ref.id))
    
    print("\n--- RAPORT FINAL ---")
    print(f"AES OpenSSL: {t_ssl:.4f}s | Memorie: {m_ssl:.4f}MB")
    print(f"AES PyCa:    {t_py:.4f}s | Memorie: {m_py:.4f}MB")
    print(f"RSA OpenSSL: {t_rsa:.4f}s | Memorie: {m_rsa:.4f}MB")
    print("\nProiectul a fost executat complet. Datele sunt salvate in DB.")

if __name__ == "__main__":
    db_interaction_tests()
    run_full_project()
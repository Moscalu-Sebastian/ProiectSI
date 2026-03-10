# Sistem Local de Management al Cheilor și Analiză de Performanță

## 1. Descrierea Proiectului
Acest proiect reprezintă o soluție software pentru gestionarea securizată a fișierelor și a cheilor de criptare, punând un accent deosebit pe **analiza performanței**. Sistemul permite utilizatorului să compare două abordări diferite: utilizarea unui instrument de sistem (OpenSSL) și a unei librării native de programare (Cryptography.io).

### Cerințe Îndeplinite:
* **Management DB:** Implementare sistem de baze de date pentru evidența fișierelor și cheilor.
* **Algoritmi multipli:** Suport pentru criptare simetrică (AES) și asimetrică (RSA).
* **Analiză Performanță:** Monitorizarea timpului de execuție și a consumului de memorie (RAM).
* **Management Fișiere:** Flux complet de Criptare -> Salvare -> Decriptare (Reconstituire).

---

## 2. Arhitectura Sistemului
Proiectul urmează o structură modulară pentru a separa logica de business de cea de stocare:

* **`database.py`**: Stratul de persistență (ORM) care gestionează baza de date SQLite.
* **`crypto_manager.py`**: Motorul criptografic ce încapsulează apelurile către OpenSSL și PyCa.
* **`main.py`**: Orchestratorul aplicației care execută testele și generează rapoartele.



---

## 3. Entități Bază de Date (Modele)
Schema bazei de date `key_manager.db` este definită prin următoarele tabele:

1.  **Algoritm**: Reține numele (AES, RSA) și tipul (Simetric, Asimetric).
2.  **Cheie**: Managementul locației cheilor (ex: `public.pem`, `private.pem`).
3.  **FisierManagement**: Monitorizează fișierele originale și cele rezultate în urma criptării.
4.  **Performanta**: Tabelul de analiză unde se salvează timpul (secunde) și memoria (MB) pentru fiecare operație.



---

## 4. Analiza de Performanță
Sistemul măsoară doi indicatori critici:
1.  **Timp de execuție**: Calculat folosind librăria `time`, măsurând latența între startul și finalul funcției.
2.  **Consum Memorie**: Calculat prin `psutil`, determinând diferența de memorie RAM utilizată în timpul procesului de criptare.

---

## 5. Instrucțiuni de Utilizare

### Instalare Dependențe
Asigurați-vă că aveți Python instalat, apoi rulați:
```bash
pip install sqlalchemy cryptography psutil
python .\main.py
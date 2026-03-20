# Sistem Local de Management al Cheilor și Analiză de Performanță

## 1. Descrierea Proiectului
Acest proiect reprezintă o soluție software integrată pentru gestionarea securizată a fișierelor și a cheilor de criptare, cu un accent deosebit pe **analiza comparativă a performanței**. Sistemul permite utilizatorului să compare două abordări distincte: utilizarea unui instrument de sistem via CLI (**OpenSSL**) și a unei librării native Python (**Cryptography.io / PyCa**).

### Cerințe Implementate 100%:
* **Management DB Complet:** Sistem de baze de date pentru evidența fișierelor, cheilor și performanțelor, cu suport total pentru operații **CRUD** (Create, Read, Update, Delete).
* **Algoritmi Multipli:** Implementare pentru criptare simetrică (**AES-256-CBC**) și asimetrică (**RSA-2048**).
* **Analiză Performanță Avansată:** Monitorizarea timpului de execuție (latență) și a consumului de memorie RAM (delta RSS).
* **Management Fișiere:** Flux complet: Creare date -> Criptare -> Salvare Metadate -> Decriptare (Verificare Integritate).

---

## 2. Arhitectura Sistemului
Diagrama de mai jos ilustrează fluxul logic și interacțiunea dintre modulele sistemului:

![Arhitectura Sistemului](arhitecture-app.png)

Proiectul utilizează o structură modulară pentru separarea responsabilităților:
* **`database.py` (Persistence Layer):** Gestionează modelele ORM (SQLAlchemy) și interacțiunea cu baza de date SQLite (`key_manager.db`). Include funcțiile CRUD: `create_record`, `read_all`, `update_performance_time` și `delete_record`.
* **`crypto_manager.py` (Cryptographic Engine):** Încapsulează logica de criptare/decriptare. Folosește `subprocess` pentru OpenSSL și funcții native pentru PyCa.
* **`main.py` (Application Orchestrator):** Coordonează execuția testelor DB, inițializează algoritmii și rulează fluxul principal de criptare și raportare.

---

## 3. Entități Bază de Date (Modele ORM)
Schema bazei de date este compusă din următoarele tabele corelate:
1. **`Algoritm`**: Reține numele algoritmului (AES, RSA) și tipul acestuia (Simetric, Asimetric).
2. **`Cheie`**: Gestionează locația cheilor (ex: `public.pem`) și legătura cu algoritmul aferent.
3. **`FisierManagement`**: Monitorizează fișierele originale, căile celor criptate și dimensiunea acestora în bytes.
4. **`Performanta`**: Tabel centralizator pentru analize, stocând framework-ul utilizat, operația, timpul de execuție și memoria utilizată.

---

## 4. Analiza de Performanță și Testare
Sistemul validează performanța prin doi indicatori critici:
1. **Timp de execuție:** Măsurat cu librăria `time`, calculând diferența dintre startul și finalul operațiunii.
2. **Consum Memorie:** Utilizând `psutil`, se determină impactul asupra memoriei RAM (în MB) în timpul procesării datelor.

### Teste CRUD (DB Interaction):
La fiecare rulare a scriptului `main.py`, sistemul execută automat un set de teste pentru a verifica integritatea DB:
* **Create:** Adăugarea unui algoritm de test.
* **Read:** Verificarea existenței înregistrărilor.
* **Update:** Modificarea unei valori de performanță.
* **Delete:** Curățarea datelor de test.

---

## 5. Instrucțiuni de Utilizare

### Instalare Dependențe
```bash
pip install sqlalchemy cryptography psutil
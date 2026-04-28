# Sistem Local de Management al Cheilor de Criptare

## Descriere
Acest proiect este o aplicatie locala pentru:

- managementul cheilor de criptare;
- managementul fisierelor criptate si decriptate;
- compararea performantelor intre mai multe framework-uri de criptare;
- stocarea metadatelor si a rezultatelor in baza de date.

Aplicatia are interfata grafica realizata cu `tkinter`, foloseste o baza de date locala `SQLite` prin `SQLAlchemy` si permite criptarea/decriptarea fisierelor folosind:

- `OpenSSL`
- `PyCa / cryptography`
- `PyCryptodome`

Sunt suportati cel putin:

- un algoritm simetric: `AES-256-CBC`
- un algoritm asimetric: `RSA-2048`

## Obiectivul proiectului
Scopul proiectului este sa ofere un sistem local prin care utilizatorul poate:

- selecta un fisier pentru test;
- alege algoritmul de criptare;
- alege framework-ul folosit;
- selecta sau adauga o cheie din baza de date;
- cripta si decripta fisierul;
- verifica integritatea prin hash;
- compara timpul si memoria consumata intre framework-uri.

## Functionalitati principale

### 1. Management algoritmi
Aplicatia initializeaza automat in baza de date algoritmii:

- `AES` - algoritm simetric
- `RSA` - algoritm asimetric

### 2. Management chei
Aplicatia permite:

- salvarea unei chei AES in baza de date;
- importul unei chei RSA publice sau private din fisiere `.pem`;
- generarea unei perechi noi de chei RSA;
- afisarea cheilor existente din baza de date.

Cheile sunt clasificate in functie de tip:

- `secret` pentru AES
- `public` pentru criptare RSA
- `private` pentru decriptare RSA

### 3. Management fisiere
Aplicatia permite:

- selectarea unui fisier existent;
- crearea rapida a unui fisier text pentru test;
- inregistrarea automata a fisierului in baza de date;
- stergerea inregistrarilor asociate unui fisier din baza de date.

Pentru fiecare fisier pot fi retinute:

- calea fisierului;
- dimensiunea in octeti;
- statusul: `Necriptat`, `Criptat`, `Decriptat`;
- hash-ul original;
- hash-ul curent;
- framework-ul si algoritmul folosit la ultima operatie.

### 4. Criptare si decriptare
Aplicatia poate executa:

- criptare AES cu `OpenSSL`
- decriptare AES cu `OpenSSL`
- criptare AES cu `PyCa`
- decriptare AES cu `PyCa`
- criptare AES cu `PyCryptodome`
- decriptare AES cu `PyCryptodome`
- criptare RSA cu `OpenSSL`
- decriptare RSA cu `OpenSSL`
- criptare RSA cu `PyCa`
- decriptare RSA cu `PyCa`
- criptare RSA cu `PyCryptodome`
- decriptare RSA cu `PyCryptodome`

Pentru `RSA`, proiectul foloseste un mecanism hibrid:

- fisierul este criptat efectiv cu o cheie simetrica AES generata temporar;
- cheia AES este apoi criptata cu RSA;
- rezultatul este stocat intr-un pachet hibrid care poate fi decriptat ulterior.

Aceasta abordare permite folosirea RSA si pentru fisiere mai mari, nu doar pentru mesaje foarte scurte.

### 5. Verificare integritate
Aplicatia calculeaza hash `SHA-256` pentru fisiere si permite:

- salvarea hash-ului in baza de date;
- verificarea fisierului rezultat dupa decriptare;
- confirmarea integritatii prin compararea hash-ului rezultat cu hash-ul original.

### 6. Analiza de performanta
Pentru fiecare operatie de criptare sau decriptare sunt masurate si salvate in baza de date:

- `timp_executie` - timpul total al operatiei;
- `timp_per_octet` - timpul raportat la dimensiunea fisierului;
- `memorie_utilizata` - memoria RAM consumata;
- `viteza_mb_s` - viteza de procesare in MB/s;
- `hash_verificat` - daca integritatea a fost confirmata sau nu;
- `detalii` - informatii suplimentare despre operatie.

Aceasta parte este utila pentru comparatia dintre:

- `OpenSSL`
- `PyCa`
- `PyCryptodome`

## Interfata grafica
Interfata este dezvoltata in `tkinter` si contine:

- zona de selectare fisier;
- configurare framework, algoritm si cheie;
- administrare chei;
- butoane pentru criptare, decriptare si verificare hash;
- tabele pentru fisiere, performante si chei;
- mesaje de status si ferestre de debug.

Utilizatorul poate face dublu-click in tabele pentru a selecta rapid un fisier sau o cheie.

## Denumirea fisierelor generate
Fisierelor generate li se atribuie nume clare si stabile, bazate pe fisierul original.

Formatul este:

- criptare: `nume_fisier__criptat__framework__algoritm.enc`
- decriptare: `nume_fisier__decriptat__framework__algoritm.extensie`

Exemple:

- `test.txt` -> `test__criptat__openssl__aes.enc`
- `test.txt` -> `test__decriptat__openssl__aes.txt`
- `test.txt` -> `test__criptat__pycryptodome__rsa.enc`

Astfel se evita formarea unor nume foarte lungi dupa mai multe operatii succesive.

## Baza de date
Aplicatia foloseste fisierul local:

- `key_manager.db`

### Tabele principale

#### `algoritmi`
Contine algoritmii disponibili:

- `id`
- `nume`
- `tip`

#### `chei`
Contine cheile salvate:

- `id`
- `nume_cheie`
- `path_cheie`
- `tip_cheie`
- `algoritm_id`

Pentru AES, `path_cheie` retine parola/secretul.
Pentru RSA, `path_cheie` retine calea catre fisierul `.pem`.

#### `fisiere`
Contine fisierele urmarite de aplicatie:

- `id`
- `nume_original`
- `path_criptat`
- `dimensiune_bytes`
- `status`
- `hash_original`
- `hash_curent`
- `fisier_sursa_id`
- `framework_ultim`
- `algoritm_ultim`

#### `performante`
Contine rezultatele operatiilor:

- `id`
- `framework`
- `operatie`
- `timp_executie`
- `timp_per_octet`
- `memorie_utilizata`
- `viteza_mb_s`
- `fisier_id`
- `algoritm_nume`
- `cheie_id`
- `hash_verificat`
- `detalii`

## Structura proiectului

```text
ProiectSI/
|-- main.py
|-- gui.py
|-- crypto_manager.py
|-- database.py
|-- README.md
|-- key_manager.db
|-- public.pem
|-- private.pem
|-- arhitecture-app.png
|-- myenv/
```

### Rolul fisierelor

- `main.py` - initializeaza baza de date, cheile implicite si porneste aplicatia;
- `gui.py` - implementeaza interfata grafica si fluxul principal al utilizatorului;
- `crypto_manager.py` - contine logica de criptare, decriptare, hash si integrarea cu framework-urile;
- `database.py` - defineste modelele ORM si operatiile de persistenta;
- `key_manager.db` - baza de date locala SQLite;
- `public.pem` / `private.pem` - cheile RSA implicite.

## Arhitectura
Diagrama generala a aplicatiei este disponibila mai jos:

![Arhitectura Sistemului](arhitecture-app.png)

Fluxul logic este:

1. utilizatorul selecteaza sau creeaza un fisier;
2. fisierul este inregistrat in baza de date;
3. utilizatorul selecteaza algoritmul, framework-ul si cheia;
4. aplicatia executa operatia de criptare sau decriptare;
5. sunt calculate metadatele si indicatorii de performanta;
6. rezultatele sunt salvate in baza de date si afisate in GUI.

## Framework-uri suportate

### 1. OpenSSL
Avantaje:

- implementare consacrata;
- foarte bun pentru comparatii de performanta;
- foloseste executabilul de sistem.

In proiect este folosit pentru:

- AES prin `openssl enc`
- RSA prin `openssl pkeyutl`

### 2. PyCa / cryptography
Avantaje:

- integrare nativa in Python;
- API modern;
- bun pentru comparatie cu OpenSSL.

In proiect este folosit pentru:

- AES in Python
- RSA hibrid in Python

### 3. PyCryptodome
Avantaje:

- biblioteca Python dedicata operatiilor criptografice;
- ofera o a treia perspectiva pentru analiza comparativa;
- suport clar pentru AES si RSA.

In proiect este folosit pentru:

- AES in Python
- RSA hibrid in Python

## Tehnologii utilizate

- `Python`
- `Tkinter`
- `SQLite`
- `SQLAlchemy`
- `OpenSSL`
- `cryptography`
- `PyCryptodome`
- `psutil`

## Cerinte de rulare

### Dependinte Python
Instalare:

```bash
pip install sqlalchemy cryptography psutil pycryptodome
```

### OpenSSL
Aplicatia are nevoie de `OpenSSL` instalat local.

Implicit cauta executabilul in:

```text
C:\Program Files\OpenSSL-Win64\bin\openssl.exe
```

Daca OpenSSL este instalat in alta locatie, se poate seta variabila de mediu:

```powershell
$env:OPENSSL_PATH="C:\cale\catre\openssl.exe"
```

## Rulare
Daca folosesti mediul virtual deja existent in proiect:

```powershell
.\myenv\Scripts\python.exe main.py
```

Sau, daca ai activat mediul virtual:

```powershell
python main.py
```

La pornire, aplicatia:

- initializeaza baza de date;
- adauga algoritmii impliciti;
- adauga cheia AES implicita `Parola_AES`;
- genereaza, daca lipsesc, cheile RSA implicite;
- porneste interfata grafica.

## Mod de utilizare

### Scenariu tipic
1. Deschide aplicatia.
2. Selecteaza un fisier existent sau creeaza un fisier text nou.
3. Alege framework-ul: `OpenSSL`, `PyCa` sau `PyCryptodome`.
4. Alege algoritmul: `AES` sau `RSA`.
5. Alege cheia potrivita din baza de date.
6. Apasa `Cripteaza`.
7. Selecteaza fisierul rezultat si apasa `Decripteaza`.
8. Foloseste `Verifica hash` pentru a verifica integritatea.
9. Consulta tabelul de performante pentru comparatie.

### Reguli importante
- pentru `AES` trebuie selectata o cheie de tip `secret`;
- pentru `RSA` la criptare trebuie folosita o cheie `public`;
- pentru `RSA` la decriptare trebuie folosita o cheie `private`.

## Ce demonstreaza proiectul
Acest proiect demonstreaza:

- integrarea dintre GUI, baza de date si engine criptografic;
- apelarea OpenSSL din Python;
- compararea intre mai multe framework-uri de criptare;
- managementul cheilor si fisierelor criptate;
- validarea integritatii prin hash;
- analiza de performanta la nivel de timp, memorie, viteza si timp per octet.

## Posibile extensii
Proiectul poate fi extins usor cu:

- export al rezultatelor din baza de date;
- grafice comparative pentru performanta;
- suport pentru algoritmi suplimentari;
- filtrare si cautare avansata in interfata;
- buton dedicat pentru curatarea fisierelor generate.

## Concluzie
Proiectul realizeaza un sistem local complet pentru managementul cheilor de criptare si al fisierelor criptate/decriptate, cu suport pentru mai multe framework-uri si cu analiza comparativa de performanta. Este potrivit pentru cerintele unui proiect universitar care combina:

- baze de date;
- criptografie;
- interfata grafica;
- masuratori de performanta;
- integrare cu instrumente externe precum OpenSSL.

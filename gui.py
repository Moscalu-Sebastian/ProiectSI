import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from crypto_manager import CryptoManager
from database import (
    Algoritm,
    Cheie,
    FisierManagement,
    Performanta,
    find_file_by_path,
    list_keys,
    record_performance,
    register_managed_file,
    session,
    upsert_key,
)


class CryptoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem Management Chei si Fisiere Criptate")
        self.root.geometry("1180x760")
        self.root.minsize(1050, 680)

        self.filepath_var = tk.StringVar()
        self.algoritm_var = tk.StringVar()
        self.cheie_var = tk.StringVar()
        self.framework_var = tk.StringVar(value="OpenSSL")
        self.status_var = tk.StringVar(
            value="Aplicatia este pregatita pentru criptare, decriptare si analiza de performanta."
        )

        self.key_options = {}

        self.setup_ui()
        self.incarca_date_db()

    def setup_ui(self):
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        frame_fisier = ttk.LabelFrame(container, text="1. Selectare Fisier", padding=10)
        frame_fisier.pack(fill="x", pady=(0, 8))

        ttk.Entry(frame_fisier, textvariable=self.filepath_var, width=92, state="readonly").grid(
            row=0, column=0, padx=5, sticky="ew"
        )
        ttk.Button(frame_fisier, text="Cauta", command=self.alege_fisier).grid(row=0, column=1, padx=4)
        ttk.Button(frame_fisier, text="Scrie Text", command=self.creeaza_fisier_text).grid(
            row=0, column=2, padx=4
        )
        ttk.Button(frame_fisier, text="Sterge din DB", command=self.sterge_fisier_db).grid(
            row=0, column=3, padx=4
        )
        frame_fisier.columnconfigure(0, weight=1)

        frame_setari = ttk.LabelFrame(container, text="2. Configurare Criptare", padding=10)
        frame_setari.pack(fill="x", pady=(0, 8))

        ttk.Label(frame_setari, text="Framework:").grid(row=0, column=0, sticky="w", pady=4)
        framework_values = ["OpenSSL", "PyCa"]
        if CryptoManager.has_pycryptodome():
            framework_values.append("PyCryptodome")
        self.combo_framework = ttk.Combobox(
            frame_setari,
            textvariable=self.framework_var,
            state="readonly",
            values=framework_values,
            width=20,
        )
        self.combo_framework.grid(row=0, column=1, padx=5, pady=4, sticky="w")

        ttk.Label(frame_setari, text="Algoritm:").grid(row=0, column=2, sticky="w", pady=4)
        self.combo_alg = ttk.Combobox(frame_setari, textvariable=self.algoritm_var, state="readonly", width=20)
        self.combo_alg.grid(row=0, column=3, padx=5, pady=4, sticky="w")
        self.combo_alg.bind("<<ComboboxSelected>>", self._on_algoritm_changed)

        ttk.Label(frame_setari, text="Cheie DB:").grid(row=0, column=4, sticky="w", pady=4)
        self.combo_cheie = ttk.Combobox(
            frame_setari, textvariable=self.cheie_var, state="readonly", width=34
        )
        self.combo_cheie.grid(row=0, column=5, padx=5, pady=4, sticky="w")

        ttk.Button(frame_setari, text="Reincarca date", command=self.incarca_date_db).grid(
            row=0, column=6, padx=5, pady=4
        )

        frame_chei = ttk.LabelFrame(container, text="3. Administrare Chei", padding=10)
        frame_chei.pack(fill="x", pady=(0, 8))

        ttk.Button(frame_chei, text="Adauga cheie AES", command=self.adauga_cheie_aes).pack(
            side="left", padx=5
        )
        ttk.Button(frame_chei, text="Importa cheie RSA", command=self.importa_cheie_rsa).pack(
            side="left", padx=5
        )
        ttk.Button(frame_chei, text="Genereaza pereche RSA", command=self.genereaza_pereche_rsa).pack(
            side="left", padx=5
        )
        ttk.Button(frame_chei, text="Debug cheie selectata", command=self.debug_cheie_selectata).pack(
            side="left", padx=5
        )

        frame_actiuni = ttk.LabelFrame(container, text="4. Operatii", padding=10)
        frame_actiuni.pack(fill="x", pady=(0, 8))

        ttk.Button(frame_actiuni, text="Cripteaza", command=self.cripteaza_fisier).pack(
            side="left", padx=5
        )
        ttk.Button(frame_actiuni, text="Decripteaza", command=self.decripteaza_fisier).pack(
            side="left", padx=5
        )
        ttk.Button(frame_actiuni, text="Verifica hash", command=self.verifica_hash_fisier).pack(
            side="left", padx=5
        )
        ttk.Button(frame_actiuni, text="Debug chei DB", command=self.debug_arata_chei).pack(
            side="left", padx=5
        )
        ttk.Button(
            frame_actiuni, text="Debug performante", command=self.debug_arata_performante
        ).pack(side="left", padx=5)

        ttk.Label(
            container,
            textvariable=self.status_var,
            foreground="#1f4d3d",
            anchor="w",
            justify="left",
        ).pack(fill="x", pady=(0, 8))

        notebook = ttk.Notebook(container)
        notebook.pack(fill="both", expand=True)

        files_tab = ttk.Frame(notebook, padding=8)
        perf_tab = ttk.Frame(notebook, padding=8)
        keys_tab = ttk.Frame(notebook, padding=8)
        notebook.add(files_tab, text="Fisiere")
        notebook.add(perf_tab, text="Performante")
        notebook.add(keys_tab, text="Chei")

        self.files_tree = self._create_tree(
            files_tab,
            ("id", "status", "algoritm", "framework", "hash", "cale"),
            {
                "id": 50,
                "status": 110,
                "algoritm": 90,
                "framework": 100,
                "hash": 140,
                "cale": 620,
            },
        )
        self.files_tree.bind("<Double-1>", self.selecteaza_fisier_din_tabel)

        self.performance_tree = self._create_tree(
            perf_tab,
            (
                "id",
                "framework",
                "algoritm",
                "operatie",
                "timp",
                "timp_octet",
                "memorie",
                "viteza",
                "hash_ok",
            ),
            {
                "id": 50,
                "framework": 100,
                "algoritm": 90,
                "operatie": 100,
                "timp": 110,
                "timp_octet": 120,
                "memorie": 110,
                "viteza": 110,
                "hash_ok": 90,
            },
        )

        self.keys_tree = self._create_tree(
            keys_tab,
            ("id", "nume", "algoritm", "tip", "valoare"),
            {"id": 50, "nume": 190, "algoritm": 100, "tip": 90, "valoare": 680},
        )
        self.keys_tree.bind("<Double-1>", self.selecteaza_cheie_din_tabel)

    def _create_tree(self, parent, columns, widths):
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=14)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        for column in columns:
            tree.heading(column, text=column.replace("_", " ").capitalize())
            tree.column(column, width=widths.get(column, 120), anchor="w")

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return tree

    def _on_algoritm_changed(self, _event=None):
        self.refresh_key_options()

    def incarca_date_db(self):
        algoritmi = session.query(Algoritm).order_by(Algoritm.nume.asc()).all()
        valori_algoritmi = [alg.nume for alg in algoritmi]
        self.combo_alg["values"] = valori_algoritmi

        if valori_algoritmi:
            if self.algoritm_var.get() not in valori_algoritmi:
                self.algoritm_var.set(valori_algoritmi[0])
        else:
            self.algoritm_var.set("")

        self.refresh_key_options()
        self.refresh_tables()

    def refresh_key_options(self):
        algoritm = self.algoritm_var.get()
        self.key_options = {}
        labels = []

        for cheie in list_keys(algoritm_nume=algoritm):
            label = f"{cheie.nume_cheie} [{cheie.tip_cheie}]"
            self.key_options[label] = cheie
            labels.append(label)

        self.combo_cheie["values"] = labels
        if labels:
            if self.cheie_var.get() not in labels:
                self.cheie_var.set(labels[0])
        else:
            self.cheie_var.set("")

    def refresh_tables(self):
        self._fill_files_table()
        self._fill_performance_table()
        self._fill_keys_table()

    def _fill_files_table(self):
        self._clear_tree(self.files_tree)
        files = session.query(FisierManagement).order_by(FisierManagement.id.desc()).all()
        for fisier in files:
            hash_text = (fisier.hash_curent or fisier.hash_original or "-")[:16]
            self.files_tree.insert(
                "",
                "end",
                values=(
                    fisier.id,
                    fisier.status,
                    fisier.algoritm_ultim or "-",
                    fisier.framework_ultim or "-",
                    hash_text,
                    fisier.path_criptat,
                ),
            )

    def _fill_performance_table(self):
        self._clear_tree(self.performance_tree)
        records = session.query(Performanta).order_by(Performanta.id.desc()).all()
        for record in records:
            self.performance_tree.insert(
                "",
                "end",
                values=(
                    record.id,
                    record.framework,
                    record.algoritm_nume,
                    record.operatie,
                    f"{record.timp_executie:.4f} s",
                    self._format_time_per_byte(record.timp_per_octet),
                    f"{record.memorie_utilizata:.4f} MB",
                    self._format_speed(record.viteza_mb_s),
                    "Da" if record.hash_verificat else "Nu",
                ),
            )

    def _fill_keys_table(self):
        self._clear_tree(self.keys_tree)
        algoritmi = {alg.id: alg.nume for alg in session.query(Algoritm).all()}
        chei = session.query(Cheie).order_by(Cheie.id.desc()).all()
        for cheie in chei:
            self.keys_tree.insert(
                "",
                "end",
                values=(
                    cheie.id,
                    cheie.nume_cheie,
                    algoritmi.get(cheie.algoritm_id, "-"),
                    cheie.tip_cheie,
                    cheie.path_cheie,
                ),
            )

    def _clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def calculeaza_hash(self, filepath):
        try:
            return CryptoManager.compute_hash(filepath)
        except Exception:
            return None

    def _detecteaza_status(self, filepath):
        return "Criptat" if str(filepath).lower().endswith(".enc") else "Necriptat"

    def inregistreaza_fisier_initial(self, cale_absoluta):
        record = find_file_by_path(cale_absoluta)
        if record:
            return record

        status = self._detecteaza_status(cale_absoluta)
        hash_curent = self.calculeaza_hash(cale_absoluta)
        hash_original = hash_curent if status == "Necriptat" else None
        record = register_managed_file(
            cale_absoluta,
            status=status,
            hash_original=hash_original,
            hash_curent=hash_curent,
        )
        self.refresh_tables()
        return record

    def alege_fisier(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        cale_absoluta = str(Path(filepath).resolve())
        self.filepath_var.set(cale_absoluta)
        self.inregistreaza_fisier_initial(cale_absoluta)
        self.status_var.set(f"Fisier selectat: {cale_absoluta}")

    def creeaza_fisier_text(self):
        popup = tk.Toplevel(self.root)
        popup.title("Creeaza Fisier Nou")
        popup.geometry("520x430")
        popup.transient(self.root)
        popup.grab_set()

        ttk.Label(popup, text="Nume fisier (ex: raport.txt):").pack(pady=6)
        nume_var = tk.StringVar()
        ttk.Entry(popup, textvariable=nume_var, width=48).pack(pady=4)

        ttk.Label(popup, text="Algoritm recomandat pentru test:").pack(pady=4)
        alg_var = tk.StringVar(value="AES")
        ttk.Combobox(
            popup, textvariable=alg_var, values=["AES", "RSA"], state="readonly", width=20
        ).pack(pady=4)

        ttk.Label(
            popup,
            text="Poti folosi acelasi fisier pentru testele OpenSSL, PyCa si PyCryptodome.",
        ).pack(pady=4)

        ttk.Label(popup, text="Continut:").pack(pady=6)
        text_area = tk.Text(popup, wrap="word", height=12, width=58)
        text_area.pack(padx=10, pady=5, fill="both", expand=True)

        def salveaza_text():
            nume = nume_var.get().strip()
            continut = text_area.get("1.0", tk.END).rstrip()

            if not nume:
                messagebox.showwarning("Atentie", "Introdu un nume pentru fisier.", parent=popup)
                return

            if not nume.endswith(".txt"):
                nume += ".txt"

            with open(nume, "w", encoding="utf-8") as handle:
                handle.write(continut)

            cale_absoluta = str(Path(nume).resolve())
            self.filepath_var.set(cale_absoluta)
            self.algoritm_var.set(alg_var.get())
            self.inregistreaza_fisier_initial(cale_absoluta)
            self.refresh_key_options()
            self.status_var.set(f"Fisierul {Path(cale_absoluta).name} a fost creat.")
            messagebox.showinfo("Succes", "Fisierul a fost creat si selectat.", parent=popup)
            popup.destroy()

        ttk.Button(popup, text="Salveaza si Selecteaza", command=salveaza_text).pack(pady=10)

    def sterge_fisier_db(self):
        fisier = self.filepath_var.get().strip()
        if not fisier:
            messagebox.showwarning("Atentie", "Selecteaza un fisier pentru stergere.")
            return

        inregistrari = session.query(FisierManagement).filter_by(path_criptat=fisier).all()
        if not inregistrari:
            inregistrari = session.query(FisierManagement).filter_by(nume_original=fisier).all()

        if not inregistrari:
            messagebox.showinfo("Info", "Fisierul selectat nu exista in baza de date.")
            return

        ids = [record.id for record in inregistrari]
        for performanta in session.query(Performanta).filter(Performanta.fisier_id.in_(ids)).all():
            session.delete(performanta)
        for record in inregistrari:
            session.delete(record)
        session.commit()

        self.filepath_var.set("")
        self.refresh_tables()
        self.status_var.set("Inregistrarile asociate fisierului au fost sterse din baza de date.")
        messagebox.showinfo("Succes", "Inregistrarile au fost sterse din baza de date.")

    def adauga_cheie_aes(self):
        nume = simpledialog.askstring("Cheie AES", "Numele cheii AES:", parent=self.root)
        if not nume:
            return
        valoare = simpledialog.askstring(
            "Cheie AES", "Parola/secretul cheii AES:", parent=self.root, show="*"
        )
        if not valoare:
            return

        upsert_key(nume.strip(), valoare.strip(), "AES", "secret")
        self.incarca_date_db()
        self.algoritm_var.set("AES")
        self.refresh_key_options()
        self.status_var.set(f"Cheia AES {nume.strip()} a fost salvata in baza de date.")

    def importa_cheie_rsa(self):
        tip = simpledialog.askstring(
            "Import cheie RSA",
            "Introdu tipul cheii: public sau private",
            parent=self.root,
        )
        if not tip:
            return
        tip = tip.strip().lower()
        if tip not in {"public", "private"}:
            messagebox.showwarning("Atentie", "Tipul cheii trebuie sa fie public sau private.")
            return

        nume = simpledialog.askstring("Import cheie RSA", "Numele cheii in DB:", parent=self.root)
        if not nume:
            return

        filepath = filedialog.askopenfilename(
            title="Selecteaza fisier PEM", filetypes=[("PEM files", "*.pem"), ("All files", "*.*")]
        )
        if not filepath:
            return

        upsert_key(nume.strip(), str(Path(filepath).resolve()), "RSA", tip)
        self.incarca_date_db()
        self.algoritm_var.set("RSA")
        self.refresh_key_options()
        self.status_var.set(f"Cheia RSA {nume.strip()} a fost importata.")

    def genereaza_pereche_rsa(self):
        prefix = simpledialog.askstring(
            "Generare RSA",
            "Prefix pentru fisierele cheii (ex: laborator_rsa):",
            parent=self.root,
            initialvalue="laborator_rsa",
        )
        if not prefix:
            return

        prefix = prefix.strip()
        private_path = Path(f"{prefix}_private.pem").resolve()
        public_path = Path(f"{prefix}_public.pem").resolve()

        try:
            CryptoManager.generate_rsa_keys(private_path, public_path)
            upsert_key(f"{prefix}_public", str(public_path), "RSA", "public")
            upsert_key(f"{prefix}_private", str(private_path), "RSA", "private")
        except Exception as exc:
            messagebox.showerror("Eroare", str(exc))
            return

        self.incarca_date_db()
        self.algoritm_var.set("RSA")
        self.refresh_key_options()
        self.status_var.set(
            f"Perechea RSA a fost generata: {public_path.name} / {private_path.name}."
        )

    def _get_selected_key(self):
        return self.key_options.get(self.cheie_var.get())

    def _ensure_selected_file(self):
        filepath = self.filepath_var.get().strip()
        if not filepath:
            raise ValueError("Selecteaza un fisier.")
        cale = Path(filepath).resolve()
        if not cale.exists():
            raise FileNotFoundError("Fisierul selectat nu exista pe disc.")
        record = find_file_by_path(str(cale))
        if record is None:
            record = self.inregistreaza_fisier_initial(str(cale))
        return str(cale), record

    def _validate_key_for_operation(self, cheie, algoritm, operatie):
        if cheie is None:
            raise ValueError("Selecteaza o cheie din baza de date.")

        if algoritm == "AES" and cheie.tip_cheie != "secret":
            raise ValueError("Pentru AES este necesara o cheie de tip secret.")

        if algoritm == "RSA" and operatie == "Criptare" and cheie.tip_cheie != "public":
            raise ValueError("Pentru criptare RSA trebuie selectata o cheie publica.")

        if algoritm == "RSA" and operatie == "Decriptare" and cheie.tip_cheie != "private":
            raise ValueError("Pentru decriptare RSA trebuie selectata o cheie privata.")

    def _slugify_output_label(self, value):
        return value.strip().lower().replace(" ", "_")

    def _get_original_reference_path(self, source_record, fallback_path):
        original_path = Path(source_record.nume_original) if source_record else Path(fallback_path)
        if not original_path.suffix:
            original_path = original_path.with_suffix(".bin")
        return original_path

    def _build_encrypted_output_path(self, input_path, source_record, framework, algoritm):
        original_path = self._get_original_reference_path(source_record, input_path)
        framework_label = self._slugify_output_label(framework)
        algoritm_label = self._slugify_output_label(algoritm)
        return str(
            original_path.with_name(
                f"{original_path.stem}__criptat__{framework_label}__{algoritm_label}.enc"
            )
        )

    def _build_decrypted_output_path(self, input_path, source_record, framework, algoritm):
        original_path = self._get_original_reference_path(source_record, input_path)
        framework_label = self._slugify_output_label(framework)
        algoritm_label = self._slugify_output_label(algoritm)
        return str(
            original_path.with_name(
                f"{original_path.stem}__decriptat__{framework_label}__{algoritm_label}{original_path.suffix}"
            )
        )

    def _execute_crypto(self, operatie):
        filepath, source_record = self._ensure_selected_file()
        algoritm = self.algoritm_var.get()
        framework = self.framework_var.get()
        cheie = self._get_selected_key()

        if not algoritm or not framework:
            raise ValueError("Selecteaza framework-ul si algoritmul.")

        self._validate_key_for_operation(cheie, algoritm, operatie)

        source_hash = source_record.hash_original or source_record.hash_curent or self.calculeaza_hash(filepath)

        if operatie == "Criptare":
            output_path = self._build_encrypted_output_path(filepath, source_record, framework, algoritm)
            self._run_encrypt(framework, algoritm, filepath, output_path, cheie)
            hash_verificat = False
            detalii = f"Fisier criptat cu {framework} folosind {algoritm}."
            status_rezultat = "Criptat"
        else:
            output_path = self._build_decrypted_output_path(filepath, source_record, framework, algoritm)
            self._run_decrypt(framework, algoritm, filepath, output_path, cheie)
            rezultat_hash = self.calculeaza_hash(output_path)
            hash_verificat = bool(source_hash and rezultat_hash and rezultat_hash == source_hash)
            if source_hash is None:
                detalii = "Decriptare finalizata, dar hash-ul original nu exista in DB pentru validare."
            elif hash_verificat:
                detalii = "Decriptare finalizata cu verificare de integritate reusita."
            else:
                detalii = "Decriptare finalizata, dar hash-ul rezultat nu corespunde cu hash-ul original."
            status_rezultat = "Decriptat"

        dimensiune = os.path.getsize(filepath)
        timp, memorie = self.last_metrics
        viteza = (dimensiune / (1024 * 1024)) / timp if timp > 0 else 0.0
        timp_per_octet = timp / dimensiune if dimensiune > 0 else 0.0
        hash_curent = self.calculeaza_hash(output_path)

        rezultat_record = register_managed_file(
            output_path,
            status=status_rezultat,
            hash_original=source_hash,
            hash_curent=hash_curent,
            source_record=source_record,
            framework=framework,
            algoritm=algoritm,
        )
        record_performance(
            framework=framework,
            operatie=operatie,
            timp_executie=timp,
            timp_per_octet=timp_per_octet,
            memorie_utilizata=memorie,
            viteza_mb_s=viteza,
            fisier_id=rezultat_record.id,
            algoritm_nume=algoritm,
            cheie_id=cheie.id,
            hash_verificat=hash_verificat,
            detalii=detalii,
        )

        self.filepath_var.set(output_path)
        self.incarca_date_db()
        self.status_var.set(
            f"{operatie} reusita cu {framework} / {algoritm}. Output: {Path(output_path).name}"
        )

        mesaj = (
            f"{operatie} reusita.\n\n"
            f"Fisier rezultat: {output_path}\n"
            f"Timp: {timp:.4f} s\n"
            f"Timp/octet: {self._format_time_per_byte(timp_per_octet)}\n"
            f"Memorie: {memorie:.4f} MB\n"
            f"Viteza: {self._format_speed(viteza)}"
        )
        if operatie == "Decriptare":
            mesaj += f"\nIntegritate hash: {'OK' if hash_verificat else 'NEVALIDATA'}"
        messagebox.showinfo("Succes", mesaj)

    def _run_encrypt(self, framework, algoritm, input_path, output_path, cheie):
        if framework == "OpenSSL" and algoritm == "AES":
            self.last_metrics = CryptoManager.encrypt_openssl_aes(input_path, output_path, cheie.path_cheie)
            return
        if framework == "OpenSSL" and algoritm == "RSA":
            self.last_metrics = CryptoManager.encrypt_openssl_rsa(input_path, output_path, cheie.path_cheie)
            return
        if framework == "PyCa" and algoritm == "AES":
            self.last_metrics = CryptoManager.encrypt_pyca_aes(input_path, output_path, cheie.path_cheie)
            return
        if framework == "PyCa" and algoritm == "RSA":
            self.last_metrics = CryptoManager.encrypt_pyca_rsa(input_path, output_path, cheie.path_cheie)
            return
        if framework == "PyCryptodome" and algoritm == "AES":
            self.last_metrics = CryptoManager.encrypt_pycryptodome_aes(
                input_path, output_path, cheie.path_cheie
            )
            return
        if framework == "PyCryptodome" and algoritm == "RSA":
            self.last_metrics = CryptoManager.encrypt_pycryptodome_rsa(
                input_path, output_path, cheie.path_cheie
            )
            return
        raise ValueError("Combinatia framework/algoritm nu este suportata pentru criptare.")

    def _run_decrypt(self, framework, algoritm, input_path, output_path, cheie):
        if framework == "OpenSSL" and algoritm == "AES":
            self.last_metrics = CryptoManager.decrypt_openssl_aes(input_path, output_path, cheie.path_cheie)
            return
        if framework == "OpenSSL" and algoritm == "RSA":
            self.last_metrics = CryptoManager.decrypt_openssl_rsa(input_path, output_path, cheie.path_cheie)
            return
        if framework == "PyCa" and algoritm == "AES":
            self.last_metrics = CryptoManager.decrypt_pyca_aes(input_path, output_path, cheie.path_cheie)
            return
        if framework == "PyCa" and algoritm == "RSA":
            self.last_metrics = CryptoManager.decrypt_pyca_rsa(input_path, output_path, cheie.path_cheie)
            return
        if framework == "PyCryptodome" and algoritm == "AES":
            self.last_metrics = CryptoManager.decrypt_pycryptodome_aes(
                input_path, output_path, cheie.path_cheie
            )
            return
        if framework == "PyCryptodome" and algoritm == "RSA":
            self.last_metrics = CryptoManager.decrypt_pycryptodome_rsa(
                input_path, output_path, cheie.path_cheie
            )
            return
        raise ValueError("Combinatia framework/algoritm nu este suportata pentru decriptare.")

    def cripteaza_fisier(self):
        try:
            self._execute_crypto("Criptare")
        except Exception as exc:
            messagebox.showerror("Eroare", str(exc))
            self.status_var.set(f"Eroare la criptare: {exc}")

    def decripteaza_fisier(self):
        try:
            self._execute_crypto("Decriptare")
        except Exception as exc:
            messagebox.showerror("Eroare", str(exc))
            self.status_var.set(f"Eroare la decriptare: {exc}")

    def verifica_hash_fisier(self):
        try:
            filepath, record = self._ensure_selected_file()
            hash_actual = self.calculeaza_hash(filepath)
            hash_referinta = record.hash_curent or record.hash_original
            if not hash_referinta:
                messagebox.showinfo("Hash", "Fisierul nu are un hash de referinta in baza de date.")
                return

            if hash_actual == hash_referinta:
                mesaj = "Hash-ul fisierului corespunde cu valoarea stocata in baza de date."
            else:
                mesaj = "Hash-ul fisierului NU corespunde cu valoarea stocata in baza de date."

            self.status_var.set(mesaj)
            messagebox.showinfo("Verificare Hash", mesaj)
        except Exception as exc:
            messagebox.showerror("Eroare", str(exc))
            self.status_var.set(f"Eroare la verificarea hash-ului: {exc}")

    def debug_cheie_selectata(self):
        cheie = self._get_selected_key()
        if not cheie:
            messagebox.showinfo("Debug", "Nu exista nicio cheie selectata.")
            return

        messagebox.showinfo(
            "Debug Cheie Selectata",
            f"ID: {cheie.id}\nNume: {cheie.nume_cheie}\nTip: {cheie.tip_cheie}\nValoare/Cale: {cheie.path_cheie}",
        )

    def debug_arata_chei(self):
        chei_db = session.query(Cheie).order_by(Cheie.id.asc()).all()
        if not chei_db:
            messagebox.showinfo("Debug", "Nu exista chei in baza de date.")
            return

        algoritmi = {alg.id: alg.nume for alg in session.query(Algoritm).all()}
        text_chei = "\n".join(
            [
                f"ID: {c.id} | Nume: {c.nume_cheie} | Algoritm: {algoritmi.get(c.algoritm_id, '-')} | Tip: {c.tip_cheie} | Cale/Valoare: {c.path_cheie}"
                for c in chei_db
            ]
        )
        messagebox.showinfo("Debug Chei DB", text_chei)

    def debug_arata_performante(self):
        perf_db = session.query(Performanta).order_by(Performanta.id.desc()).all()
        if not perf_db:
            messagebox.showinfo("Performante", "Nu exista date de performanta.")
            return

        lines = []
        for record in perf_db:
            lines.append(
                f"[{record.framework} | {record.algoritm_nume}] {record.operatie} | Timp: {record.timp_executie:.4f}s | "
                f"Timp/octet: {self._format_time_per_byte(record.timp_per_octet)} | "
                f"Memorie: {record.memorie_utilizata:.4f}MB | Viteza: {self._format_speed(record.viteza_mb_s)} | "
                f"Hash OK: {'Da' if record.hash_verificat else 'Nu'}"
            )
        messagebox.showinfo("Performante DB", "\n".join(lines))

    def selecteaza_fisier_din_tabel(self, _event=None):
        selectie = self.files_tree.selection()
        if not selectie:
            return

        valori = self.files_tree.item(selectie[0], "values")
        if not valori:
            return

        self.filepath_var.set(valori[5])
        if valori[2] and valori[2] != "-":
            self.algoritm_var.set(valori[2])
            self.refresh_key_options()
        self.status_var.set(f"Fisier selectat din tabel: {valori[5]}")

    def selecteaza_cheie_din_tabel(self, _event=None):
        selectie = self.keys_tree.selection()
        if not selectie:
            return

        valori = self.keys_tree.item(selectie[0], "values")
        if not valori:
            return

        algoritm = valori[2]
        label = f"{valori[1]} [{valori[3]}]"
        self.algoritm_var.set(algoritm)
        self.refresh_key_options()
        if label in self.key_options:
            self.cheie_var.set(label)
        self.status_var.set(f"Cheia {valori[1]} a fost selectata din tabel.")

    def _format_speed(self, viteza_mb_s):
        if 0 < viteza_mb_s < 0.01:
            return f"{viteza_mb_s * 1024:.2f} KB/s"
        return f"{viteza_mb_s:.2f} MB/s"

    def _format_time_per_byte(self, timp_per_octet):
        if timp_per_octet == 0:
            return "0 s/octet"
        return f"{timp_per_octet:.6e} s/octet"


if __name__ == "__main__":
    from main import init_database

    init_database()
    root = tk.Tk()
    CryptoApp(root)
    root.mainloop()

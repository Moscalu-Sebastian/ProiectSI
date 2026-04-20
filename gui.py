import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import hashlib
import os
import time
import psutil
from database import session, Algoritm, Cheie, FisierManagement, Performanta
from crypto_manager import CryptoManager

class CryptoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem Management Chei Criptare")
        self.root.geometry("700x450")
        self.root.resizable(False, False)

        self.filepath_var = tk.StringVar()
        self.algoritm_var = tk.StringVar()
        self.cheie_var = tk.StringVar()
        self.framework_var = tk.StringVar()

        self.setup_ui()
        self.incarca_date_db()

    def setup_ui(self):
        frame_fisier = ttk.LabelFrame(self.root, text="1. Selectare Fisier", padding=10)
        frame_fisier.pack(fill="x", padx=10, pady=5)

        ttk.Entry(frame_fisier, textvariable=self.filepath_var, width=45, state="readonly").grid(row=0, column=0, padx=5)
        ttk.Button(frame_fisier, text="Cauta", command=self.alege_fisier).grid(row=0, column=1, padx=2)
        ttk.Button(frame_fisier, text="Scrie Text", command=self.creeaza_fisier_text).grid(row=0, column=2, padx=2)
        ttk.Button(frame_fisier, text="Sterge din DB", command=self.sterge_fisier_db).grid(row=0, column=3, padx=2)

        frame_setari = ttk.LabelFrame(self.root, text="2. Setari Criptare", padding=10)
        frame_setari.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_setari, text="Framework:").grid(row=0, column=0, sticky="w", pady=5)
        self.combo_framework = ttk.Combobox(frame_setari, textvariable=self.framework_var, state="readonly")
        self.combo_framework['values'] = ["OpenSSL", "PyCa"]
        self.combo_framework.current(0)
        self.combo_framework.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_setari, text="Algoritm:").grid(row=1, column=0, sticky="w", pady=5)
        self.combo_alg = ttk.Combobox(frame_setari, textvariable=self.algoritm_var, state="readonly")
        self.combo_alg.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame_setari, text="Cheie DB:").grid(row=2, column=0, sticky="w", pady=5)
        self.combo_cheie = ttk.Combobox(frame_setari, textvariable=self.cheie_var, state="readonly")
        self.combo_cheie.grid(row=2, column=1, padx=5, pady=5)

        frame_actiuni = ttk.Frame(self.root, padding=10)
        frame_actiuni.pack(fill="x", padx=10, pady=10)

        ttk.Button(frame_actiuni, text="Cripteaza", command=self.cripteaza_fisier).pack(side="left", padx=5)
        ttk.Button(frame_actiuni, text="Decripteaza", command=self.decripteaza_fisier).pack(side="left", padx=5)

        frame_debug = ttk.Frame(self.root, padding=10)
        frame_debug.pack(fill="x", padx=10, pady=0)

        ttk.Button(frame_debug, text="Arata Chei DB", command=self.debug_arata_chei).pack(side="left", padx=5)
        ttk.Button(frame_debug, text="Arata Performante", command=self.debug_arata_performante).pack(side="left", padx=5)

    def incarca_date_db(self):
        algoritmi = session.query(Algoritm).all()
        self.combo_alg['values'] = [alg.nume for alg in algoritmi]
        
        chei = session.query(Cheie).all()
        self.combo_cheie['values'] = [cheie.nume_cheie for cheie in chei]

    def calculeaza_hash(self, filepath):
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256.update(byte_block)
            return sha256.hexdigest()
        except Exception:
            return None

    def inregistreaza_fisier_initial(self, cale_absoluta):
        fisier_db = session.query(FisierManagement).filter_by(path_criptat=cale_absoluta).first()
        if not fisier_db:
            dimensiune = os.path.getsize(cale_absoluta)
            hash_f = self.calculeaza_hash(cale_absoluta)
            nou_fisier = FisierManagement(nume_original=cale_absoluta, path_criptat=cale_absoluta, dimensiune_bytes=dimensiune, status="Necriptat", hash_original=hash_f)
            session.add(nou_fisier)
            session.commit()

    def alege_fisier(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            cale_absoluta = os.path.abspath(filepath)
            self.filepath_var.set(cale_absoluta)
            self.inregistreaza_fisier_initial(cale_absoluta)

    def creeaza_fisier_text(self):
        popup = tk.Toplevel(self.root)
        popup.title("Creeaza Fisier Nou")
        popup.geometry("400x420")
        popup.transient(self.root)
        popup.grab_set()

        ttk.Label(popup, text="Nume fisier (ex: secret.txt):").pack(pady=5)
        nume_var = tk.StringVar()
        ttk.Entry(popup, textvariable=nume_var, width=40).pack(pady=5)

        ttk.Label(popup, text="Algoritm vizat:").pack(pady=2)
        alg_var = tk.StringVar(value="AES")
        combo_alg = ttk.Combobox(popup, textvariable=alg_var, values=["AES", "RSA"], state="readonly")
        combo_alg.pack(pady=2)

        indicatie_var = tk.StringVar(value="Indicatie: Fara limita de caractere")
        lbl_indicatie = ttk.Label(popup, textvariable=indicatie_var)
        lbl_indicatie.pack(pady=2)

        def schimba_indicatie(event):
            if alg_var.get() == "RSA":
                indicatie_var.set("Indicatie: Maxim 245 caractere pentru RSA")
            else:
                indicatie_var.set("Indicatie: Fara limita de caractere pentru AES")

        combo_alg.bind("<<ComboboxSelected>>", schimba_indicatie)

        ttk.Label(popup, text="Continut:").pack(pady=5)
        text_area = tk.Text(popup, wrap="word", height=10, width=45)
        text_area.pack(pady=5, padx=10, fill="both", expand=True)

        def salveaza_text():
            nume = nume_var.get().strip()
            continut = text_area.get("1.0", tk.END).strip()
            
            if not nume:
                messagebox.showwarning("Atentie", "Introdu un nume pentru fisier!", parent=popup)
                return
                
            if alg_var.get() == "RSA" and len(continut.encode('utf-8')) > 245:
                messagebox.showwarning("Atentie", "Textul are peste 245 de caractere si nu poate fi criptat cu RSA!", parent=popup)
                return

            if not nume.endswith(".txt"):
                nume += ".txt"
                
            with open(nume, "w", encoding="utf-8") as f:
                f.write(continut)
                
            cale_absoluta = os.path.abspath(nume)
            self.filepath_var.set(cale_absoluta)
            self.algoritm_var.set(alg_var.get())
            self.inregistreaza_fisier_initial(cale_absoluta)
            
            messagebox.showinfo("Succes", f"Fisier pregatit pentru {alg_var.get()}!", parent=popup)
            popup.destroy()

        ttk.Button(popup, text="Salveaza si Selecteaza", command=salveaza_text).pack(pady=10)

    def sterge_fisier_db(self):
        fisier = self.filepath_var.get()
        if not fisier:
            messagebox.showwarning("Atentie", "Selecteaza un fisier pentru a-l sterge.")
            return

        inregistrari = session.query(FisierManagement).filter_by(path_criptat=fisier).all()
        if not inregistrari:
            inregistrari = session.query(FisierManagement).filter_by(nume_original=fisier).all()

        if not inregistrari:
            messagebox.showinfo("Info", "Fisierul selectat nu exista in baza de date.")
            return

        for f in inregistrari:
            performante = session.query(Performanta).filter_by(fisier_id=f.id).all()
            for p in performante:
                session.delete(p)
            session.delete(f)

        session.commit()
        self.filepath_var.set("")
        messagebox.showinfo("Succes", "Inregistrarile au fost sterse din baza de date.")

    def cripteaza_fisier(self):
        fisier = self.filepath_var.get()
        alg_nume = self.algoritm_var.get()
        nume_cheie = self.cheie_var.get()
        framework = self.framework_var.get()

        if not fisier or not alg_nume or not nume_cheie or not framework:
            messagebox.showwarning("Atentie", "Selecteaza fisier, framework, algoritm si cheie")
            return

        hash_fisier = self.calculeaza_hash(fisier)
        cheie_db = session.query(Cheie).filter_by(nume_cheie=nume_cheie).first()
        output_file = fisier + "_" + framework.lower() + ".enc"
        dimensiune = os.path.getsize(fisier)

        try:
            if framework == "OpenSSL":
                if alg_nume == "AES":
                    timp, mem = CryptoManager.encrypt_openssl_aes(fisier, output_file, cheie_db.path_cheie)
                elif alg_nume == "RSA":
                    timp, mem = CryptoManager.encrypt_openssl_rsa(fisier, output_file, cheie_db.path_cheie)
            elif framework == "PyCa":
                if alg_nume == "AES":
                    cheie_bytes = cheie_db.path_cheie.encode('utf-8').ljust(32, b'\0')[:32]
                    timp, mem = CryptoManager.encrypt_pyca_aes(fisier, output_file, cheie_bytes)
                elif alg_nume == "RSA":
                    return
        except Exception as e:
            messagebox.showerror("Eroare", str(e))
            return

        viteza = (dimensiune / (1024 * 1024)) / timp if timp > 0 else 0

        fisier_criptat_db = session.query(FisierManagement).filter_by(path_criptat=output_file).first()
        if not fisier_criptat_db:
            fisier_criptat_db = FisierManagement(nume_original=fisier, path_criptat=output_file, dimensiune_bytes=os.path.getsize(output_file), status="Criptat", hash_original=hash_fisier)
            session.add(fisier_criptat_db)
            session.commit()

        noua_perf = Performanta(framework=framework, operatie="Criptare", timp_executie=timp, memorie_utilizata=mem, viteza_mb_s=viteza, fisier_id=fisier_criptat_db.id, algoritm_nume=alg_nume)
        session.add(noua_perf)
        session.commit()

        messagebox.showinfo("Succes", f"Criptat cu {framework}")

    def decripteaza_fisier(self):
        fisier = self.filepath_var.get()
        alg_nume = self.algoritm_var.get()
        nume_cheie = self.cheie_var.get()
        framework = self.framework_var.get()

        if not fisier or not alg_nume or not nume_cheie or not framework:
            messagebox.showwarning("Atentie", "Selecteaza fisier, framework, algoritm si cheie")
            return

        cheie_db = session.query(Cheie).filter_by(nume_cheie=nume_cheie).first()
        output_file = fisier + "_dec.txt"
        dimensiune = os.path.getsize(fisier)

        try:
            if framework == "OpenSSL" and alg_nume == "AES":
                process = psutil.Process(os.getpid())
                mem_start = process.memory_info().rss / (1024 * 1024)
                start_time = time.time()
                CryptoManager.decrypt_openssl_aes(fisier, output_file, cheie_db.path_cheie)
                timp = time.time() - start_time
                mem = (process.memory_info().rss / (1024 * 1024)) - mem_start
            else:
                return
        except Exception as e:
            messagebox.showerror("Eroare", str(e))
            return

        viteza = (dimensiune / (1024 * 1024)) / timp if timp > 0 else 0

        fisier_dec_db = session.query(FisierManagement).filter_by(path_criptat=output_file).first()
        if not fisier_dec_db:
            hash_dec = self.calculeaza_hash(output_file)
            fisier_dec_db = FisierManagement(nume_original=fisier, path_criptat=output_file, dimensiune_bytes=os.path.getsize(output_file), status="Decriptat", hash_original=hash_dec)
            session.add(fisier_dec_db)
            session.commit()

        noua_perf = Performanta(framework=framework, operatie="Decriptare", timp_executie=timp, memorie_utilizata=mem, viteza_mb_s=viteza, fisier_id=fisier_dec_db.id, algoritm_nume=alg_nume)
        session.add(noua_perf)
        session.commit()

        messagebox.showinfo("Succes", f"Decriptat cu {framework}")

    def debug_arata_chei(self):
        chei_db = session.query(Cheie).all()
        if not chei_db:
            messagebox.showinfo("Debug", "Nu exista chei in baza de date.")
            return
        
        text_chei = "\n".join([f"ID: {c.id} | Nume: {c.nume_cheie} | Cale/Val: {c.path_cheie}" for c in chei_db])
        messagebox.showinfo("Debug Chei DB", text_chei)

    def debug_arata_performante(self):
        perf_db = session.query(Performanta).all()
        if not perf_db:
            messagebox.showinfo("Performante", "Nu exista date de performanta.")
            return
            
        text_perf_lines = []
        for p in perf_db:
            fisier = session.query(FisierManagement).filter_by(id=p.fisier_id).first()
            nume_fisier = os.path.basename(fisier.nume_original) if fisier else "Fisier sters"
            
            if p.viteza_mb_s < 0.01 and p.viteza_mb_s > 0:
                viteza_kb = p.viteza_mb_s * 1024
                viteza_text = f"{viteza_kb:.2f} KB/s"
            else:
                viteza_text = f"{p.viteza_mb_s:.2f} MB/s"
                
            text_perf_lines.append(f"[{p.framework} | {p.algoritm_nume}] {p.operatie} '{nume_fisier}' | Timp: {p.timp_executie:.4f}s | Viteza: {viteza_text}")
            
        text_perf = "\n".join(text_perf_lines)
        messagebox.showinfo("Performante DB", text_perf)

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoApp(root)
    root.mainloop()
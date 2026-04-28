from pathlib import Path

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Algoritm(Base):
    __tablename__ = "algoritmi"

    id = Column(Integer, primary_key=True)
    nume = Column(String, unique=True, nullable=False)
    tip = Column(String, nullable=False)


class Cheie(Base):
    __tablename__ = "chei"

    id = Column(Integer, primary_key=True)
    nume_cheie = Column(String, nullable=False)
    path_cheie = Column(Text, nullable=False)
    tip_cheie = Column(String, default="secret")
    algoritm_id = Column(Integer, ForeignKey("algoritmi.id"), nullable=False)


class FisierManagement(Base):
    __tablename__ = "fisiere"

    id = Column(Integer, primary_key=True)
    nume_original = Column(Text, nullable=False)
    path_criptat = Column(Text, nullable=False)
    dimensiune_bytes = Column(Integer, default=0)
    status = Column(String, default="Necriptat")
    hash_original = Column(String)
    hash_curent = Column(String)
    fisier_sursa_id = Column(Integer, ForeignKey("fisiere.id"))
    framework_ultim = Column(String)
    algoritm_ultim = Column(String)


class Performanta(Base):
    __tablename__ = "performante"

    id = Column(Integer, primary_key=True)
    framework = Column(String, nullable=False)
    operatie = Column(String, nullable=False)
    timp_executie = Column(Float, default=0.0)
    timp_per_octet = Column(Float, default=0.0)
    memorie_utilizata = Column(Float, default=0.0)
    viteza_mb_s = Column(Float, default=0.0)
    fisier_id = Column(Integer, ForeignKey("fisiere.id"))
    algoritm_nume = Column(String, ForeignKey("algoritmi.nume"))
    cheie_id = Column(Integer, ForeignKey("chei.id"))
    hash_verificat = Column(Integer, default=0)
    detalii = Column(Text)


DB_PATH = Path(__file__).resolve().parent / "key_manager.db"
engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
Session = sessionmaker(bind=engine, future=True)
session = Session()


def _add_missing_columns():
    migrations = {
        "chei": {"tip_cheie": "TEXT DEFAULT 'secret'"},
        "fisiere": {
            "hash_curent": "TEXT",
            "fisier_sursa_id": "INTEGER",
            "framework_ultim": "TEXT",
            "algoritm_ultim": "TEXT",
        },
        "performante": {
            "timp_per_octet": "FLOAT DEFAULT 0.0",
            "cheie_id": "INTEGER",
            "hash_verificat": "INTEGER DEFAULT 0",
            "detalii": "TEXT",
        },
    }

    with engine.begin() as connection:
        for table_name, columns in migrations.items():
            existing_columns = {
                row[1] for row in connection.execute(text(f"PRAGMA table_info({table_name})"))
            }
            for column_name, ddl in columns.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}")
                    )


def init_db():
    Base.metadata.create_all(engine)
    _add_missing_columns()


def create_record(obj):
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def read_all(model):
    return session.query(model).all()


def update_performance_time(perf_id, new_time):
    record = session.query(Performanta).filter_by(id=perf_id).first()
    if record:
        record.timp_executie = new_time
        session.commit()
        session.refresh(record)
    return record


def delete_record(obj):
    session.delete(obj)
    session.commit()


def get_or_create_algoritm(nume, tip):
    algoritm = session.query(Algoritm).filter_by(nume=nume).first()
    if algoritm:
        return algoritm
    return create_record(Algoritm(nume=nume, tip=tip))


def get_key_by_name(nume_cheie):
    return session.query(Cheie).filter_by(nume_cheie=nume_cheie).first()


def list_keys(algoritm_nume=None, tip_cheie=None):
    query = session.query(Cheie).join(Algoritm, Cheie.algoritm_id == Algoritm.id)
    if algoritm_nume:
        query = query.filter(Algoritm.nume == algoritm_nume)
    if tip_cheie:
        query = query.filter(Cheie.tip_cheie == tip_cheie)
    return query.order_by(Cheie.nume_cheie.asc()).all()


def upsert_key(nume_cheie, valoare, algoritm_nume, tip_cheie="secret"):
    algoritm = session.query(Algoritm).filter_by(nume=algoritm_nume).first()
    if not algoritm:
        raise ValueError(f"Algoritmul {algoritm_nume} nu exista in baza de date.")

    cheie = session.query(Cheie).filter_by(nume_cheie=nume_cheie).first()
    if cheie:
        cheie.path_cheie = valoare
        cheie.tip_cheie = tip_cheie
        cheie.algoritm_id = algoritm.id
        session.commit()
        session.refresh(cheie)
        return cheie

    return create_record(
        Cheie(
            nume_cheie=nume_cheie,
            path_cheie=valoare,
            tip_cheie=tip_cheie,
            algoritm_id=algoritm.id,
        )
    )


def find_file_by_path(path_fisier):
    cale = str(Path(path_fisier).resolve())
    return session.query(FisierManagement).filter_by(path_criptat=cale).first()


def register_managed_file(
    path_fisier,
    status,
    hash_original=None,
    hash_curent=None,
    source_record=None,
    framework=None,
    algoritm=None,
):
    cale = Path(path_fisier).resolve()
    record = session.query(FisierManagement).filter_by(path_criptat=str(cale)).first()

    if record is None:
        record = FisierManagement(
            nume_original=source_record.nume_original if source_record else str(cale),
            path_criptat=str(cale),
            dimensiune_bytes=cale.stat().st_size if cale.exists() else 0,
            status=status,
            hash_original=hash_original,
            hash_curent=hash_curent,
            fisier_sursa_id=source_record.id if source_record else None,
            framework_ultim=framework,
            algoritm_ultim=algoritm,
        )
        session.add(record)
    else:
        record.nume_original = source_record.nume_original if source_record else record.nume_original
        record.dimensiune_bytes = cale.stat().st_size if cale.exists() else record.dimensiune_bytes
        record.status = status
        record.hash_original = hash_original
        record.hash_curent = hash_curent
        record.fisier_sursa_id = source_record.id if source_record else record.fisier_sursa_id
        record.framework_ultim = framework
        record.algoritm_ultim = algoritm

    session.commit()
    session.refresh(record)
    return record


def record_performance(
    framework,
    operatie,
    timp_executie,
    timp_per_octet,
    memorie_utilizata,
    viteza_mb_s,
    fisier_id,
    algoritm_nume,
    cheie_id=None,
    hash_verificat=False,
    detalii=None,
):
    record = Performanta(
        framework=framework,
        operatie=operatie,
        timp_executie=timp_executie,
        timp_per_octet=timp_per_octet,
        memorie_utilizata=memorie_utilizata,
        viteza_mb_s=viteza_mb_s,
        fisier_id=fisier_id,
        algoritm_nume=algoritm_nume,
        cheie_id=cheie_id,
        hash_verificat=1 if hash_verificat else 0,
        detalii=detalii,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


init_db()

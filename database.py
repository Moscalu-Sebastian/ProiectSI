from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Algoritm(Base):
    __tablename__ = 'algoritmi'
    id = Column(Integer, primary_key=True)
    nume = Column(String, unique=True)
    tip = Column(String)

class Cheie(Base):
    __tablename__ = 'chei'
    id = Column(Integer, primary_key=True)
    nume_cheie = Column(String)
    path_cheie = Column(String)
    algoritm_id = Column(Integer, ForeignKey('algoritmi.id'))

class FisierManagement(Base):
    __tablename__ = 'fisiere'
    id = Column(Integer, primary_key=True)
    nume_original = Column(String)
    path_criptat = Column(String)
    dimensiune_bytes = Column(Integer)

class Performanta(Base):
    __tablename__ = 'performante'
    id = Column(Integer, primary_key=True)
    framework = Column(String)
    operatie = Column(String)
    timp_executie = Column(Float)
    memorie_utilizata = Column(Float)
    fisier_id = Column(Integer, ForeignKey('fisiere.id'))
    algoritm_id = Column(Integer, ForeignKey('algoritmi.id'))

engine = create_engine('sqlite:///key_manager.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def create_record(obj):
    """Operatie CREATE: Adauga orice obiect in DB."""
    session.add(obj)
    session.commit()
    return obj

def read_all(model):
    """Operatie READ: Returneaza toate inregistrarile dintr-un tabel."""
    return session.query(model).all()

def update_performance_time(perf_id, new_time):
    """Operatie UPDATE: Modifica timpul unei inregistrari de performanta."""
    record = session.query(Performanta).filter_by(id=perf_id).first()
    if record:
        record.timp_executie = new_time
        session.commit()
    return record

def delete_record(obj):
    """Operatie DELETE: sterge un obiect din DB."""
    session.delete(obj)
    session.commit()
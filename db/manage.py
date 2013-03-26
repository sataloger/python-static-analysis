import contextlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from analyzer.db.tables import Base

__all__= ['connect', 'get_session', 'syncdb', 'disconnect']
engine = create_engine('sqlite:///db.sqlite')
_session = None

def connect():
    global _session
    Session = sessionmaker(bind=engine)
    _session = Session()

def get_session():
    if _session:
        return _session
    raise Exception("Attempt to access database before connect.")

def syncdb():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def disconnect():
    global _session
    if _session:
        _session.close()
        _session = None







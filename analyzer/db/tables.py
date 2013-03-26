from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *

Base = declarative_base()

class AnalyzedFile(Base):
    __tablename__ = 'analyzed_files'

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    source_path = Column(String)
    result_path = Column(String)
    status = Column(Boolean)

    def __init__(self, source_path, filename, result_path = None):
        self.filename = filename
        self.source_path = source_path
        if result_path:
            self.result_path = result_path
        else:
            self.result_path = source_path
        self.status = False

    def __repr__(self):
        return "<AnalyzedFile('%s','%s', '%s')>" % (self.source_path, self.filename, self.status)

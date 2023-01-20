# This module handles CRUD for the sqlite database

# sqlalchemy
import sqlalchemy as db
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Integer, String

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import inspect, select, update, delete, values

# marshmallow 
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

# Custom modules
import ao3scraper.constants as constants

engine = db.create_engine(f'sqlite:///{constants.DATABASE_FILE_PATH}')
connection = engine.connect()

Base = declarative_base()
metadata = MetaData()

# Setup sessionmaker so we don't need to use Session(engine) every time
Session = sessionmaker(engine)

# Create fanfic class
class Fanfic(Base):
    __tablename__ = "fics"
    
    id = db.Column(Integer, primary_key=True, unique=True)

# Add each item in TABLE_COLUMNS to the database as a db.Column(String) object.
for column in constants.TABLE_COLUMNS:
    setattr(Fanfic, column, db.Column(String))

# Create Schema for serialization via Marshmallow.
class FanficSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Fanfic
        include_relationships = True
        load_instance = True


def add_fic(fic_id):
    """Adds a new fic to the database."""
    with Session() as session:
        session.add(Fanfic(id=fic_id))
        session.commit()

def add_all_fics(fic_id):
    """Adds multiple new fics to the database. (Input needs to be list)"""

    # https://stackoverflow.com/questions/7889183/sqlalchemy-insert-or-update-example
    with Session() as session:
        session.add_all(Fanfic(id=fic_id))
        session.commit()


def update_fic(fic, fic_id):
    """Updates all fics with scraped data."""

    with Session() as session:
        stmt = update(Fanfic).where(Fanfic.id == int(fic_id)).values(fic)
        session.execute(stmt)
        session.commit()


def delete_fic(fic_id):
    """Deletes a fic from the database."""

    with Session() as session:
        query = session.get(Fanfic, fic_id)
        session.delete(query)
        session.commit()

def get_fic(fic_id):
    """Returns a fic from the database."""

    with Session() as session:
        query = session.get(Fanfic, fic_id)
        result_dict = FanficSchema().dump(query)
        return result_dict


def get_all_fics():
    """Returns all fics from the database."""

    with Session() as session:
        query = session.query(Fanfic)
        result_dict = [FanficSchema().dump(u) for u in query.all()]
        return result_dict
    

def get_fic_ids():
    """Returns all fic IDs from the database in a list."""

    with Session() as session:
        query = session.query(Fanfic.id).all()
        result = [r for r, in query]
        return result


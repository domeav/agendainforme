from peewee import *
from settings import DB_FILE
from datetime import datetime

db = SqliteDatabase(DB_FILE)

CATEGORIES = {
    "ateliers": "Portes ouvertes ateliers d'artistes",
    "cine_regul": "Cinematographe : séances régulières",
    "cine_retro": "Cinématographe : festivals – cycles – rétrospectives",
    "cine_unique": "Cinématographe : séances uniques",
    "concerts": "Concerts",
    "divers": "Expressions diverses et variées",
    "expositions": "Expositions",
    "radio": "Radiophonie",
    "workshops": "Ateliers – workshop – masterclass – stage – pratique musicale"
}

class Event(Model):
    category = CharField(index=True)
    date_start = DateField(index=True, null=True)
    date_end = DateField(index=True, null=True)
    time_details = CharField(null=True)
    place = TextField()
    description = TextField()
    price = CharField(null=True)
    external_link = CharField(null=True)
    creation_date = DateTimeField(index=True, null=True, default=datetime.now)
    created_by = CharField(index=True)
    highlight = BooleanField()
    
    class Meta:
        database = db


class Place(Model):
    name = CharField()
    description = TextField()

    class Meta:
        database = db

db.connect()
db.create_tables([Event, Place])

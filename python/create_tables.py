import database

db = database.Database()
db.metadata.create_all(db.engine)
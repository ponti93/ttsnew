from models.models import db
from app import app

def reinit_db():
    print("Dropping all tables...")
    with app.app_context():
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Database reinitialized successfully!")

if __name__ == "__main__":
    reinit_db()
from server import app, db
from sqlalchemy import text

def reset_database():
    with app.app_context():
        try:
            print("WARNING: This will delete all data in the database!")
            print("Dropping all tables...")
            db.drop_all()
            
            print("Creating all tables with new schema...")
            db.create_all()
            
            print("Database reset successfully! New schema applied.")
        except Exception as e:
            print(f"Error resetting database: {e}")

if __name__ == "__main__":
    reset_database()

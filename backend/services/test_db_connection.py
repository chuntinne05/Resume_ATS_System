from database.config import SessionLocal

def test_connection():
    db = SessionLocal()
    try:
        result = db.execute("SELECT 1")
        print("Database connection successful:", result.fetchone())
    finally:
        db.close()

if __name__ == "__main__":
    test_connection()
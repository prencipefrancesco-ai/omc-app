import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "omc.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create attori table
    print("Creating 'attori' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            ruolo TEXT,
            attivo INTEGER DEFAULT 1
        );
    """)

    # 2. Insert default actors if empty
    print("Inserting default actors...")
    cursor.execute("SELECT count(*) FROM attori")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO attori (nome, ruolo) VALUES (?, ?)",
            [
                ("Account (Default)", "Account"),
                ("Mario Rossi", "PM"),
                ("Giulia Bianchi", "Account")
            ]
        )

    # 3. Alter forecast table to add attore_id
    print("Checking if 'attore_id' exists in 'forecast' table...")
    try:
        # Check if column exists by trying to select it
        cursor.execute("SELECT attore_id FROM forecast LIMIT 1")
        print("'attore_id' column already exists in 'forecast'.")
    except sqlite3.OperationalError:
        print("Adding 'attore_id' column to 'forecast' table...")
        cursor.execute("ALTER TABLE forecast ADD COLUMN attore_id INTEGER REFERENCES attori(id)")
    
    # 4. Assign default actor (id=1) to existing forecasts
    print("Assigning default actor to existing forecasts without one...")
    cursor.execute("UPDATE forecast SET attore_id = 1 WHERE attore_id IS NULL")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()

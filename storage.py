import sqlite3
import csv
import os

# === Verbindung zur SQLite-Datenbank herstellen ===
conn = sqlite3.connect("motorrad.db")
c = conn.cursor()

# === Tabelle anlegen, falls sie nicht existiert ===
c.execute("""
CREATE TABLE IF NOT EXISTS FireChairDatabase (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    preis TEXT,
    kilometer TEXT
)
""")

# === Alle CSV-Dateien im aktuellen Ordner finden ===
csv_files = [f for f in os.listdir() if f.endswith(".csv")]
print(f"[INFO] Gefundene CSV-Dateien: {csv_files}")

# === Jede CSV-Datei einzeln importieren ===
for csv_file in csv_files:
    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                c.execute("""
                    INSERT OR IGNORE INTO anzeigen (url, preis, kilometer)
                    VALUES (?, ?, ?)
                """, (row["url"], row["preis"], row["kilometer"]))
                count += 1
            except Exception as e:
                print(f"[WARN] Fehler in Datei {csv_file} bei Eintrag {row['url']}: {e}")
        print(f"[INFO] {count} Einträge aus '{csv_file}' importiert.")

# === Änderungen speichern und schließen ===
conn.commit()
conn.close()
print("[INFO] Alle CSVs wurden verarbeitet.")

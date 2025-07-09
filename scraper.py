import requests
from bs4 import BeautifulSoup
import re
import time
import csv
import sqlite3
from tqdm import tqdm

MODEL = "honda cbr 600f"
BASE_URL = "https://www.kleinanzeigen.de/s-motorraeder-roller/{MODEL}/k0c305"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_listing_urls(page_url):
    try:

        res = requests.get(page_url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        links =soup.find_all("a", href=True)        
        print("[DEBUG] Lade URL:", page_url,)
        
        anzeigen_urls = [
            "https://www.kleinanzeigen.de" + a["href"]
            for a in links
            
            if a["href"].startswith("/s-anzeige/") 
            
            ]
        return list(set(anzeigen_urls))
    except Exception as e:
        print(f"[ERROR] Fehler beim Laden von {page_url}: {e}")
        return []

def get_price_and_km(url):
    try:
        time.sleep(1.5)
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        # Preis extrahieren
        price_tag = soup.select_one("h2#viewad-price")
        price = price_tag.get_text(strip=True) if price_tag else None

        # Kilometer extrahieren
        km = None
        for li in soup.select("li.addetailslist--detail"):
            if "Kilometerstand" in li.get_text():
                span = li.find("span", class_="addetailslist--detail--value")
                km = span.get_text(strip=True) if span else None
                break

        return price, km

    except Exception as e:
        print(f"[ERROR] Fehler bei {url}: {e}")
        return None, None

def save_to_csv(data, filename=None):
    if not filename:
        filename = MODEL.replace(" ", "-") + ".csv"
    print(f"[INFO] Speichere {len(data)} Einträge in {filename}")
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["url", "preis", "kilometer"])
        writer.writeheader()
        writer.writerows(data)



def save_to_db(data, model="unbekannt"):
    conn = sqlite3.connect("motorrad.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS anzeigen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            preis TEXT,
            kilometer TEXT,
            modell TEXT
        )
    """)
    for eintrag in data:
        c.execute("""
            INSERT OR IGNORE INTO anzeigen (url, preis, kilometer, modell)
            VALUES (?, ?, ?, ?)
        """, (eintrag["url"], eintrag["preis"], eintrag["kilometer"], model))
    conn.commit()
    conn.close()


def build_page_url(query: str, page: int) -> str:
    base = f"https://www.kleinanzeigen.de/s-{query}/k0c305"
    return base  if page == 1 else f"https://www.kleinanzeigen.de/Seite:{page}/s-{query}/k0c305"



def scrape_all_pages(pages=1):
    all_data = []
    query = MODEL.replace(" ", "-")

    for page in range(1, pages + 1):
        print(f"\n[INFO] Lade Seite {page}...")
        page_url = build_page_url(query, page)
        print(f"[INFO] Lade Seite {page}: {page_url}")
        urls = get_listing_urls(page_url)
        print(f"[INFO] {len(urls)} in {page_url} Anzeigen gefunden.")

        for url in tqdm(urls, desc=f"Seite {page}"):
            price, km = get_price_and_km(url)
            all_data.append({"url": url, "preis": price, "kilometer": km})

    save_to_csv(all_data)
    print_summary(all_data)

def get_max_pages(query):
    query_url = f"https://www.kleinanzeigen.de/s-{query}/k0c305"
    try:
        res = requests.get(query_url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        # Finde alle Seiten-Links
        page_links = soup.select("a.pagination-page")
        page_numbers = []

        for link in page_links:
            try:
                number = int(link.get_text(strip=True))
                page_numbers.append(number)
            except ValueError:
                continue

        max_page = max(page_numbers) if page_numbers else 1
        print(f"[INFO] Maximale Seitenzahl erkannt: {max_page}")
        return max_page

    except Exception as e:
        print(f"[ERROR] Fehler beim Ermitteln der Seitenzahl: {e}")
        return 1

def parse_number(value: str) -> int:
    if not value:
        return float("inf")
    cleaned = (
        value.replace(".", "")
             .replace("€", "")
             .replace("km", "")
             .replace("KM", "")
             .replace("Kilometer", "")
             .strip()
    )
    try:
        return int(cleaned)
    except ValueError:
        return float("inf")


def print_summary(data):
    if not data:
        print("[INFO] Keine Daten vorhanden für Zusammenfassung.")
        return

    # Mit bereinigten Werten vergleichen
    cheapest = min(data, key=lambda x: parse_number(x["preis"]))
    lowest_km = min(data, key=lambda x: parse_number(x["kilometer"]))

    print("\n Günstigste Anzeige:")
    print(f"- Preis: {cheapest['preis']}")
    print(f"- Kilometer: {cheapest['kilometer']}")
    print(f"- URL: {cheapest['url']}")

    print("\n Anzeige mit dem niedrigsten Kilometerstand:")
    print(f"- Preis: {lowest_km['preis']}")
    print(f"- Kilometer: {lowest_km['kilometer']}")
    print(f"- URL: {lowest_km['url']}")




if __name__ == "__main__":
    query = MODEL.replace(" ", "-")
    max_pages = get_max_pages(query)
    scrape_all_pages(pages=max_pages)


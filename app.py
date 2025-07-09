import flet as ft
import sqlite3
from scraper import (
    build_page_url,
    get_listing_urls,
    get_price_and_km,
    save_to_csv,
    save_to_db,
    get_max_pages,
    parse_number,
)

def print_summary_text(data):
    if not data:
        return " Keine Daten gefunden."
    cheapest = min(data, key=lambda x: parse_number(x["preis"]))
    lowest_km = min(data, key=lambda x: parse_number(x["kilometer"]))
    return f"""**Zusammenfassung**\n\n🔻 *Günstigste Anzeige*\n- Preis: {cheapest['preis']}\n- Kilometer: {cheapest['kilometer']}\n- URL: {cheapest['url']}\n\n🛣️ *Niedrigster Kilometerstand*\n- Preis: {lowest_km['preis']}\n- Kilometer: {lowest_km['kilometer']}\n- URL: {lowest_km['url']}"""

def main(page: ft.Page):
    page.title = "🏍️ Motorrad-Scraper Web UI"
    page.theme_mode = "dark"
    page.scroll = "auto"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"

    model_input = ft.TextField(label="Motorrad-Modell", width=300)
    scrape_button = ft.ElevatedButton("Scraping starten", width=300)
    progress = ft.ProgressBar(width=300, value=0)
    status = ft.Text("", selectable=True)
    result_count = ft.Text("", selectable=True)
    summary_output = ft.Markdown("", selectable=True)

    sql_input = ft.TextField(label="SQL-Abfrage", multiline=True, min_lines=3, max_lines=5, width=600)
    sql_output = ft.Markdown("", selectable=True, expand=True)

    def on_scrape_click(e):
        model = model_input.value.strip()
        if not model:
            status.value = " Bitte gib ein Modell ein."
            page.update()
            return

        query = model.replace(" ", "-")
        status.value = f"Scraping gestartet für: '{model}'..."
        result_count.value = ""
        summary_output.value = ""
        progress.value = 0
        page.update()

        try:
            max_pages = get_max_pages(query)
            all_data = []
            current_step = 0
            total_steps = 0

            for page_num in range(1, max_pages + 1):
                total_steps += len(get_listing_urls(build_page_url(query, page_num)))

            for page_num in range(1, max_pages + 1):
                page_url = build_page_url(query, page_num)
                urls = get_listing_urls(page_url)
                for url in urls:
                    price, km = get_price_and_km(url)
                    all_data.append({"url": url, "preis": price, "kilometer": km})
                    current_step += 1
                    progress.value = current_step / total_steps if total_steps else 0
                    page.update()

            save_to_csv(all_data, f"{query}.csv")
            save_to_db(all_data, model)

            status.value = f"Fertig: {query}.csv gespeichert und Datenbank aktualisiert."
            result_count.value = f" {len(all_data)} Anzeigen gefunden."
            summary_output.value = print_summary_text(all_data)
            progress.value = 1

        except Exception as err:
            status.value = f" Fehler: {err}"
            result_count.value = ""
            summary_output.value = ""
            progress.value = 0

        page.update()

    def execute_sql_query(e):
        query = sql_input.value.strip()
        if not query:
            sql_output.value = " Bitte gib eine SQL-Abfrage ein."
            page.update()
            return
        try:
            conn = sqlite3.connect("motorrad.db")
            c = conn.cursor()
            result = c.execute(query).fetchall()
            columns = [desc[0] for desc in c.description] if c.description else []
            conn.close()

            if not result:
                sql_output.value = "Keine Ergebnisse gefunden."
            else:
                header = " | ".join(columns)
                separator = " | ".join(["---"] * len(columns))
                rows = "\n".join(" | ".join(str(col) for col in row) for row in result)
                sql_output.value = f"**Ergebnisse:**\n\n{header}\n{separator}\n{rows}"

        except Exception as err:
            sql_output.value = f" Fehler: {err}"

        page.update()

    scrape_button.on_click = on_scrape_click
    query_button = ft.ElevatedButton("SQL ausführen", on_click=execute_sql_query)

    page.add(
        ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Container(height=80),
                        ft.Text("Fire Chair Motorrad-Scraper für Ebay Kleinanzeigen", size=24, weight="bold"),
                        model_input,
                        scrape_button,
                        progress,
                        status,
                        result_count,
                        summary_output,
                        ft.Divider(),
                        ft.Text("SQL-Abfrage an motorrad.db", size=18),
                        sql_input,
                        query_button,
                        sql_output,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    )

ft.app(target=main, view=ft.WEB_BROWSER)

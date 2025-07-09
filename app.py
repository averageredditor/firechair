import flet as ft
from scraper import (
    build_page_url,
    get_listing_urls,
    get_price_and_km,
    save_to_csv,
    get_max_pages,
    parse_number,
)

def scrape_model(model: str):
    """Vollständiger Ablauf für Scraping mit Rückgabe der Daten"""
    query = model.replace(" ", "-")
    max_pages = get_max_pages(query)
    all_data = []

    for page in range(1, max_pages + 1):
        page_url = build_page_url(query, page)
        urls = get_listing_urls(page_url)
        for url in urls:
            price, km = get_price_and_km(url)
            all_data.append({"url": url, "preis": price, "kilometer": km})

    save_to_csv(all_data, f"{query}.csv")
    return all_data

def print_summary_text(data):
    if not data:
        return " Keine Daten gefunden."

    cheapest = min(data, key=lambda x: parse_number(x["preis"]))
    lowest_km = min(data, key=lambda x: parse_number(x["kilometer"]))

    summary = f"""**Zusammenfassung**

 *Günstigste Anzeige*
- Preis: {cheapest['preis']}
- Kilometer: {cheapest['kilometer']}
- URL: {cheapest['url']}

 *Niedrigster Kilometerstand*
- Preis: {lowest_km['preis']}
- Kilometer: {lowest_km['kilometer']}
- URL: {lowest_km['url']}"""

    return summary

def main(page: ft.Page):
    page.title = "FireChair"
    page.theme_mode = "dark"
    page.scroll = "auto"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    # UI-Elemente
    status = ft.Text()
    result_count = ft.Text()
    summary_output = ft.Markdown("")

    modell_input = ft.TextField(
        label="Motorrad-Modell", width=300, autofocus=True
    )
    scrape_button = ft.ElevatedButton("Scraping starten", width=300)

    # Fortschrittsanzeige (Balken statt Spinner)
    progress_bar = ft.ProgressBar(width=300, value=0)

    # Callback
    def on_scrape_click(e):
        model = modell_input.value.strip()
        if not model:
            status.value = " Bitte gib ein Modell ein."
            page.update()
            return

        query = model.replace(" ", "-")
        status.value = f" Scraping gestartet für: '{model}'..."
        result_count.value = ""
        summary_output.value = ""
        progress_bar.value = 0
        page.update()

        try:
            max_pages = get_max_pages(query)
            all_data = []
            current_step = 0
            total_steps = 0

            # Vorab zählen
            for page_num in range(1, max_pages + 1):
                page_url = build_page_url(query, page_num)
                total_steps += len(get_listing_urls(page_url))

            if total_steps == 0:
                status.value = " Keine Anzeigen gefunden."
                page.update()
                return

            for page_num in range(1, max_pages + 1):
                page_url = build_page_url(query, page_num)
                urls = get_listing_urls(page_url)

                for url in urls:
                    price, km = get_price_and_km(url)
                    all_data.append({"url": url, "preis": price, "kilometer": km})
                    current_step += 1
                    progress_bar.value = current_step / total_steps
                    page.update()

            save_to_csv(all_data, f"{query}.csv")
            status.value = f" Fertig: {query}.csv gespeichert"
            result_count.value = f" {len(all_data)} Anzeigen gefunden."
            summary_output.value = print_summary_text(all_data)
            progress_bar.value = 1

        except Exception as err:
            status.value = f"Fehler: {err}"
            result_count.value = ""
            summary_output.value = ""
            progress_bar.value = 0

        page.update()

    scrape_button.on_click = on_scrape_click

    # Zentriertes Layout: alle Elemente in Column → innerhalb Row (zentriert)
    page.add(
        ft.Row(
            controls=[
                ft.Column(
                    [
                        ft.Text("FireChair Motorrad-Scraper für Ebay Kleinanzeigen", size=24, weight="bold"),
                        modell_input,
                        scrape_button,
                        progress_bar,
                        status,
                        result_count,
                        summary_output,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            expand=True,
        )
    )



ft.app(target=main, view=ft.WEB_BROWSER)

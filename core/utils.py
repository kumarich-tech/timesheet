import requests
from bs4 import BeautifulSoup
from datetime import datetime, date

def parse_consultant_calendar(year):
    url = "https://www.consultant.ru/law/ref/calendar/proizvodstvennye/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка при загрузке календаря: {e}")
        return set(), set()

    soup = BeautifulSoup(response.text, "html.parser")
    holidays = set()
    weekends = set()

    headers = soup.find_all(lambda tag: tag.name in ["h2", "h3"] and str(year) in tag.text)
    if not headers:
        return holidays, weekends
    header = headers[0]
    table = header.find_next_sibling("table")
    if not table:
        return holidays, weekends

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        month_name = cells[0].get_text(strip=True)
        try:
            month = datetime.strptime(month_name, "%B").month
        except ValueError:
            continue
        for day_idx, cell in enumerate(cells[1:], start=1):
            style = cell.get("style", "")
            classes = cell.get("class", [])
            if "red" in style or "holiday" in classes:
                holidays.add(date(year, month, day_idx))
            elif "weekend" in classes:
                weekends.add(date(year, month, day_idx))

    return holidays, weekends

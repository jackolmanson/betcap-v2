import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; betcap-pipeline/1.0)"}


def fetch_team_data(year: int = None) -> pd.DataFrame:
    if year is None:
        today = date.today()
        # Season URLs use the year the season ends (e.g. 2026-27 → 2027).
        # November and December belong to the new season.
        year = today.year + 1 if today.month >= 11 else today.year

    base = "https://www.sports-reference.com/cbb/seasons"
    url = f"{base}/{year}-advanced-school-stats.html"
    url2 = f"{base}/{year}-advanced-opponent-stats.html"

    print(f"Scraping team stats for {year}...")
    html = requests.get(url, headers=HEADERS).text
    html2 = requests.get(url2, headers=HEADERS).text

    soup = BeautifulSoup(html, features="lxml")
    soup2 = BeautifulSoup(html2, features="lxml")

    headers = [th.getText() for th in soup.findAll("tr", limit=2)[1].findAll("th")]
    headers.pop(0)

    x = 1
    for i in range(len(headers)):
        if len(headers[i]) < 2:
            headers[i] = x
            x += 1

    rows = soup.findAll("tr")[2:]
    rows_data = [[td.getText() for td in rows[i].findAll("td")] for i in range(len(rows))]

    headers2 = [th.getText() for th in soup2.findAll("tr", limit=2)[1].findAll("th")]
    headers2.pop(0)
    headers.append("OpTS%")

    rows2 = soup2.findAll("tr")[2:]
    rows_data2 = [[td.getText() for td in rows2[i].findAll("td")] for i in range(len(rows2))]

    for n in range(len(rows_data)):
        try:
            rows_data[n].append(rows_data2[n][24])
            rows_data[n][0] = rows_data[n][0].upper()
            rows_data[n][0] = rows_data[n][0].replace(" ", "-")
            rows_data[n][0] = rows_data[n][0].replace("&", "")
            rows_data[n][0] = rows_data[n][0].replace(".", "")
            rows_data[n][0] = rows_data[n][0].replace("(", "")
            rows_data[n][0] = rows_data[n][0].replace(")", "")
            rows_data[n][0] = rows_data[n][0].replace("'", "")
        except Exception:
            continue

    rows_data = list(filter(None, rows_data))
    df = pd.DataFrame(rows_data, columns=headers)

    for col in range(1, 15):
        del df[col]
    for col in ["W-L%", "SRS", "SOS", "BLK%", "ORB%", "FT/FGA", "Tm.", "Opp.", "eFG%", "FTr", "3PAr", "AST%"]:
        del df[col]

    df.columns = ["Name", "Pace", "OffensiveRating", "TrueShooting%", "TotalRebound%", "Steal%", "Turnover%", "OppTrueShooting%"]
    print(f"Scraped {len(df)} teams")
    return df

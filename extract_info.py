import pandas as pd
from bs4 import BeautifulSoup
import regex as re
import time
from datetime import datetime

def extract_info(file_path):
    soup = None

    with open(file_path, "r") as f:
        content = f.read()
        soup = BeautifulSoup(content, "html.parser")

    document_type = soup.document.type.find_next(text=True)[0:-1]

    cik = re.search(r"(?<=CENTRAL INDEX KEY:)(.*?)(?=\n)", content).group()
    cik = cik.strip()

    reporting_date = re.search(r"(?<=CONFORMED PERIOD OF REPORT:)(.*?)(?=\n)", content).group()
    reporting_date = reporting_date.strip()
    reporting_date = datetime.strptime(reporting_date, "%Y%m%d")

    filing_date = re.search(r"(?<=FILED AS OF DATE:)(.*?)(?=\n)", content).group()
    filing_date = filing_date.strip()
    filing_date = datetime.strptime(filing_date, "%Y%m%d")

    industry = re.search(r"(?<=STANDARD INDUSTRIAL CLASSIFICATION:)(.*?)(?=\[)", content).group()
    industry = industry.strip()

    street1 = re.search(r"(?<=STREET 1:)(.*?)(?=\n)", content).group()
    street2 = re.search(r"(?<=STREET 2:)(.*?)(?=\n)", content)
    city = re.search(r"(?<=CITY:)(.*?)(?=\n)", content).group()
    state = re.search(r"(?<=STATE:)(.*?)(?=\n)", content).group()
    
    if street2 is None:
        location = street1.strip() + ", " + city.strip() + ", " + state.strip()
    else:
        street2 = street2.group()
        location = street1.strip() + "/" + street2.strip() + ", " + city.strip() + ", " + state.strip()

    fiscal_year = re.search(r"(?<=CONFORMED PERIOD OF REPORT:)(.*?)(?=\n)", content).group()
    fiscal_year = fiscal_year.strip()[0:4]

    trading_symbol = soup.find(attrs={"name": "dei:TradingSymbol"})
    trading_symbol = trading_symbol.get_text("")

    company_info = {
        "Document": document_type,
        "CIK": cik,
        "Ticker": trading_symbol,
        "Fiscal_year": fiscal_year,
        "Reporting_date": reporting_date,
        "Filing_date": filing_date,
        "Location": location,
        "Industry": industry
    }

    return company_info

if __name__ == "__main__":
    # Testing 
    start = time.time()
    test = extract_info("filings/0001213900-22-015871.txt")
    end = time.time() - start
    print(end)
    print(test)
"""Build task2/reference/ticker_names.csv: which company names count as a mention of each ticker.

Input 1: the S&P 500 list from 2 April 2018 (the closest dated list after our price data ends),
         pinned to one commit so anyone gets the same file:
         https://raw.githubusercontent.com/datasets/s-and-p-500-companies/5dfdfbc3b9f52802f89e72da6e050b5cafdec4a6/data/constituents.csv
Input 2: the 505 tickers in all_stocks_5yr.csv.
Output:  ticker, company, match_names ("|" between names), rule (auto / manual / not_matched)

Usage: python3 make_ticker_names.py constituents_2018.csv all_stocks_5yr.csv ticker_names.csv
"""
import csv
import re
import sys

# 7 tickers had left the list or been renamed by April 2018. Names are from their 2013-2017 filings.
MISSING_FROM_2018_LIST = {
    "CBG": "CBRE Group", "CHK": "Chesapeake Energy", "HCN": "Welltower",
    "PCLN": "Priceline Group", "PDCO": "Patterson Companies", "SIG": "Signet Jewelers",
    "SNI": "Scripps Networks Interactive",
}

# Names chosen by hand: short forms news actually uses, or a longer form when the short one is a common word.
MANUAL = {
    "MMM": "3M", "GOOGL": "Alphabet|Google", "GOOG": "Alphabet|Google", "AMZN": "Amazon.com|Amazon Inc",
    "FB": "Facebook", "T": "AT&T", "KO": "Coca-Cola", "DIS": "Walt Disney|Disney", "WMT": "Walmart|Wal-Mart",
    "HRB": "H&R Block", "LLY": "Eli Lilly", "GWW": "W. W. Grainger|W.W. Grainger", "EIX": "Edison International",
    "HON": "Honeywell", "MAR": "Marriott", "HIG": "Hartford Financial", "PEG": "Public Service Enterprise Group|PSEG",
    "RL": "Ralph Lauren", "PHM": "PulteGroup|Pulte Homes", "UNH": "UnitedHealth", "UAL": "United Airlines|United Continental",
    "F": "Ford Motor", "HPQ": "Hewlett-Packard|HP Inc", "JPM": "JPMorgan|JP Morgan|J.P. Morgan",
    "C": "Citigroup|Citibank", "BK": "BNY Mellon|Bank of New York Mellon", "CRM": "Salesforce",
    "PCLN": "Priceline", "MCD": "McDonald's", "KSS": "Kohl's", "LOW": "Lowe's", "M": "Macy's",
    "ORLY": "O'Reilly Auto", "YUM": "Yum! Brands|Yum Brands", "FOXA": "21st Century Fox|Twenty-First Century Fox",
    "FOX": "21st Century Fox|Twenty-First Century Fox", "NWSA": "News Corp", "NWS": "News Corp",
    "DISCA": "Discovery Communications", "DISCK": "Discovery Communications", "UAA": "Under Armour", "UA": "Under Armour",
    "ETFC": "E*Trade|E-Trade", "SPGI": "S&P Global|Standard & Poor's", "LLL": "L3 Technologies|L-3 Communications",
    "LH": "LabCorp|Laboratory Corporation of America", "CBG": "CBRE", "HCN": "Welltower|Health Care REIT",
    "BHGE": "Baker Hughes", "XL": "XL Group|XL Catlin", "PM": "Philip Morris International", "MO": "Altria",
    "GPS": "Gap Inc", "TGT": "Target Corporation|Target Corp", "V": "Visa Inc", "BLL": "Ball Corporation",
    "SO": "Southern Company", "MOS": "Mosaic Company", "PGR": "Progressive Corporation|Progressive Insurance",
    "COO": "Cooper Companies", "D": "Dominion Energy|Dominion Resources", "ED": "Con Edison|Consolidated Edison",
    "CA": "CA Technologies", "XOM": "ExxonMobil|Exxon Mobil|Exxon", "CME": "CME Group", "HCA": "HCA Healthcare|HCA Holdings",
    "ABT": "Abbott Laboratories", "BAX": "Baxter International", "WAT": "Waters Corporation", "VRTX": "Vertex Pharmaceuticals",
    "HLT": "Hilton Worldwide", "CAT": "Caterpillar Inc", "DE": "John Deere|Deere & Company", "K": "Kellogg's|Kellogg Company",
    "HSY": "Hershey Company|Hershey's", "CCL": "Carnival Corporation|Carnival Cruise", "GLW": "Corning Inc",
    "XYL": "Xylem Inc", "ANTM": "Anthem Inc", "APA": "Apache Corporation", "DOV": "Dover Corporation",
    "HRS": "Harris Corporation", "HES": "Hess Corporation", "WMB": "Williams Companies", "MU": "Micron Technology",
    "BRK.B": "Berkshire Hathaway", "BF.B": "Brown-Forman", "TIF": "Tiffany & Co", "RE": "Everest Re",
    "GE": "General Electric", "GM": "General Motors", "IBM": "IBM", "CVS": "CVS", "O": "Realty Income",
    "L": "Loews", "A": "Agilent", "KEY": "KeyCorp", "RSG": "Republic Services", "INFO": "IHS Markit",
    "AAL": "American Airlines", "DAL": "Delta Air Lines", "LUV": "Southwest Airlines", "MS": "Morgan Stanley",
    "TWX": "Time Warner", "AET": "Aetna", "CI": "Cigna", "MCK": "McKesson", "CF": "CF Industries", "IT": "Gartner",
    "RHT": "Red Hat", "COL": "Rockwell Collins", "DWDP": "DowDuPont", "SNI": "Scripps Networks",
    "AON": "Aon plc|Aon Corporation", "AIG": "American International Group|AIG", "VZ": "Verizon",
    "CSCO": "Cisco", "ADBE": "Adobe Systems|Adobe Inc", "COST": "Costco", "TRV": "Travelers Companies",
    "IFF": "International Flavors & Fragrances", "WEC": "WEC Energy", "VFC": "VF Corporation|V.F. Corporation",
    "QCOM": "Qualcomm", "NDAQ": "Nasdaq Inc|Nasdaq OMX", "NLSN": "Nielsen Holdings|Nielsen Company",
    "CMI": "Cummins Inc", "ETN": "Eaton Corporation", "KMX": "CarMax", "PDCO": "Patterson Companies",
    "STT": "State Street Corporation|State Street Corp", "TPR": "Tapestry Inc|Coach Inc", "ANDV": "Andeavor|Tesoro",
    "ANTM": "Anthem Inc|WellPoint", "AGN": "Allergan|Actavis", "WBA": "Walgreens", "CB": "Chubb|ACE Limited",
    "KHC": "Kraft Heinz|Kraft Foods", "AJG": "Arthur J. Gallagher", "MKC": "McCormick & Company",
    "MRK": "Merck & Co", "MCO": "Moody's",
}

SUFFIX = re.compile(r"(,?\s+(Inc\.?|Incorporated|Corp\.?|Corporation|Co\.?|Company|Cos\.|Companies|Ltd\.?|Limited|plc|Plc|PLC|"
                    r"N\.V\.|Holdings?|Group|Class [ABC]|\(The\)|A))+$")


def auto_name(name):
    cleaned = SUFFIX.sub("", name.replace("Int'l", "International")).strip(" ,")
    cleaned = re.sub(r"^The\s+", "", cleaned)
    cleaned = re.sub(r"\s*&$", "", cleaned)
    if len(cleaned) >= 4:
        return cleaned
    first = name.split()[0].strip(",")
    return first if re.fullmatch(r"[A-Z]{3}", first) else ""   # 3-letter names like CSX or PPL


def main(list_path, prices_path, out_path):
    names = {row["Symbol"]: row["Name"] for row in csv.DictReader(open(list_path, newline=""))}
    names.update(MISSING_FROM_2018_LIST)
    tickers = sorted({row["Name"].strip() for row in csv.DictReader(open(prices_path, newline=""))})
    with open(out_path, "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["ticker", "company", "match_names", "rule"])
        for ticker in tickers:
            company = names.get(ticker, "")
            if ticker in MANUAL:
                match, rule = MANUAL[ticker], "manual"
            else:
                match = auto_name(company)
                rule = "auto" if match else "not_matched"
            writer.writerow([ticker, company, match, rule])
    print("tickers:", len(tickers))


if __name__ == "__main__":
    main(*sys.argv[1:4])

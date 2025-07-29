import requests
import json
import os

class CIKLookup:
    def __init__(self, use_cache=False, cache_path="company_tickers.json"):
        self.company_name_map = {}
        self.ticker_map = {}
        self._load_data(use_cache=use_cache, cache_path=cache_path)

    def _load_data(self, use_cache=False, cache_path="company_tickers.json"):
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {
            "User-Agent": "Mashiur mashiurrahman17675@gmail.com",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }

        try:
            if use_cache and os.path.exists(cache_path):
                print(f"Loading data from cache: {cache_path}")
                with open(cache_path, "r") as f:
                    data = json.load(f)
            else:
                print("Fetching fresh data from SEC...")
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                with open(cache_path, "w") as f:
                    json.dump(data, f)

            for entry in data.values():
                cik_str = str(entry["cik_str"]).zfill(10)
                name = entry["title"].strip()
                ticker = entry["ticker"].strip().upper()

                self.company_name_map[name.lower()] = (cik_str, name, ticker)
                self.ticker_map[ticker] = (cik_str, name, ticker)

            print(f"Loaded {len(self.ticker_map)} companies.")
        
        except Exception as e:
            print(f"Error loading data: {e}")

    def ticker_to_cik(self, ticker_symbol):
        key = ticker_symbol.strip().upper()
        result = self.ticker_map.get(key)
        if not result:
            print(f"Ticker symbol '{ticker_symbol}' not found.")
        return result


if __name__ == "__main__":
    cik_lookup = CIKLookup(use_cache=True)

    print("\n🔍 Enter a stock ticker to look up its CIK. Type 'exit' to quit.")
    while True:
        user_input = input("Ticker: ").strip()
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        result = cik_lookup.ticker_to_cik(user_input)
        if result:
            cik, name, ticker = result
            print(f"Result — CIK: {cik}, Name: {name}, Ticker: {ticker}\n")

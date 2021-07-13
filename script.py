import json
import sys
import requests
from datetime import datetime
from bs4 import BeautifulSoup as bs
import hashlib


class parse:
    def __init__(self, html):
        soup = bs(html, "html.parser")
        self.get_datetime()
        self.get_product_name(soup)
        self.get_previous_price(soup)
        self.get_current_price(soup)
        self.get_hash()

    def get_datetime(self):
        self.datetime = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M")

    def get_product_name(self, soup):
        product_title = soup.find("h1", {"class": "product-single__title"}).text.strip()
        self.product_name = product_title

    def get_previous_price(self, soup):
        previous_price = soup.find(id="ComparePrice-product-template")
        if previous_price is not None:
            self.previous_price = previous_price.text.strip()
        else:
            self.previous_price = None

    def get_current_price(self, soup):
        current_price = soup.find(id="ProductPrice-product-template")
        if current_price is not None:
            self.current_price = current_price.text.strip()
        else:
            self.current_price = None

    def get_hash(self):
        m = hashlib.md5()
        for s in (self.product_name, self.previous_price, self.current_price):
            m.update(str(s).encode())
        self.hash = m.hexdigest()


r = requests.get("https://www.festoolrecon.com/")
if r.status_code == 200:
    ad = parse(r.text)
    data = vars(ad)
    json.dump(data, sys.stdout)
    sys.stdout.write("\n")

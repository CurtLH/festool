import json
import sys
import requests
from datetime import datetime
from time import sleep
from bs4 import BeautifulSoup as bs


class parse:
    def __init__(self, html):
        soup = bs(html, "html.parser")
        self.get_datetime()
        self.get_product_name(soup)
        self.get_previous_price(soup)
        self.get_current_price(soup)

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


def get_data():

    r = requests.get("https://www.festoolrecon.com/")
    if r.status_code == 200:
        ad = parse(r.text)
        data = vars(ad)
    return data


if __name__ == "__main__":

    # set inital value for product name
    previous_product_name = None

    # run continuously
    while True:
        data = get_data()
        if data["product_name"] != previous_product_name:
            json.dump(data, sys.stdout)
            sys.stdout.write("\n")
            previous_product_name = data["product_name"]
        else:
            pass
        sleep(60)

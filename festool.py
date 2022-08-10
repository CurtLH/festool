import logging
import os
import sys
from slack import WebClient
from slack.errors import SlackApiError
import requests
import psycopg2
from bs4 import BeautifulSoup as bs

# set up basic logging
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


class parse:
    def __init__(self, html):
        soup = bs(html, "html.parser")
        self.get_product_name(soup)
        self.get_original_price(soup)
        self.get_refurb_price(soup)
        self.calc_discount()

    def get_product_name(self, soup):
        product_name = soup.find("h1", {"class": "product-single__title"}).text.strip()
        self.product_name = product_name

    def get_original_price(self, soup):
        original_price = soup.find(id="ComparePrice-product-template")
        if original_price is not None:
            self.original_price = float(
                original_price.text.strip().replace("$", "").replace(",", "")
            )
        else:
            self.original_price = None

    def get_refurb_price(self, soup):
        refurb_price = soup.find(id="ProductPrice-product-template")
        if refurb_price is not None:
            self.refurb_price = float(
                refurb_price.text.strip().replace("$", "").replace(",", "")
            )
        else:
            self.refurb_price = None

    def calc_discount(self):
        if self.original_price is not None and self.refurb_price is not None:
            self.discount = round(1 - (self.refurb_price / self.original_price), 2)
        else:
            self.discount = None


def send_slack(body, channel="#general"):

    """
    Send Slack message
    """

    client = WebClient(token=os.getenv("slack_client"))

    try:
        response = client.chat_postMessage(channel=channel, link_names=1, text=body)
    except SlackApiError as e:
        assert e.response["ok"] is False
        assert e.response["error"]
        logging.warning(f"Error: {e.response['error']}")


if __name__ == "__main__":

    # load keywords to look for
    with open("/home/curtis/github/festool/keywords.txt", "r") as f:
        keywords = f.read().splitlines()

    # connect to the database
    conn = psycopg2.connect(
        database=os.getenv("psql_dbname"),
        user=os.getenv("psql_user"),
        password=os.getenv("psql_password"),
        host=os.getenv("psql_host"),
    )
    conn.autocommit = True
    cur = conn.cursor()
    logging.info("Successfully connected to the database")

    # get the last product found
    cur.execute(
        """
        SELECT product_name
        FROM festool
        WHERE id = (SELECT MAX(id) FROM festool)
    """
    )
    try:
        most_recent = list(cur)[0][0]
    except Exception:
        most_recent = None
    logging.info(f"Most recent product: {most_recent}")

    # get the current product available
    r = requests.get("https://www.festoolrecon.com/")
    if r.status_code != 200:
        logging.warning("Request failed")
        sys.exit()

    else:
        # parse the HTML
        logging.info("Successfully retreived web page")
        ad = parse(r.text)
        logging.info("Parsed fields from HTML")

        # check if product is new
        if ad.product_name == most_recent:
            logging.info(f"Still available: {ad.product_name}")
            pass

        # if the item is new...
        else:
            # insert into the database
            cur.execute(
                """
                INSERT INTO festool (
                    product_name,
                    original_price,
                    refurb_price,
                    discount
                )
                VALUES (%s, %s, %s, %s)
                """,
                [ad.product_name, ad.original_price, ad.refurb_price, ad.discount],
            )
            logging.info("New record inserted into database")

            # format values for email
            product_name = ad.product_name
            discount = f"{int(ad.discount * 100)}%"
            orig_price = f"${ad.original_price:,.2f}"
            refurb_price = f"${ad.refurb_price:,.2f}"

            # write the Slack message
            body = f"{product_name} is now {discount} off at {refurb_price}. The original price is {orig_price}."

            # consturct the slack message
            if any(k.lower() in ad.product_name.lower() for k in keywords):
                body = f"@here: {body}"
            else:
                pass

            # send the email
            send_slack(body, channel="#general")

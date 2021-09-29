import logging
import os
import sys
import smtplib
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
        product_title = soup.find("h1", {"class": "product-single__title"}).text.strip()
        self.product_name = product_title

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


def send_email(user, pwd, recipient, subject, body):

    """
    Thanks to #10147455
    """

    FROM = user
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (
        FROM,
        ", ".join(TO),
        SUBJECT,
        TEXT,
    )
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        logging.info("successfully sent the mail")
    except Exception:
        logging.warning("failed to send mail")


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

            # check if the product name contains a keyword
            if any(k.lower() in ad.product_title.lower() for k in keywords):

                # create email
                subject = f"Now available: {ad.product_name} for ${ad.refurb_price}"
                body = f"""
                    The {ad.product_name} is now available at a {int(ad.discount * 100)}% discount for ${ad.refurb_price}. The original price is ${ad.original_price}.
                    \n
                    https://www.festoolrecon.com
                    """

                # send the email
                send_email(
                    os.getenv("email_user"),
                    os.getenv("email_pwd"),
                    "CurtLHampton@gmail.com",
                    subject,
                    body,
                )
                logging.info("Email sent")

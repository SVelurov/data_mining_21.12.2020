import datetime as dt
import dotenv
import requests
import bs4
from urllib.parse import urljoin
import pymongo as pm

dotenv.load_dotenv(".env")
MONTHS = {
    "янв": 1,
    "фев": 2,
    "мар": 3,
    "апр": 4,
    "май": 5,
    "мая": 5,
    "июн": 6,
    "июл": 7,
    "авг": 8,
    "сен": 9,
    "окт": 10,
    "ноя": 11,
    "дек": 12,
}


class MagnitParse:
    def __init__(self, start_url, mongo_db):
        self.start_url = start_url
        self.db = mongo_db

    def __get_soup(self, url) -> bs4.BeautifulSoup:
        while True:
            try:
                response = requests.get(url)
                if response.status_code != 200:
                    raise StatusCodeError(f'status {response.status_code}')
                return bs4.BeautifulSoup(response.text, 'lxml')
            except (requests.exceptions.ConnectTimeout, StatusCodeError):
                time.sleep(0.1)

    def run(self):
        for product in self.parse():
            self.save(product)

    def parse(self):
        soup = self.__get_soup(self.start_url)
        catalog_main = soup.find("div", attrs={"class": "сatalogue__main"})
        for product_tag in catalog_main.find_all("a", recursive=False):
            try:
                yield self.product_parse(product_tag)
            except AttributeError:
                pass

    def product_parse(self, product: bs4.Tag) -> dict:
        dt_parser = self.date_parse(
            product.find("div", attrs={"class": "card-sale__date"}).text
        )
        product_result = {}
        for key, value in self.get_product_template(dt_parser).items():
            try:
                product_result[key] = value(product)
            except (AttributeError, ValueError, StopIteration):
                continue
        return product_result

    def save(self, data):
        collection = self.db["magnit"]
        collection.insert_one(data)

    @staticmethod
    def date_parse(date_string: str):
        date_list = date_string.replace("с ", "", 1).replace("\n", "").split("до")
        for date in date_list:
            temp_date = date.split()
            yield dt.datetime(
                year=dt.datetime.now().year,
                day=int(temp_date[0]),
                month=MONTHS[temp_date[1][:3]],
            )

    def get_product_template(self, dates):
        product_template = {
            "url": lambda soups: urljoin(self.start_url, soups.attrs.get("href")),
            "promo_name": lambda soups: soups.find(
                "div", attrs={"class": "card-sale__header"}
            ).text,
            "product_name": lambda soups: str(
                soups.find("div", attrs={"class": "card-sale__title"}).text
            ),
            "old_price": lambda soups: float(
                ".".join(
                    itm
                    for itm in soups.find(
                        "div", attrs={"class": "label__price_old"}
                    ).text.split()
                )
            ),
            "new_price": lambda soups: float(
                ".".join(
                    itm
                    for itm in soups.find(
                        "div", attrs={"class": "label__price_new"}
                    ).text.split()
                )
            ),
            "image_url": lambda soups: urljoin(
                self.start_url, soups.find("img").attrs.get("data-src")
            ),
            "date_from": lambda _: next(dates),
            "date_to": lambda _: next(dates),
        }
        return product_template


if __name__ == "__main__":
    database = pm.MongoClient('mongodb://localhost:27017')['gb_parse']
    parser = MagnitParse("https://magnit.ru/promo/?geo=moskva", database)
    parser.run()
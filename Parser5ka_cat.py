import requests
import time
import json
from pathlib import Path


class StatusCodeError(Exception):
    def __init__(self, txt):
        self.txt = txt


class ParserCatalog:

    _params =  {
        'records_per_page': 50,
    }

    headers = {
        'User Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (HTML, like Gecko) "
                      "Chrome/87.0.4280.88 Safari/537.36"
    }

    def __init__(self, start_url, category_url):
        self.category_url = category_url
        self.start_url = start_url

    def get_categories(self, url, **kwargs):
        while True:
            try:
                response = requests.get(url, headers=self.headers, **kwargs)
                if response.status_code != 200:
                    raise StatusCodeError(f'status {response.status_code}')
                return response.json()
            except (requests.exceptions.ConnectTimeout, StatusCodeError):
                time.sleep(0.1)

    def run(self):
        for category in self.get_categories(self.category_url):
            data = {
                "name": category['parent_group_name'],
                "code": category['parent_group_name'],
                "products": [],
            }

            self._params['categories'] = category['parent_group_code']

            for products in self.parse(self, start_url):
                data['products'].extend(products)
            self.save_to_json_file(
                data,
                category['parent_group_code']
            )

    def parse(self, url):
        while url:
            response = self._get_response(url, headers=self.headers)
            data: dict = response.json()
            url = data['next']
            yield data.get('results', [])


if __name__ == '__main__':
    parser = ParserCatalog('https://5ka.ru/api/v2/special_offers/', 'https://5ka.ru/api/v2/categories/')
    parser.run()

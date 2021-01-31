import os
import requests
import bs4
from urllib.parse import urljoin
from dotenv import load_dotenv
from dateutil import parser as dtparser

from database import Database


class ParseGb:
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0"
    }

    def __init__(self, start_url, database, comments_url):
        self.start_url = start_url
        self.done_urls = set()
        self.tasks = [self.parse_task(self.start_url, self.pag_parse)]
        self.done_urls.add(self.start_url)
        self.database = database
        self.comments_url = comments_url

    @staticmethod
    def _get_soup(*args, **kwargs):
        response = requests.get(*args, **kwargs)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        return soup

    def parse_task(self, url, callback):
        def wrap():
            soup = self._get_soup(url)
            return callback(url, soup)

        return wrap

    def run(self):
        for task in self.tasks:
            result = task()
            if result:
                self.database.create_post(result)

    def post_parse(self, url, soup: bs4.BeautifulSoup):
        author_name_tag = soup.find('div', attrs={'itemprop': 'author'})
        post_id = soup.find('comments', attrs={'commentable-type': 'Post'}).get('commentable-id')
        data = {
            'post_data': {
                'url': url,
                'title': soup.find('h1', attrs={'class': 'blogpost-title'}).text,
                'date': dtparser.parse(soup.find('time', attrs={'itemprop': 'datePublished'}).get('datetime'))
            },
            'author': {
                'url': urljoin(url, author_name_tag.parent.get('href')),
                'name': author_name_tag.text,
            },
            'tags': [{
                'name': tag.text,
                'url': urljoin(url, tag.get('href'))
            } for tag in soup.find_all('a', attrs={'class': 'small'})],
            'image': {
                'url': soup.find('div', attrs={'itemprop': 'image'}).text
            },
            'comments': self._get_comments_list(post_id, self.comments_url)
        }
        return data

    def pag_parse(self, url, soup):
        gb_pagination = soup.find('ul', attrs={'class': 'gb__pagination'})
        a_tags = gb_pagination.find_all('a')
        for a in a_tags:
            pag_url = urljoin(url, a.get('href'))
            if pag_url not in self.done_urls:
                task = self.parse_task(pag_url, self.pag_parse)
                self.tasks.append(task)
                self.done_urls.add(pag_url)
        print(1)
        posts_urls = soup.find_all('a', attrs={'class': 'post-item__title'})
        for post_url in posts_urls:
            post_href = urljoin(url, post_url.get('href'))
            if post_href not in self.done_urls:
                task = self.parse_task(post_href, self.post_parse)
                self.tasks.append(task)
                self.done_urls.add(post_href)

    def _get_comments_list(self, post_id, url):
        params = {
            'commentable_type': 'Post',
            'commentable_id': post_id
        }
        response = requests.get(url, headers=self.headers, params=params)
        data = self._get_comment(response.json())
        return data

    def _get_comment(self, data):
        comments = []
        comment_dict = {}
        for comment in data:
            comment_dict['url'] = comment.get('comment').get('user').get('url')
            comment_dict['author_name'] = comment.get('comment').get('user').get('full_name')
            comment_dict['text'] = comment.get('comment').get('body')
            comment_dict['comment_id'] = comment.get('comment').get('id')
            comment_dict['parent_id'] = comment.get('comment').get('parent_id')
            comments.append(comment_dict.copy())
            children_comments = comment.get('comment').get('children')
            if children_comments:
                comments += (self._get_comment(children_comments))
        return comments


if __name__ == '__main__':

    parser = ParseGb('https://geekbrains.ru/posts', Database(os.getenv('SQL_DB')),
                     'https://geekbrains.ru/api/v2/comments')

    parser.run()
import requests
from bs4 import BeautifulSoup, Comment
import feedparser
from newspaper import Article
import datetime
from fake_useragent import UserAgent


class NewsCrawler():
    def __init__(self):
        self.user_agent = UserAgent()
        self.headers = None

    def extract_tag(self, item, tag):
        [elem.extract() for elem in item(tag)]


    def extract_comments(self, item):
        for element in item(text=lambda text: isinstance(text, Comment)):
            element.extract()
            
    def get_headers(self, shuffle_header=False):
        if self.headers is None or shuffle_header:
            self.headers = {
                'User-Agent': self.user_agent.random,
            }
        return self.headers


    def crawl_url(self, url, shuffle_header=False, language='ko'):
        try:
            # article title
            article = Article(url, language=language)
            article.download()
            article.parse()
            if not article.url:
                print("[ERROR] no url found..")
                return None        

            data = {}
            data['title'] = article.title
            data['image'] = article.meta_img
            data['crawl_url'] = url
            data['url'] = article.url

            print(article.url)
            if article.publish_date:
                data['published_at'] = article.publish_date
            else:
                data['published_at'] = datetime.datetime.now()

            res = requests.get(url, headers=self.get_headers(shuffle_header=shuffle_header))
            soup = BeautifulSoup(res.text, 'html.parser')

            for script in soup(['script', 'style']):
                script.decompose()

            body = soup.find("div", itemprop="articleBody")

            if body is None:
                body = soup.select('#articleBodyContents')
                if len(body) > 0:
                    body = body[0]
                    self.extract_comments(body)
                    self.extract_tag(body, 'img')
                    self.extract_tag(body, 'div')
                    body = str(body)
                else:
                    body = article.text
                    body = body.replace('\n','<br>')
            else:
                self.extract_comments(body)
                self.extract_tag(body, 'img')
                self.extract_tag(body, 'div')
                body = str(body)

            data['text'] = article.text
            data['body'] = body
            data['language'] = language

        except Exception as e:
            print(e)
            data = None

        return data
    
    def crawl_rss(self, rss_url, shuffle_header=False, language='ko'):
        feed = feedparser.parse(rss_url)
        data_list = []
        for post in feed.entries:
            if post.link:
                data_list.append(self.crawl_url(post.link, shuffle_header, language))

        return data_list
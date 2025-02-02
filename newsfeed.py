import requests
from bs4 import BeautifulSoup
import pymysql
import os
from pathlib import Path


class XmlRss:
    def __init__(self, xml_url):
        self.xml_url = xml_url
        self.data_dict_list = []
        self.feed_image_url = ""
        self.author = ""

    def get_feed_image_url(self, item):
        self.feed_image_url = find_image_media_content(item)
        return self.feed_image_url

    def make_data_dict_list(self, count=4):
        responses = requests.get(self.xml_url)
        soup = BeautifulSoup(responses.content, 'lxml-xml')
        self.get_author_name()

        for item in soup.findAll('item'):
            detail = {}

            title = item.find('title')
            description = item.find('description')
            link = item.find('link')
            pub_date = item.find('pubDate')

            try:
                detail['title'] = title.getText()
                detail['description'] = description.getText()
                detail['link'] = link.getText()
                detail['create_date'] = pub_date.getText()

            except AttributeError:
                continue

            detail['author'] = self.author
            feed_image = self.get_feed_image_url(item)
            detail['feed_image'] = feed_image

            self.data_dict_list.append(detail)

            return self.data_dict_list[:count]

    def get_author_name(self):
        self.author = ""


class JtbcXmlRss(XmlRss):
    def get_author_name(self):
        self.author = "JTBC"


class MbnXmlRss(XmlRss):
    def get_author_name(self):
        self.author = "MBN"


class ZDNetXmlRss(XmlRss):
    def get_author_name(self):
        self.author = "ZDNet"


class NoCutXmlRss(XmlRss):
    def get_author_name(self):
        self.author = "노컷뉴스"


def find_image_media_content(item):
    try:
        img = item.find('media:content')['url']
        return img
    except (KeyError, AttributeError):
        return None


def execute_data_list_mysql(conn, new_data_dict_list):
    if new_data_dict_list[0] == 'data_dict_list object is empty....':
        print("{0} -> {1}".format(new_data_dict_list[1], new_data_dict_list[0]))

    else:
        for new_dict in new_data_dict_list:
            cur = conn.cursor()

            cur.execute("INSERT INTO rss_feed(title, link, description, create_date, author, feed_image) VALUES(%s, %s, %s, %s, %s, %s)",
                        (new_dict['title'], new_dict['link'], new_dict['description'], new_dict['create_date'], new_dict['author'],
                         new_dict['feed_image']))

            conn.commit()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    sql_pass = Path(os.environ['SQL_CONFIG'])

    infile = open(sql_pass)
    line = infile.readline()
    db_pass = line.rstrip()

    sql_conn = pymysql.connect(user=user, host="localhost", password=db_pass, port=port, db="news",
                               charset="utf8")

    try:
        jtbc_politics = JtbcXmlRss("https://fs.jtbc.joins.com//RSS/politics.xml").make_data_dict_list(3)
        execute_data_list_mysql(sql_conn, jtbc_politics)
    finally:
        print("jtbc_politics done")

    try:
        mbn_economy = MbnXmlRss("https://www.mk.co.kr/rss/30100041/").make_data_dict_list(4)
        execute_data_list_mysql(sql_conn, mbn_economy)
    finally:
        print("mbn_economy done")

    try:
        jtbc_culture = JtbcXmlRss("https://fs.jtbc.joins.com//RSS/culture.xml").make_data_dict_list(2)
        execute_data_list_mysql(sql_conn, jtbc_culture)
    finally:
        print("jtbc_culture done")

    try:
        zdnet_it = ZDNetXmlRss("https://feeds.feedburner.com/zdkorea").make_data_dict_list(2)
        execute_data_list_mysql(sql_conn, zdnet_it)
    finally:
        print("zdnet_it done")

    try:
        nocut_gangwon = NoCutXmlRss("https://rss.nocutnews.co.kr/news/gangwon.xml").make_data_dict_list(1)
        execute_data_list_mysql(sql_conn, nocut_gangwon)
    finally:
        print("nocut_gangwon done")

    sql_conn.close()

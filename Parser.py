import requests
from googlesearch import search
from urllib.parse import urlencode, urlunparse, urlparse
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import trafilatura
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import os
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.keys import Keys
import time
from Boilerpipe import Boilerpipe
import re
import difflib

class WebParser:
    def __init__(self, time_w=10, source_count=40, browser_name='google', text_minimum=40, is_compare=False, links=False, query='', parse_type='keyword', js_parse=True):
        self.time_w = time_w
        self.source_count = source_count
        self.browser_name=browser_name
        self.text_minimum=text_minimum
        self.is_compare = is_compare
        self.parse_type = parse_type
        self.links = links
        self.query = query
        self.js_parse=js_parse
        self.browser = None
        self.extractor = Boilerpipe()

    def search_n(self):
        if self.js_parse or self.browser_name=='Bing':
            options = webdriver.FirefoxOptions()
            options.log.level = "trace"

            options.add_argument("-remote-debugging-port=9224")
            options.add_argument("-headless")
            options.add_argument("-disable-gpu")
            options.add_argument("-no-sandbox")
            binary = FirefoxBinary(os.environ.get('FIREFOX_BIN'))

            self.browser = webdriver.Firefox(
                firefox_binary=binary,
                executable_path=os.environ.get('GECKODRIVER_PATH'),
                options=options)
            #self.browser.set_page_load_timeout(self.time_w)
        if not self.links or self.parse_type=='keyword':
            self.links = []
            if self.browser_name == 'google':
                for j in search(self.query,  num=self.source_count, stop=self.source_count, pause=2, country='ua'):
                    self.links.append(j)
            else:
                self.bing_urls()
        texts = []

        for i in self.links:
            data = requests.get(i, verify=False).text
            _, result = self.extractor.extract_text(data)

            if result is not None and "JavaScript недоступно." not in result:
                if result is not None and len(result) >= self.text_minimum:
                    texts.append([result,i, 0])
            else:
                if self.js_parse:
                    text = self.crawl_url(i)
                    if text is not None and len(text) >= self.text_minimum:
                        texts.append([text, i, 0])
        if self.is_compare and self.is_compare!='no':
            texts = self.compare_texts(texts)
        final_text = self.formats_text(texts)
        if self.browser:
            self.browser.quit()
        print(len(texts))
        return final_text

    def compare_texts(self, texts):
        deleted = set()
        for i in range(len(texts)):
            for j in range(i+1, len(texts)):
                matcher = difflib.SequenceMatcher(None, texts[i][0], texts[j][0])
                ratio = matcher.ratio()
                if ratio > 0.7:
                    texts[i][2] = texts[i][2]+1
                    deleted.add(j)
                elif ratio > 0.5:
                    texts[i][2] = texts[i][2]+1
        result = []
        for i in range(len(texts)):
            if i not in deleted:
                result.append(texts[i])
        return result




    def scrollDown(self, numberOfScrollDowns):
        body = self.browser.find_element_by_tag_name("body")
        while numberOfScrollDowns >=0:
            body.send_keys(Keys.PAGE_DOWN)
            numberOfScrollDowns -= 1

    def crawl_url(self, url):
        try:
           self.browser.get(url)
           time.sleep(self.time_w)
           self.scrollDown( 20)
           elem = self.browser.find_element_by_xpath('//*')
           source = elem.get_attribute("outerHTML")
           _, result = self.extractor.extract_text(source)

           return (result)
        except:
           return ''
    def formats_text(self, texts):
        result = ''
        texts.sort(key=lambda x: x[2], reverse=True)
        for i in texts:
            if self.is_compare!='yes':
                d = ''
            else:
                d = '\tДостовірність: '+str(i[2])
            result += 'Джерело: '+ i[1]+d +'\n'+i[0] + '   \n\n\n'
        return result[0:-6]
    def bing_urls(self):
        pagination = 1
        url = urlunparse(("https", "www.bing.com", "/search", "", urlencode({"q": self.query}), ""))
        while len(self.links) < self.source_count:
            self.browser.get(url+'&first='+str(pagination))
            self.scrollDown(20)
            elem = self.browser.find_element_by_xpath('//*')
            source = elem.get_attribute("outerHTML")
            soup = BeautifulSoup(source, 'lxml')
            links = soup.find_all("div", class_='b_attribution')
            all_links = []
            for link in links:
                tags = ['<strong>', '</strong>']
                result = re.split('</cite>', re.split('<cite>', str(link))[1])[0]
                for i in tags:
                    result = re.sub(i, '', result)
                all_links.append(result)
            pagination+=10
            for i in all_links:
                if len(self.links) >= self.source_count:
                    break
                isvalid = self.url_valid(i)
                if isvalid:
                    self.links.append(isvalid)
            time.sleep(5)
    def url_valid(self, x):
        try:
            result = urlparse(x)
            r =  all([result.scheme, result.netloc])
            if r and x[-3:]!='pdf':
                return x
            elif x[0:3] =='www' and x[-3:]!='pdf':
                return 'https://'+x
            return False
        except:
            return False

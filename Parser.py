import requests
from googlesearch import search
import trafilatura
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.keys import Keys
import time
from Boilerpipe import extract_text

class WebParser:
    def __init__(self, time_w=10, source_count=40, browser_name='google', text_minimum=40, is_compare=False, links=False, query='', js_parse=True):
        self.time_w = time_w
        self.source_count = source_count
        self.browser_name=browser_name
        self.text_minimum=text_minimum
        self.is_compare = is_compare
        self.links = links
        self.query = query
        self.js_parse=js_parse
        self.browser = None

    def search_n(self):
        if not self.links:
            self.links = []
            for j in search(self.query,  num=self.source_count, stop=self.source_count, pause=2, country='ua'):
                self.links.append(j)
        if self.js_parse:
            options = Options()
            options.add_argument('--enable-javascript')
            options.headless = True
            self.browser = webdriver.Firefox(options=options, executable_path=GeckoDriverManager().install())
            self.browser.set_page_load_timeout(self.time_w)
        texts = []
        for i in self.links:
            data = trafilatura.fetch_url(i)
            _, result = extract_text(data)#trafilatura.extract(data, favor_recall=True)

            if result is not None and "JavaScript недоступно." not in result:
                if result is not None and len(result) >= self.text_minimum:
                    texts.append([result,i])
            else:
                if self.js_parse:
                    text = self.crawl_url(i)
                    if text is not None and len(text) >= self.text_minimum:
                        texts.append([text, i])
        print(len(texts))

        final_text =  self.formats_text(texts)
        print(final_text)
        return final_text
        #print(result)


    def scrollDown(self, numberOfScrollDowns):
        body = self.browser.find_element_by_tag_name("body")
        while numberOfScrollDowns >=0:
            body.send_keys(Keys.PAGE_DOWN)
            numberOfScrollDowns -= 1
     #  return browser

    def crawl_url(self, url):
        try:
           self.browser.get(url)
           time.sleep(self.time_w)
           self.scrollDown( 20)
           elem = self.browser.find_element_by_xpath('//*')
           source = elem.get_attribute("outerHTML")
           # print(source)
           _, result = extract_text(source)#trafilatura.extract(source, favor_recall=True)
           #print('------------------\n')
           #print(result)
           return (result)
        except:
           return ''
    def formats_text(self, texts):
        result = ''
        for i in texts:
            result += 'Джерело: '+ i[1]+'\n'+i[0] + '\n\n'
        return result

#a = WebParser(query='a star algorithm', source_count=10)
#a.search_n()
import re
a = []
strin = 'sss saw2    dsdsd 3dsd dddds s f. -'
for i in list(filter(None, re.split('\w+', 'sss saw2    dsdsd 3dsd dddds s f. -'))):
    sp = strin.split(i, 1)
    a.append(sp[0])
    strin = sp[1]
print(a)
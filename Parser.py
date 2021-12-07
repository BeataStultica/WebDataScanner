import requests
from googlesearch import search
import trafilatura
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.keys import Keys
import time


def search_n(time=10, source_count=40, browser='google', text_minimum=40, is_compare=False, links=False, query='', js_parse=True):
    if links==False:
        links = []
        for j in search(query,  num=source_count, stop=source_count, pause=2, country='ua'):
            links.append(j)
    if js_parse:
        options = Options()
        options.add_argument('--enable-javascript')
        options.headless = True
        browser = webdriver.Firefox(options=options, executable_path=GeckoDriverManager().install())
        browser.set_page_load_timeout(time)
    texts = []
    for i in links:
        data = trafilatura.fetch_url(i)
        result = trafilatura.extract(data, favor_recall=True)

        if result is not None and "JavaScript недоступно." not in result:
            if result is not None and len(result) >= text_minimum:
                texts.append([result,i])
        else:
            if js_parse:
                text = crawl_url(i, browser, time)
                if text is not None and len(text) >= text_minimum:
                    texts.append([text, i])
    print(len(texts))
    for i in texts:
        print('\n---------')
        print(i)
    #print(result)


def scrollDown(browser, numberOfScrollDowns):
    body = browser.find_element_by_tag_name("body")
    while numberOfScrollDowns >=0:
        body.send_keys(Keys.PAGE_DOWN)
        numberOfScrollDowns -= 1
    return browser

def crawl_url(url, browser, times=10):
    try:
       browser.get(url)
       time.sleep(times)
       browser = scrollDown(browser, 20)
       elem = browser.find_element_by_xpath('//*')
       source = elem.get_attribute("outerHTML")
       # print(source)
       result = trafilatura.extract(source, favor_recall=True)
       #print('------------------\n')
       #print(result)
       return (result)
    except:
       return ''


search_n(query='a star algorithm')
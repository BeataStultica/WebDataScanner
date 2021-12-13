import unittest
from Boilerpipe import Boilerpipe, Text, ParseState, wc
from Parser import WebParser
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import requests
from flask_socketio import SocketIO
class TestMethods(unittest.TestCase):
    def test_wc(self):
        self.assertEqual(wc('addddd  4ds 3 dd .---->'), 4)
    def test_recalc(self):
        text = Text('das.')
        text.text = 'jsjsj Sasas eeeee \n QQQQQQQQ 002 s.'
        wc = text.wordcount
        l = text.linecount
        ld = text.link_density
        wd = text.word_density
        uc = text.upper_case_density
        p = text.puncts
        self.assertEqual(wc, 1)
        self.assertEqual(l ,1)
        self.assertEqual(ld, 0)
        self.assertEqual(wd, 1)
        self.assertEqual(uc, 0)
        self.assertEqual(p, 1)
        text.recalc()
        wc = text.wordcount
        l = text.linecount
        ld = text.link_density
        wd = text.word_density
        uc = text.upper_case_density
        p = text.puncts
        self.assertEqual(wc, 6)
        self.assertEqual(l, 2)
        self.assertEqual(ld, 0)
        self.assertEqual(wd, 3)
        self.assertAlmostEqual(uc, 0.33333, places=5)
        self.assertEqual(p, 1)
    def test_merge(self):
        text1 = Text('fff - ')
        text2 = Text('eee!')
        text1.merge(text2)
        self.assertEqual(text1.text, 'fff -  eee!')
    def test_reverse_merge(self):
        text1 = Text('fff - ')
        text2 = Text('eee!')
        text1.reverse_merge(text2)
        self.assertEqual(text1.text, 'eee! fff - ')
    def test_is_content(self):
        text1 = Text('fff - ')
        text1.labels.add('content')
        self.assertEqual(text1.is_content, True)
        text1.labels.add('ignore')
        self.assertEqual(text1.is_content, False)
    def test_flush(self):
        state = ParseState()
        state.curr_text = ' dd aw'
        state.flush()
        self.assertEqual(state.parts[0].text, ' dd aw')
    def test_character(self):
        state = ParseState()
        state.curr_text = '-'
        a = 'html PUBLIC'
        state.characters(a)
        self.assertEqual(state.curr_text, '')
        state.tags.append('b')
        b = 'dddd3 addd  3 ssd  3 dsd ss dd'
        state.characters(b)
        self.assertEqual('ignore' in state.parts[0].labels, True)
    def test_parse_html(self):
        b = Boilerpipe()
        data = requests.get('https://en.wikipedia.org/wiki/Minimax', verify=False).text
        result = b.parse_html(data)
        self.assertGreaterEqual(len(result.parts), 10)
    def test_text_extract(self):
        b = Boilerpipe()
        data = requests.get('https://en.wikipedia.org/wiki/Minimax', verify=False).text
        _, res = b.extract_text(data)
        self.assertGreaterEqual(len(res), 300)
    def test_url_valid(self):
        p = WebParser()
        self.assertEqual(p.url_valid('http://sssss.com'), 'http://sssss.com')
        self.assertEqual(p.url_valid('www.google.com'), 'https://www.google.com')
        self.assertEqual(p.url_valid('google.com'), False)
        self.assertEqual(p.url_valid('http://www.ddsd.pdf'), False)
    '''
    def test_bing(self):
        p = WebParser(query='minimax algorithm', source_count=5)
        options = Options()
        options.add_argument('--enable-javascript')
        options.headless = True
        p.browser = webdriver.Firefox(options=options, executable_path=GeckoDriverManager().install())
        p.browser.set_page_load_timeout(5)
        p.bing_urls()
        self.assertEqual(len(p.links), 5)
    
    def test_search_n(self):
        socketio = SocketIO(app, cors_allowed_origins="*")
        p =WebParser(links=['https://en.wikipedia.org/wiki/Minimax', 'https://en.wikipedia.org/wiki/Artificial_intelligence'], parse_type='links', is_compare=True, js_parse=False)
        r = p.search_n(socketio, 'drjs2239dj223193')
        self.assertEqual(len(r.split('\n\n\n')), 2)
    '''



if __name__ == '__main__':
    unittest.main()

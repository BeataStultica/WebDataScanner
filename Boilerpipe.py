import re
from bs4 import BeautifulSoup as BS, Tag, Comment
from cleaners import HTMLcleaners
import time


def wc(text):
    return len(list(filter(None, re.split('\w+', text))))


class Text:
    def __init__(self, text='',  ignore=0, tags=[]):
        self.cleaners = HTMLcleaners()
        self.text = self.cleaners.clean_html(text)
        self.ignore = ignore
        self.tags = tags
        self.labels = set()
        self.wordcount = 0
        self.linecount = 0
        self.link_density = 0
        self.word_density = 1
        self.upper_case_density = 0
        self.puncts = 0
        self.recalc()

    def recalc(self):
        self.wordcount = wc(self.text)
        self.linecount = self.text.count('\n') + 1
        self.upper_case_density, self.puncts = self.calc_upper_case(self.text)
        if self.wordcount:
            self.word_density = float(self.wordcount) / self.linecount
        if 'a' in self.tags:
            self.link_density = float(self.wordcount) / self.tags.count('a')

    def merge(self, other):
        self.text += ' ' + other.text
        self.labels |= other.labels
        self.recalc()

    def reverse_merge(self, other):
        self.text = other.text + ' ' + self.text
        self.labels |= other.labels
        self.recalc()
    def calc_upper_case(self, text):
        words = []
        puncts = ['.', '!', '?']
        punct_coin = 0
        for i in puncts:
            if i in text:
                punct_coin+=1
        for i in list(filter(None, re.split('\w+', text))):
            sp = text.split(i, 1)
            words.append(sp[0])
            text = sp[1]
        if len(text) >0:
            words.append(text)
        count_up = 0
        for w in words:
            if len(w)>0:
                if w[0].isupper():
                    count_up += 1
        return (count_up / (len(words)+0.00001), punct_coin)
    @property
    def is_content(self):
        return 'content' in self.labels and 'ignore' not in self.labels

    def __len__(self):
        return len(self.text)


class ParseState():
    def __init__(self):
        self.parts = []
        self.title = ''
        self.curr_text = ''
        self.tags = []
        self.ignore_depth = 0
        self.__actions = {}
        self.fill_actions()
        self.cleaners = HTMLcleaners()
    def fill_actions(self):
        self.__actions['a'] = 'anchor'
        self.__actions['body'] = 'body'
        self.__actions['br'] = 'NOP'
        self.__actions['div'] = 'id'
        self.__actions['title'] = 'title'
        self.__actions['p'] = 'paragraph'
        ignorable = ['style', 'script', 'footer', 'option', 'objects', 'embed', 'applet', 'link', 'abbr', 'acronym',
                     'noscript']
        self.__actions.update(dict.fromkeys(ignorable, 'ignore'))
        inline = ['strike', 'u', 'b', 'i', 'em', 'strong', 'span', 'sup', 'code', 'tt',
                  'sub', 'var', 'abbr', 'acronym', 'font', 'inline']
        self.__actions.update(dict.fromkeys(inline, 'inline'))
        blocks = ['li', 'h1', 'h2', 'h3']
        self.__actions.update(dict.fromkeys(blocks, 'block'))

    def flush(self, *labels):
        curr = self.curr_text.strip()
        if curr:
            self.parts.append(
                Text(self.curr_text, self.ignore_depth, self.tags[:]))
            self.parts[-1].labels |= set(labels)
        self.curr_text = ''


    def tag_start(self, name, attr):
        action = self.__actions.get(name, None)
        self.tags.append(name)
        if action == 'anchor':
            pass
        elif action == 'ignore':
            self.flush()
            self.ignore_depth += 1
        elif action == 'body':
            self.flush()
        elif action == 'inline':
            self.curr_text = self.curr_text.strip(' ') + ' '
        elif action == 'block':
            self.flush()
        elif action == 'paragraph':
            self.flush()
        elif action == 'title':
            self.flush()
        else:
            self.flush()
            return

    def characters(self, text):
        if text.strip().startswith('html PUBLIC'):
            self.curr_text = ''
            return
        if self.tags[-1] in {'b', 'em', 'i', 'strong'}:
            if wc(text) > 5:
                self.flush()
                self.curr_text += text
                self.flush('ignore', 'ignore_inline_' + self.tags[-1])
                return
        self.curr_text += text

    def tag_end(self, name):
        action = self.__actions.get(name, None)
        if action == 'anchor':
            pass
        elif action == 'ignore':
            self.flush()
            self.ignore_depth -= 1
        elif action == 'body':
            self.flush()
        elif action == 'inline':
            self.curr_text = self.curr_text.strip() + ' '
        elif action == 'block':
            self.flush(name, 'heading')
        elif action == 'paragraph':
            self.flush('maybe_content', 'maybe_content_paragraph')
        elif action == 'title':
            self.flush('title')
        else:
            self.flush()
        assert name == self.tags.pop()
    def __str__(self):
        return '<%s %d:%r>' % (self.__class__.__name__, len(self.parts), map(len, self.parts))

class Boilerpipe:
    def __init__(self, cud=0.2, nud=0.2, pud=0.2, tp=2, cld=0.333333, pld=0.555556, cwd=9, nwd=10, pwd=4):
        self.cleaners = HTMLcleaners()
        self.cud = cud
        self.nud = nud
        self.pud = pud
        self.tp = tp
        self.cld = cld
        self.pld = pld
        self.cwd = cwd
        self.nwd = nwd
        self.pwd = pwd

    def descend(self, node, state):
        state.tag_start(node.name.lower(), node)
        for child in node.childGenerator():
            if isinstance(child, Tag):
                self.descend(child, state)
            elif not isinstance(child, Comment):
                state.characters(child)
        state.tag_end(node.name.lower())


    def parse_html(self, html):
        timer = time.time()
        #print('======')
        html = self.cleaners.translate_microsoft(html)
        html = self.cleaners.translate_nurses(html)
        #print('translate_time: ' + str(time.time() - timer))
        bs = BS(html, 'lxml')
        state = ParseState()
        timer = time.time()
        try:
            self.descend(bs, state)
            #print('descend time: ' + str(time.time() - timer))
            return state
        except:
            #print('stack overflow')
            return state


    def merge_text_density(self, blocks):
        for prev, curr in zip([Text()] + blocks, blocks):
            if prev.wordcount and curr.wordcount and (prev.wordcount + curr.wordcount) > 30:
                if (0.5 < (prev.word_density / curr.word_density) < 2.0) :
                    curr.reverse_merge(prev)
                    prev.labels.add('ignore')
                    prev.labels.add('ignore_merge_text_density')
        return


    def density_marker(self, blocks):
        for prev, curr, next in zip([Text()] + blocks, blocks, blocks[1:] + [Text()]):
            if curr.link_density <= self.cld:
                if prev.link_density <= self.pld:
                    if curr.word_density <= self.cwd:
                        if next.word_density <= self.nwd:
                            if prev.word_density <= self.pwd:
                                use = False
                            else:
                                use = True
                        else:
                            use = True
                    else:
                        if next.word_density:
                            use = True
                        else:
                            use = False
                    if curr.upper_case_density >= self.cud:
                        if next.upper_case_density >= self.nud:
                            if prev.upper_case_density >= self.pud or (curr.puncts + prev.puncts+next.puncts <= self.tp):
                                use = False
                            elif use is True:
                                use = True
                        elif (curr.puncts + prev.puncts+next.puncts <= self.tp) and prev.upper_case_density >=self.pud:
                            use = False
                        elif use is True:
                            use = True
                    else:
                        if next.upper_case_density and use is True:
                            use = True
                        else:
                            use = False

            else:
                use = False
            if use:
                curr.labels.add('content')
                curr.labels.add('content_density_marker')
            else:
                curr.labels.discard('content')
                curr.labels.discard('content_density_marker')


    def ignore_comments(self, blocks):
        for block in blocks:
            if block.text.lower().startswith(('sign in', 'log in', 'forgot your password?',
                                              'create account', 'sign In', 'you are using an outdated browser')):
                block.labels.add('ignore')
                block.labels.add('ignore_ignore_comments')
        return


    def simple_filter(self, html):
        page = self.parse_html(html)
        blocks = page.parts
        blocks = [block for block in blocks if not block.ignore]
        # density_marker(blocks)
        self.merge_text_density(blocks)
        blocks = [block for block in blocks if 'ignore' not in block.labels]
        self.density_marker(blocks)
        page.good = [block for block in blocks if block.is_content]
        #print(page.good)
    #    print('---')
    #    print(page.good[-2].text + str(page.good[-2].upper_case_density) +' p '+ str(page.good[-2].puncts))
    #    print(page.good[-1].text + str(page.good[-1].upper_case_density) +' p '+ str(page.good[-1].puncts))
    #    print(page.good[-3].text + str(page.good[-3].upper_case_density)+ ' p '+ str(page.good[-3].puncts))

        page.good = [block for block in blocks if block.is_content]
        return page


    def clean_body(self, body):
        body = body.strip()
        if body:
            newbody = self.cleaners.strip_timestamp(body)
            if newbody != body:
                body = self.cleaners.strip_partial_sentence(newbody)

        return body


    def extract_text(self, html):
        import time
        import func_timeout
        def a():
            timer = time.time()
            page = self.simple_filter(html)
            #print('Ts ' + str(time.time() - timer))
            body = ''
            timer = time.time()
            for p in page.good:
                if time.time() - timer < 10:
                    body += self.clean_body(p.text) + ' '
                    #print('Ts -' + str(time.time() - timer))
                else:
                    body +=p.text

            return '', body
        try:
            my_square = func_timeout.func_timeout(
                10, a
            )
            return my_square
        except func_timeout.FunctionTimedOut:
            print('error')
            return '', ''


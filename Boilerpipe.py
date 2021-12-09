import re
from bs4 import BeautifulSoup as BS, Tag, Comment
import cleaners

actions = {}
actions['a'] = 'anchor'
actions['body'] = 'body'
actions['br'] = 'NOP'
actions['div'] = 'id'
actions['title'] = 'title'
actions['p'] = 'paragraph'
ignorable = ['style', 'script', 'footer', 'option', 'objects', 'embed', 'applet', 'link', 'abbr', 'acronym', 'noscript']
actions.update(dict.fromkeys(ignorable, 'ignore'))
inline = ['strike', 'u', 'b', 'i', 'em', 'strong', 'span', 'sup', 'code', 'tt',
          'sub', 'var', 'abbr', 'acronym', 'font', 'inline']
actions.update(dict.fromkeys(inline, 'inline'))
blocks = ['li', 'h1', 'h2', 'h3']
actions.update(dict.fromkeys(blocks, 'block'))

def apply_font(start, txt):
    if not txt:
        return start
    delta = re.match(('([+-]\d+)'), txt)
    absolute = re.match('(\d+)', txt)
    if txt == 'smaller':
        return start - 1
    elif txt == 'larger':
        return start + 1
    elif delta:
        try:
            return start + int(delta.group(1))
        except TypeError:
            pass
    elif absolute:
        try:
            return int(absolute.group(1))
        except TypeError:
            pass
    return start

def wc(text):
    return len(list(filter(None, re.split('\w+', text))))

class Text(object):
    def __init__(self, text='', depth=0, ignore=0, tags=[], ids=[]):
        self.text = cleaners.clean_html(text)
        self.depth = depth
        self.ignore = ignore
        self.tags = tags
        self.ids = ids
        self.labels = set()
        self.wordcount = 0
        self.linecount = 0
        self.link_density = 0
        self.word_density = 0
        self.recalc()

    def recalc(self):
        self.wordcount = wc(self.text)
        self.linecount = self.text.count('\n') + 1
        if self.wordcount:
            self.word_density = float(self.wordcount) / self.linecount
        if 'a' in self.tags:
            self.link_density = float(self.wordcount) / self.tags.count('a')

    def merge(self, other):
        self.text += ' ' + other.text
        self.labels |= other.labels
        self.recalc()

    @property
    def is_content(self):
        return 'content' in self.labels and 'ignore' not in self.labels

    def __len__(self):
        return len(self.text)

    def __repr__(self):
        return '<%s depth=%d ignore=%d tags=%r ids=%r labels=%r text=%r>' % (self.__class__.__name__, self.depth, self.ignore, self.tags, self.ids, self.labels, self.text)


class ParseState(object):
    def __init__(self):
        self.parts = []
        self.title = u''
        self.curr_text = u''
        self.curr_ids = []
        self.tags = []
        self.ignore_depth = 0
        self.anchor_depth = 0
        self.body_depth = 0
        self.font_sizes = [3]


    def flush(self, *labels):
        curr = self.curr_text.strip()
        if curr:
            self.parts.append(Text(self.curr_text, len(self.tags) + 1, self.ignore_depth, self.tags[:], self.curr_ids[:]))
            self.parts[-1].labels |= set(labels)
        self.curr_text = ''

    def tag_start(self, name, attr):
        action = actions.get(name, None)
        self.tags.append(name)
        try:
            self.curr_ids.append(attr['id'])
        except KeyError:
            self.curr_ids.append('')
        if action == 'anchor':
            self.anchor_depth += 1
            assert self.anchor_depth == 1, "Anchor tags can't be nested"
        elif action == 'ignore':
            self.flush()
            self.ignore_depth += 1
        elif action == 'body':
            self.flush()
            self.body_depth += 1
        elif action == 'inline':
            self.curr_text = self.curr_text.strip(' ') + ' '
            if name == 'font':
                self.font_sizes.append(apply_font(self.font_sizes[-1], attr.get('size', None)))
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
        action = actions.get(name, None)
        if action == 'anchor':
            self.anchor_depth -= 1
        elif action == 'ignore':
            self.flush()
            self.ignore_depth -= 1
        elif action == 'body':
            self.flush()
            self.body_depth -= 1
        elif action == 'inline':
            self.curr_text = self.curr_text.strip() + u' '
            if name == 'font':
                self.font_sizes.pop()
        elif action == 'block':
            self.flush(name, 'heading')
        elif action == 'paragraph':
            self.flush('maybe_content', 'maybe_content_paragraph')
        elif action == 'title':
            self.flush('title')
            self.title = title_cleaner(self.parts[-1].text)
        else:
            self.flush()
        assert name == self.tags.pop()
        self.curr_ids.pop()

    def __str__(self):
        return '<%s %d:%r>' % (self.__class__.__name__, len(self.parts), map(len, self.parts))


def descend(node, state):
    state.tag_start(node.name.lower(), node)
    for child in node.childGenerator():
        if isinstance(child, Tag):
            descend(child, state)
        elif not isinstance(child, Comment):
            state.characters(child)
    state.tag_end(node.name.lower())


def parse_html(html):
    html = cleaners.translate_microsoft(html)
    html = cleaners.translate_nurses(html)
    bs = BS(html, 'lxml')
    state = ParseState()
    descend(bs, state)
    return state

def merge_text_density(blocks):
    for prev, curr in zip([Text()] + blocks, blocks):
        if prev.wordcount and curr.wordcount and (prev.wordcount + curr.wordcount) > 30:
            # roughly similar word densities
            if 0.5 < (prev.word_density / curr.word_density) < 2.0:
                curr.merge(prev)
                prev.labels.add('ignore')
                prev.labels.add('ignore_merge_text_density')
    return

def density_marker(blocks):
    for prev, curr, next in zip([Text()] + blocks, blocks, blocks[1:] + [Text()]):
        if curr.link_density <= 0.333333:
            if prev.link_density <= 0.555556:
                if curr.word_density <= 9:
                    if next.word_density <= 10:
                        if prev.word_density <= 4:
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
        else:
            use = False
        if use:
            curr.labels.add('content')
            curr.labels.add('content_density_marker')


def largest_block(blocks, expand_same_level=True, minwords=150):
    best = (0, -1)
    for i, block in enumerate(blocks):
        if block.is_content or 'maybe_content' in block.labels:
            if block.wordcount > minwords:
                best = max(best, (block.wordcount, i))
    longest, i = best
    if not longest:
        return
    main = blocks[i]
    main.labels.add('likely_content')
    for block in blocks:
        block.labels.add('maybe_content')
        block.labels.add('maybe_content_largest_block')

    for adjacents in [reversed(blocks[:i]), blocks[i+1:]]:
        for adj in adjacents:
            if len(adj.tags) < len(main.tags):
                break
            elif len(adj.tags) == len(main.tags):
                if not block.is_content:
                    adj.labels.discard('ignore')
                    adj.labels.add('!ignore_largest_block')
                    adj.labels.add('content')
                adj.labels.add('content_largest_block')

def merge_blocks(blocks, content_only=False, same_depth_only=False):
    it = iter(blocks)
    try:
        prev = Text()
        curr = next(it)
        while True:
            if not curr.is_content or \
               (content_only and (not curr.is_content or not prev.is_content)) or \
               (same_depth_only and len(curr.tags) != len(prev.tags)):
                prev = curr
                curr = next(it)
                continue
            else:
                prev.merge(curr)
                curr.labels.add('ignore')
                curr.labels.add('ignore_merge_blocks')
                curr = next(it)
    except StopIteration:
        pass



def ignore_comments(blocks):
    for block in blocks:
        if block.text.lower().startswith(('sign in', 'log in', 'forgot your password?',
                                          'create account','sign In', 'you are using an outdated browser')):
            block.labels.add('ignore')
            block.labels.add('ignore_ignore_comments')
    return



def title_cleaner(title):
    splitter = "\s*[\xbb|,:()\-\xa0]+\s*"
    best = sorted(re.split(splitter, title), key=len)[-1]
    best = best.replace("'", "", 1)
    return best

def simple_filter(html):
    page = parse_html(html)
    blocks = page.parts
    blocks = [block for block in blocks if not block.ignore]
    merge_text_density(blocks)
    merge_blocks(blocks)
    density_marker(blocks)
    page.good = [block for block in blocks if block.is_content]
    largest_block(blocks)
    page.good = [block for block in blocks if block.is_content]
    return page


def clean_body(body, title):
    body = body.strip()
    if body and title:
        newbody = cleaners.strip_words(body, title)
        if newbody != body:
            body = cleaners.strip_partial_sentence(body)
    if body:
        newbody = cleaners.strip_timestamp(body)
        if newbody != body:
            body = cleaners.strip_partial_sentence(newbody)

    return body

def meat2(html):
    page = simple_filter(html)
    title = page.title
    #blocks = filter(lambda x:x.wordcount>3, page.good)
    best = ''
    for p in page.good:
        best += clean_body(p.text, title)
    best = clean_body(best, title)
    return title, best


def extract_text(html):
    for func in [meat2]:
        title, body = func(html)
        if body:
            return title, body
    return '--', '--'

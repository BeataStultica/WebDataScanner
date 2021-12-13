
import functools
import re

class HTMLcleaners:
    entities = {'nbsp': ' ',
                'mdash': '-',
                'quot': "'",
                'lsquo': "'",
                'rsquo': "'",
                'ldquo': '"',
                'rdquo': '"',
                }
    def edit_distance(self, a, b):
        return len(set(a) ^ set(b)) + abs(len(a) - len(b))

    def translate_microsoft(self, txt):
        """ turn word document ungliness into ascii """
        if txt:
            txt = txt.replace(u"\u201c", '"')
            txt = txt.replace(u"\u201d", '"')
            txt = txt.replace(u"\u2018", "'")
            txt = txt.replace(u"\u2019", "'")
            txt = txt.replace(u"\u02BC", "'")
            txt = txt.replace(u"\u2063", " ")
            txt = txt.replace(u"\u2026", "...")
            txt = txt.replace(u"\u2022", "-")
            txt = txt.replace(u"\u25cf", "-")
            txt = txt.replace(u"\u2012", "-")
            txt = txt.replace(u"\u2013", "-")
            txt = txt.replace(u"\u2014", "-")
            txt = txt.replace(u"\u2015", "-")
            txt = txt.replace(u"\u2053", "-")
            txt = txt.replace(u"\u2E3A", "-")
            txt = txt.replace(u"\u2E3B", "-")
            txt = txt.replace(u"\u2025", ' ')
            txt = txt.replace(u"\xa0", ' ')
            return txt
        return ''



    def translate_html_entities(self, html):
        if not html:
            html = ''
        parts = []
        curr = 0
        '''
        for m in re.finditer('&#([xX]?)([0-9a-fA-F]+);', html):
            parts.append(html[curr:m.start()])
            ishex, number = m.groups()
            value = chr(int(number, base=(16 if (ishex) else 10)))
            parts.append(value)
            curr = m.end()
        parts.append(html[curr:])
        html = ''.join(parts)
        '''
        for code, translation in self.entities.items():
            html = html.replace('&%s;' % code, translation)
        return html

    def translate_nurses(self, txt):
        txt = txt.replace('\r\n', '\n')
        txt = txt.replace('\r', '\n')
        return txt

    def translate_whitespace(self, txt):
        txt = txt.replace('\t', ' ')
        #txt = re.sub(' +', ' ', txt)
        txt = txt.replace(' \n', '\n')
        txt = txt.replace('\n ', '\n')
        #txt = re.sub(' +', ' ', txt)
        txt = txt.replace('\n\n', '\n')
        return txt

    def clean_html(self, html):
        return self.translate_whitespace(self.translate_microsoft(self.translate_html_entities(html)))



    def strip_partial_sentence(self, text):
        return re.sub('^[^.?]{0,10}(\.|\?)\s*', '', text)

    def strip_timestamp(self, text):
        best = 0
        regexps = ['(\d{1,2}\D+20\d\d)',
                   '(\d{1,2}(:\d\d)+\s*(AM|PM|a\.m\.|p\.m\.)?\s*(ET|EST|EDT|PT|PST|PDT|CT|CST|CDT)?)',
                   '(\d{1,2}(:\d\d)*\s*(AM|PM|A\.M\.|P\.M\.)?\s*(ET|EST|EDT|PT|PST|PDT|CT|CST|CDT))',
                  ]
        for pattern, m in [(pattern, re.search(pattern, text[:50], re.IGNORECASE)) for pattern in regexps]:
            if m:
                best = max(best, m.end())
        return text[best:].strip()
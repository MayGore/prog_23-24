# https://rifmovnik.ru/find   это который на внутренних куки
# https://rifme.net/r/книги/1   это где хорошо парсить

import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import pandas as pd
from pymorphy2 import MorphAnalyzer


session = requests.session()
ua = UserAgent()

df = pd.read_csv('lines.csv', sep='; ')
for j in range(df.shape[0]):
    df.at[j, 'Last_word'] = df._get_value(j, 'Last_word').lower()


def get_rhymes(word):
    link = f'https://rifme.net/r/{word}'
    # ссылка на несуществующее слово https://rifme.net/u/мпамотв
    req = session.get(link, headers={'User-Agent': ua.random})
    text = req.text
    soup = BeautifulSoup(text, 'html.parser')
    rhymes = []
    # <ul class="rifmypodryad" id="tochnye">
    # точные рифмы
    # <li data-w="биссектриса" class="riLi">биссектр<span class="u">и</span>са</li>
    accurate_soup = soup.find_all('ul', {'class': 'rifmypodryad', 'id': 'tochnye'})
    # на некоторый страницах есть раздел менее строгие рифмы
    # <ul class="rifmypodryad" id="meneestrogie">
    loose_soup = soup.find_all('ul', {'class': 'rifmypodryad', 'id': 'meneestrogie'})
    if len(accurate_soup) == len(loose_soup) == 0:
        return rhymes
        # который в этот момент пустой
    if len(accurate_soup) > 0:
        words = [i.attrs['data-w'] for i in accurate_soup[0].find_all('li', {'class': 'riLi'})]
        rhymes.extend(words)
    if len(loose_soup) > 0:
        words = [i.attrs['data-w'] for i in loose_soup[0].find_all('li', {'class': 'riLi'})]
        rhymes.extend(words)
    return rhymes


def get_word_pos(word):
    morph = MorphAnalyzer()
    if not word.isalpha():
        return ""
    tag = morph.parse(word)[0].tag.POS
    if tag in ('VERB', 'INFN', 'PRTF', 'PRTS', 'GRND'):
        return 'V'
        # потому что так они будут записаны в боте
    if tag == 'NOUN':
        return 'N'
    if tag in ('ADJF', 'ADJS', 'COMP'):
        return 'ADJ'
    if tag == 'ADVB':
        return 'ADV'
    return 'OTHER'


def get_rhyming_lines(word, pos):
    global df
    rhyming_lines = pd.DataFrame(columns=['Title', 'Year', 'Original_line', 'Line_number', 'Last_word', 'Last_word_POS'])
    rhyming_words = get_rhymes(word)
    # might be empty => rhyming_lines will be empty
    for word in rhyming_words:
        word_pos = get_word_pos(word)
        if word_pos == '':
            continue
        if pos[word_pos]:
            with_this_word = df[df['Last_word'] == word.lower()]
            rhyming_lines = pd.concat([rhyming_lines, with_this_word], ignore_index=True)
    return rhyming_lines


# allowed_pos = {
#     'N': True,
#     'V': True,
#     'ADJ': True,
#     'ADV': True,
#     'OTHER': True
# }


# inp = input('slovo:')
# res = get_rhyming_lines(inp)
# if res.empty:
#     print("К сожалению, мы не смогли найти строчки, рифмующиеся с этим словом")
# else:
#     print(res.to_string())


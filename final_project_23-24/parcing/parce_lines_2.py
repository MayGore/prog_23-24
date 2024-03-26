import requests
from fake_useragent import UserAgent
import random
from bs4 import BeautifulSoup
import time

from pymorphy2 import MorphAnalyzer
import nltk
from nltk.tokenize import wordpunct_tokenize
nltk.download('punkt')

session = requests.session()

ua = UserAgent()


# https://www.culture.ru/literature/poems/author-ivan-bunin?page=2


def parce_pages():

    # спарсим странички
    for i in range(1, 7):
        url = f'https://www.culture.ru/literature/poems/author-ivan-bunin?page={i}'
        req = session.get(url, headers={'User-Agent': ua.random})
        page = req.text
        time.sleep(random.uniform(1.1, 1.8))
        pages.append(page)


def parce_links():
    global pages
    with open('links2.txt', 'w', encoding='utf-8') as f:
        pass
    links = []
    for page in pages:
        soup = BeautifulSoup(page, 'html.parser')
        links_this_page = ['https://www.culture.ru' + i.attrs['href']
                           for i in soup.find_all('a',  {'class': '_9OVEn'})]
        with open('links2.txt', 'a', encoding='utf-8') as f:
            for i in links_this_page:
                print(i, file=f)
        links.extend(links_this_page)


def get_word_info(line):
    #  из дз по краулингу
    morph = MorphAnalyzer()
    if type(line) != str:
        return "", ""
    line = line.replace('.', '').replace(',', '').replace(';', '').replace(':', '').replace('-', '').replace('!', '').replace('?', '').replace('(', '').replace(')', '').replace('"', '').replace("'", '')
    text = wordpunct_tokenize(line)
    word = text[-1]
    if not word.isalpha():
        return "", ""
    tag = morph.parse(word)[0].tag.POS
    return word, tag


def parce_texts():
    with open('links2.txt') as file:
        links = list(map(str.strip, file.readlines()))
    with open('../lines.csv', 'w', encoding='utf-8') as f:
        print('Title; Year; Original_line; Line_number; Last_word; Last_word_POS', file=f)
    #  для будущего датасета
    title_data = []
    year_data = []
    orig_line_data = []
    line_number_data = []
    last_word_data = []
    last_word_pos_data = []
    counter = 0
    print(len(links))

    for link in links:
        print(counter)
        counter += 1
        # парсим стишок
        req = session.get(link, headers={'User-Agent': ua.random})
        poem = req.text
        time.sleep(random.uniform(1.1, 2.2))
        res = ''
        # вытаскиваем нужную информацию
        soup = BeautifulSoup(poem, 'html.parser')

        if '<div class="xtEsw">' in str(soup):
            ttl = soup.find_all('div', {'class': 'xtEsw'})[0]
            title = str(ttl)[str(ttl).find('>') + 1:str(ttl).rfind('<')].strip().replace(';', ',')
        else:
            title = 'Без названия'

        if '<div class="ZJO6Q">' in str(soup):
            year = soup.find_all('div', {'class': 'ZJO6Q'})[0]
            a = str(year)[str(year).find('>') + 1:str(year).rfind('<')]
            year = a[0:4]
        else:
            year = 'Год написания не известен'

        text = soup.find_all('div', {'data-content': 'text'})[0]
        lines_str = str(text)[str(text).find('>') + 1:str(text).rfind('<')]
        lines_list = lines_str.replace('/', ' ').replace('br ', 'br').replace('\xa0', ' ').replace('&lrm;', '').replace('&nbsp;', '').replace('"', '').split('<br>')
        lines = list(map(str.strip, lines_list))

        # обработаем каждую строчку
        for i in range(len(lines)):
            line = lines[i].replace(';', ',')
            word, pos = get_word_info(line)
            if word == '':
                continue
            title_data.append(title)
            year_data.append(year)
            orig_line_data.append(line)
            line_number_data.append(i + 1)
            last_word_data.append(word.lower())
            last_word_pos_data.append(pos)

            res = f'{title}; {year}; {line}; {i + 1}; {word}; {pos}'
            # записываем в файл
            with open('../lines.csv', 'a', encoding='utf-8') as f:
                print(res, file=f)


def purify():
    #  забыла сначала удалить эти теги, удаляю из готового файла уже
    with open('../lines.csv', encoding='utf-8') as file:
        lines = list(map(str.strip, file.readlines()))

    res = []

    for line in lines:
        if '‎' in line or ' ' in line:
            r = line.replace('‎', '').replace(' ', ' ')
            res.append(r)
        else:
            res.append(line)
    with open('../lines.csv', 'w', encoding='utf-8') as file:
        for i in res:
            print(i, file=file)


pages = []
# parce_pages()
# parce_links()
# parce_texts()
# purify()


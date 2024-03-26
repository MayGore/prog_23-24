from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, recall_score, precision_score
import pandas as pd

import requests
from fake_useragent import UserAgent
import random
from bs4 import BeautifulSoup
import time


linreg = LinearRegression()
vectorizer = TfidfVectorizer()


def collect_data():
    # сейчас я спаршу пять страниц стихов рандомных поэтов. это примерно столько же сколько у меня всего Бунина
    # вся эта функция скопирована из кусочков в файле parcing/parce_lines_2.py
    session = requests.session()
    ua = UserAgent()
    pages = []
    for i in range(10, 15):
        url = f'https://www.culture.ru/literature/poems?page={i}'
        req = session.get(url, headers={'User-Agent': ua.random})
        page = req.text
        time.sleep(random.uniform(1.1, 1.8))
        pages.append(page)
    links = []
    for page in pages:
        soup = BeautifulSoup(page, 'html.parser')
        links_this_page = ['https://www.culture.ru' + i.attrs['href']
                           for i in soup.find_all('a', {'class': '_9OVEn'})]
        with open('parcing/links2.txt', 'a', encoding='utf-8') as f:
            for i in links_this_page:
                print(i, file=f)
        links.extend(links_this_page)
    title_data = []
    author_data = []
    year_data = []
    orig_line_data = []
    counter = 0
    print(len(links))
    with open('parcing/random_poems.csv', 'w', encoding='utf-8') as f:
        print('Title; Author; Year; Original_line', file=f)
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
        if '‎' in title or ' ' in title:
            title = title.replace('‎', '').replace(' ', ' ')

        if '<div class="IHYwd">' in str(soup):
            auth = soup.find_all('div', {'class': 'IHYwd'})[0]
            author = str(auth)[str(auth).find('>') + 1:str(auth).rfind('<')].strip().replace(';', ',')
        else:
            author = 'Автор не известен'
        if '‎' in author or ' ' in author:
            author = author.replace('‎', '').replace(' ', ' ')

        if '<div class="ZJO6Q">' in str(soup):
            year = soup.find_all('div', {'class': 'ZJO6Q'})[0]
            a = str(year)[str(year).find('>') + 1:str(year).rfind('<')]
            year = a[0:4]
        else:
            year = 'Год написания не известен'

        text = soup.find_all('div', {'data-content': 'text'})[0]
        lines_str = str(text)[str(text).find('>') + 1:str(text).rfind('<')]
        lines_list = lines_str.replace('/', ' ').replace('br ', 'br').replace('\xa0', ' ').replace('&lrm;', '').replace(
            '&nbsp;', '').replace('"', '').split('<br>')
        lines = list(map(str.strip, lines_list))

        # обработаем каждую строчку
        for i in range(len(lines)):
            line = lines[i].replace(';', ',')
            line = line.replace('.', '').replace(',', '').replace(';', '').replace(':', '').replace('-', '').replace(
                '!', '').replace('?', '').replace('(', '').replace(')', '').replace('"', '').replace("'", '')
            if '‎' in line or ' ' in line:
                line = line.replace('‎', '').replace(' ', ' ')
            title_data.append(title)
            author_data.append(author)
            year_data.append(year)
            orig_line_data.append(line)

            res = f'{title}; {author}; {year}; {line}'
            # записываем в файл
            with open('parcing/random_poems.csv', 'a', encoding='utf-8') as f:
                print(res, file=f)


def add_bunin_to_data():
    # теперь добавим в датасет имеющегося бунина. на датасете обучим модель
    df_bunin = pd.read_csv('lines.csv', sep='; ')
    with open('parcing/bunin_poems.csv', 'w', encoding='utf-8') as f:
        print('Title; Author; Year; Original_line', file=f)
    for i in range(df_bunin.shape[0]):
        dt = df_bunin.iloc[i]
        # Title; Year; Original_line; Line_number; Last_word; Last_word_POS
        res = f"{dt['Title']}; Иван Бунин; {dt['Year']}; {dt['Original_line']}"
        # записываем в файл
        with open('parcing/bunin_poems.csv', 'a', encoding='utf-8') as f:
            print(res, file=f)


def train_model():
    # взято из моего дз по ML
    df = pd.read_csv('parcing/random_poems.csv', sep='; ')
    df_bunin = pd.read_csv('parcing/bunin_poems.csv', sep='; ')
    df.dropna(inplace=True, ignore_index=True)
    df_bunin.dropna(inplace=True, ignore_index=True)

    test_size = 0.2

    x1 = df["Original_line"]
    y1 = [1 if item == "Иван Бунин" else 0 for item in df["Author"].values]
    x_train1, x_test1, y_train, y_test = train_test_split(x1, y1, test_size=test_size, random_state=42)

    x2 = df_bunin["Original_line"]
    y2 = [1 if item == "Иван Бунин" else 0 for item in df_bunin["Author"].values]
    x_train2, x_test2, y_train2, y_test2 = train_test_split(x2, y2, test_size=test_size, random_state=42)

    # я это сделала чтобы точно не было так, что бунина в train не оказалось
    x_train = pd.concat([x_train1, x_train2])
    x_test = pd.concat([x_test1, x_test2])
    y_train.extend(y_train2)
    y_test.extend(y_test2)

    x_train_transformed = vectorizer.fit_transform(x_train)
    x_test_transformed = vectorizer.transform(x_test)
    linreg.fit(x_train_transformed, y_train)

    y_pred = [0 if i < 0.5 else 1 for i in linreg.predict(x_test_transformed)]

    # print("SKL Accuracy: ", accuracy_score(y_test, y_pred))
    # print("SKL Recall: ", recall_score(y_test, y_pred))
    # print("SKL Precision: ", precision_score(y_test, y_pred))


def is_Bunin_ish(user_line):
    train_model()
    pred = [0 if i < 0.5 else 1 for i in linreg.predict(vectorizer.transform([user_line]))]
    return bool(pred[0])


# collect_data()
# add_bunin_to_data()

# print(is_Bunin_ish('fghjk%6'))

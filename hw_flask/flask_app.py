from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('agg')

app = Flask(__name__)


@app.route('/')
def hello(name=None):
    return render_template('index.html')


@app.route('/qa')
def QA(name=None):
    return render_template('index_q_a.html', )


@app.route('/stat')
def stat(name=None):
    av_age = None
    min_score = None
    max_score = None

    # for making a plot
    corr_by_ege_summ = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0]
    corr_by_ege_k = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0]
    correctness = []
    egeScores = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
                 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53,
                 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
                 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100]

    with open('static/ans.txt', mode='r') as f:
        lines = f.readlines()
        print(lines)
        for line in lines:

            if av_age is None:
                av_age = 0
            if min_score is None:
                min_score = 101
            if max_score is None:
                max_score = -1

            s = line.strip().split(';')

            av_age += int(s[1])
            min_score = min(min_score, int(s[2]))
            max_score = max(max_score, int(s[2]))

            corr_by_ege_summ[int(s[2])] += int(s[-1])
            corr_by_ege_k[int(s[2])] += 1

        if av_age is not None:
            av_age = av_age // len(lines)

    for i in range(len(corr_by_ege_k)):
        if corr_by_ege_k[i] == 0:
            correctness.append(0)
        else:
            correctness.append(corr_by_ege_summ[i] // corr_by_ege_k[i])
    # from visualisation for students
    X = egeScores
    Y = correctness
    plt.plot(X, Y)  # рисуем график - последовательно соединяем точки с координатами из X и Y
    plt.title('Среднее количество правильных ответов на тест по баллам ЕГЭ')  # заголовок
    plt.xlabel('Баллы ЕГЭ')  # подпись оси Х
    plt.ylabel('Баллы за тест')  # подпись оси Y
    plt.savefig('static/images/my_image.jpg')
    plt.show()

    return render_template('index_stat.html', av_age=av_age, min_score=min_score, max_score=max_score)


@app.route('/ans')
def check_answers(name=None):
    rez = 0
    userName = request.args.get('userName')
    age = request.args.get('age')
    egeScore = request.args.get('egeScore')
    q1 = request.args.get('q1')
    if q1 == '12':
        rez += 1
    q2 = request.args.get('q2')
    if q2 == '13':
        rez += 1
    q3 = request.args.get('q3')
    if q3 == '134':
        rez += 1
    q4 = request.args.get('q4')
    if q4 == '13':
        rez += 1
    q5 = request.args.get('q5')
    if q5 == '123':
        rez += 1
    q6 = request.args.get('q6')
    if q6 == '2':
        rez += 1
    q7 = request.args.get('q7')
    if q7 == '123':
        rez += 1
    q8 = request.args.get('q8')
    if q8 == '46':
        rez += 1
    q9 = request.args.get('q9')
    if q9 == '12':
        rez += 1
    q10 = request.args.get('q10')
    if q10 == '1':
        rez += 1
    answers = [userName, egeScore, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, rez]
    with open('static/ans.txt', mode='a+') as f:
        print(f"{userName};{age};{egeScore};{q1};{q2};{q3};{q4};{q5};{q6};{q7};{q8};{q9};{q10};{rez}", file=f)
    return render_template('index_ans.html', rez=rez, answers=answers)


if __name__ == '__main__':
    app.run(debug=False)

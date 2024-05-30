from datetime import datetime
# Импортируется функция для выбора случайного значения:
from random import randrange
from flask import Flask, abort, redirect, render_template, url_for, flash
# Импортируем класс для работы с ORM:
from flask_sqlalchemy import SQLAlchemy
# Новые импорты:
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, URLField
from wtforms.validators import DataRequired, Length, Optional


app = Flask(__name__)

# Подключаем БД SQLite:
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY'] = 'FKDLFK34KLEFQ3L3!@2932'
# Создаём экземпляр SQLAlchemy и в качестве параметра
# передаём в него экземпляр приложения Flask:
db = SQLAlchemy(app)


class Opinion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    text = db.Column(db.Text, unique=True, nullable=False)
    source = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)


# Класс формы опишите сразу после модели Opinion.
class OpinionForm(FlaskForm):
    title = StringField(
        'Введите название фильма',
        validators=[DataRequired(message='Обязательное поле'),
                    Length(1, 128)]
    )
    text = TextAreaField(
        'Напишите мнение',
        validators=[DataRequired(message='Обязательное поле')]
    )
    source = URLField(
        'Добавьте ссылку на подробный обзор фильма',
        validators=[Length(1, 256), Optional()]
    )
    submit = SubmitField('Добавить')


@app.route('/')
def index_view():
    # Определяется количество мнений в базе данных:
    quantity = Opinion.query.count()
    # Если мнений нет...
    if not quantity:
        # Если в базе пусто, при запросе к главной странице
        # пользователь увидит ошибку 500:
        abort(500)
    # Иначе выбирается случайное число в диапазоне от 0 до quantity...
    offset_value = randrange(quantity)
    # ...и определяется случайный объект:
    opinion = Opinion.query.offset(offset_value).first()
    return render_template('opinion.html', opinion=opinion)


@app.route('/add', methods=['GET', 'POST'])
def add_opinion_view():
    form = OpinionForm()
    if form.validate_on_submit():
        text = form.text.data
        # Если в БД уже есть мнение с текстом, который ввёл пользователь...
        if Opinion.query.filter_by(text=text).first() is not None:
            # ...вызвать функцию flash и передать соответствующее сообщение:
            flash('Такое мнение уже было оставлено ранее!')
            # Вернуть пользователя на страницу «Добавить новое мнение»:
            return render_template('add_opinion.html', form=form)
        opinion = Opinion(
            title=form.title.data,
            text=text,
            source=form.source.data
        )
        # Затем добавить его в сессию работы с базой данных:
        db.session.add(opinion)
        # И зафиксировать изменения:
        db.session.commit()
        # Затем переадресовать пользователя на страницу добавленного мнения:
        return redirect(url_for('opinion_view', id=opinion.id))
    # Если валидация не пройдена — просто отрисовать страницу с формой:
    return render_template('add_opinion.html', form=form)


# Тут указывается конвертер пути для id:
@app.route('/opinions/<int:id>')
# Параметром указывается имя переменной:
def opinion_view(id):
    # Теперь можно запросить нужный объект по id...
    opinion = Opinion.query.get_or_404(id)
    # ...и передать его в шаблон (шаблон тот же, что и для главной страницы):
    return render_template('opinion.html', opinion=opinion)


@app.errorhandler(500)
def internal_error(error):
    # Ошибка 500 возникает в нештатных ситуациях на сервере.
    # Например, провалилась валидация данных.
    # В таких случаях можно откатить изменения, не зафиксированные в БД,
    # чтобы в базу не записалось ничего лишнего.
    db.session.rollback()
    # Пользователю вернётся страница, сгенерированная на основе шаблона 500.html.
    # Этого шаблона пока нет, но сейчас мы его тоже создадим.
    # Пользователь получит и код HTTP-ответа 500.
    return render_template('500.html'), 500


@app.errorhandler(404)
def page_not_found(error):
    # При ошибке 404 в качестве ответа вернётся страница, созданная
    # на основе шаблона 404.html, и код HTTP-ответа 404:
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run()
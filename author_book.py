#  this is a low flask
from flask import Flask, render_template, flash, redirect, url_for
from flask import request
from flask_sqlalchemy import SQLAlchemy, models_committed
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


#创建表单类，用来添加信息
class Append(FlaskForm):
    author = StringField(label="作者：",validators=[DataRequired()])
    book = StringField(label="书籍：",validators=[DataRequired()])
    submit = SubmitField(u'添加')


app = Flask(__name__)

class Config(object):
    SQLALCHEMY_DATABASE_URI = "mysql://root:cq@127.0.0.1:3306/author_book_17"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "ASLDLAKSDLASASLKDJAKSLK"

app.config.from_object(Config)


# 1.创建数据库对象
db = SQLAlchemy(app)

# 2.创建表
class Author(db.Model):
    """作者表 一的一方"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # 关系字段
    # author.books :查询该作者的所有书籍
    # book.author : 该书籍属于哪个作者
    books = db.relationship("Book", backref="author")

    def __repr__(self):
        return "Author: %s %s" % (self.name, self.id)


class Book(db.Model):
    """书籍表 多的一方"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # 外键
    author_id = db.Column(db.Integer, db.ForeignKey("author.id"))

    def __repr__(self):
        return "Book: %s %s" % (self.name, self.id)


@app.route('/', methods=["POST", "GET"])
def author_book():
    """显示模板数据， 书籍添加接口"""
    # 0. 创建wtf表单对象
    form = Append()
    # 所有验证器全部通过才会返回True
    if form.validate_on_submit():
        #  添加书籍操作
        # 1. 获取数据 （作者名称 书籍名称）
        author_name = request.form.get("author", "")
        book_name = request.form.get("book", "")
        #1.1 查询作者
        author = Author.query.filter(Author.name == author_name).first()
        #2.0 判断作者是否存在
        if not author:
            #2.1 作者不存在 添加作者 添加书籍（将书籍关联到作者身上）
            # 创建作者对象
            author = Author(name=author_name)
            db.session.add(author)
            db.session.commit()
            # 创建书籍 注意：只有author添加到数据库之后author.id才有值
            book = Book(name=book_name, author_id=author.id)
            db.session.add(book)
            db.session.commit()
        else:
            #2.2 作者存在 添加书籍 查询书籍是否存在
            book = Book.query.filter(Book.name == book_name).first()
            #2.2.1  存在不能重复添加
            if book:
                flash("书籍已经存在不能重复添加")
            else:
                #2.2.2 书籍不存在，直接添加书籍
                book = Book(name=book_name, author_id=author.id)
                db.session.add(book)
                db.session.commit()

    # 1. 查询所有书籍数据， 查询所有作者数据
    # 注意： 当我们获取到author作者对象的时候，我们可以根据author.books获取该作者所有的书籍
    authors = Author.query.all()

    return render_template("author_book.html", authors=authors, form=form)


@app.route('/delete_author/<author_id>')
def delete_author(author_id):
    """根据作者id删除作者信息"""
    # 1.查询作者是否存在
    try:
        author = Author.query.get(author_id)
    except Exception as e:
        flash(e)

    if not author:
        flash("作者不存在不能删除")
    else:
        #TODO: 这里也需要捕获异常和回滚（留给你们练习）
        # 1.先删除书籍
        # 获取书籍列表
        books = author.books
        for book in books:
            db.session.delete(book)
        # 2.再删除作者
        db.session.delete(author)
        db.session.commit()

    # 切记：上面的操作只是将数据库的数据删除，页面需要重新查询数据刷新页面
    return redirect(url_for("author_book"))


@app.route('/delete_book/<book_id>')
def delete_book(book_id):
    """根据书籍id删除书籍信息"""
    #1.查询书籍是否存在
    try:
        book = Book.query.get(book_id)
    except Exception as e:
        flash(e)
    #2.判断书籍是否存在
    if not book:
        flash("书籍不存在不能删除")
    else:
        try:
            # 书籍存在，删除即可
            db.session.delete(book)
            db.session.commit()
        except Exception as e:
            flash(e)
            # 数据库回滚
            db.session.rollback()

    # 切记：上面的操作只是将数据库的数据删除，页面需要重新查询数据刷新页面
    return redirect(url_for("author_book"))


@models_committed.connect_via(app)
def models_committed(app, changes):
    print(app,changes)

if __name__ == '__main__':
    db.drop_all()
    db.create_all()

    # 生成数据
    au1 = Author(name='老王')
    au2 = Author(name='老尹')
    au3 = Author(name='老刘')
    # 把数据提交给用户会话
    db.session.add_all([au1, au2, au3])
    # 提交会话
    db.session.commit()
    bk1 = Book(name='老王回忆录', author_id=au1.id)
    bk2 = Book(name='我读书少，你别骗我', author_id=au1.id)
    bk3 = Book(name='如何才能让自己更骚', author_id=au2.id)
    bk4 = Book(name='怎样征服美丽少女', author_id=au3.id)
    bk5 = Book(name='如何征服英俊少男', author_id=au3.id)
    # 把数据提交给用户会话
    db.session.add_all([bk1, bk2, bk3, bk4, bk5])
    # 提交会话
    db.session.commit()
    app.run(debug=True)


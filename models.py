from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import sql
from my_log import log

import time
import shutil
import hashlib

# 数据库的路径
db_path = 'db.sqlite'
# 获取 app 的实例
app = Flask(__name__)
# 这个先不管，其实是 flask 用来加密 session 的东西
app.secret_key = 'random string'
# 配置数据库的打开方式
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(db_path)

db = SQLAlchemy(app)


def local_time(unix_time):
    return time.strftime(r'%Y/%m/%d %H:%M:%S', time.localtime(unix_time))


def convert_to_sha1(pwd):
    if len(pwd) < 3:
        return 'too-short!'
    else:
        return hashlib.sha1(pwd.encode('utf-8')).hexdigest()


# 数据库里面的一张表，是一个类
# 它继承自 db.Model
class User(db.Model):
    # 类的属性就是数据库表的字段
    # 这些都是内置的 __tablename__ 是表名
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    password = db.Column(db.String())
    sex = db.Column(db.String())
    note = db.Column(db.String(), nullable=True)
    role = db.Column(db.Integer, default=2)
    follow_count = db.Column(db.Integer, default=0)
    fan_count = db.Column(db.Integer, default=0)
    created_time = db.Column(db.DateTime(timezone=True), default=sql.func.now())
    release_time = db.Column(db.String(), default=local_time(time.time()))
    # 这是引用别的表的数据的属性，表明了它关联的东西
    blogs = db.relationship('Blog', backref='user')

    def __init__(self, form):
        super(User, self).__init__()
        self.username = form.get('username', '')
        self.password = convert_to_sha1(form.get('password', ''))
        self.sex = form.get('sex', '')
        self.note = form.get('note', '')

    def __repr__(self):
        class_name = self.__class__.__name__
        return u'<{}: {}>'.format(class_name, self.id)

    def save(self):
        # 这是数据库的概念，用法就是这样，先 add 再 commit
        db.session.add(self)
        db.session.commit()

    # 验证注册用户的合法性的，应该还要添加防止用户名重复的情况
    def valid(self):
        username_len = len(self.username) >= 3
        password_len = self.password != 'too-short!'
        all_users = User.query.all()
        users = [x.username for x in all_users]
        if self.username not in users:
            username_unique = True
        else:
            username_unique = False
        return username_len and password_len and username_unique

    def validate(self, user):
        if isinstance(user, User):
            username_equals = self.username == user.username
            password_equals = self.password == user.password
            return username_equals and password_equals
        else:
            return False

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self, form):
        a = form.get('username', '')
        b = form.get('password', '')
        if a == '' or b == '':
            return False
        else:
            self.username = a
            self.password = convert_to_sha1(b)
            return True


class Blog(db.Model):
    __tablename__ = 'blogs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    content = db.Column(db.String())
    created_time = db.Column(db.DateTime(timezone=True), default=sql.func.now())
    release_time = db.Column(db.String(), default=local_time(time.time()))
    com_count = db.Column(db.Integer, default=0)
    # 这是一个外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='blog')

    def __init__(self, form):
        self.title = form.get('title', '')
        self.content = form.get('content', '')

    def __repr__(self):
        class_name = self.__class__.__name__
        return u'<{}: {}>'.format(class_name, self.id)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self, form):
        self.title = form.get('title', '')
        self.content = form.get('content', '')
        self.created_time = sql.func.now()
        self.release_time = local_time(time.time())
        return True


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String())
    created_time = db.Column(db.DateTime(timezone=True), default=sql.func.now())
    release_time = db.Column(db.String(), default=local_time(time.time()))
    sender_name = db.Column(db.String())
    reply_id = db.Column(db.Integer, default=0)
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.id'))

    def __init__(self, form):
        self.content = form.get('content', '')

    def __repr__(self):
        class_name = self.__class__.__name__
        return u'<{}: {}>'.format(class_name, self.id)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Follow(db.Model):
    __tablename__ = 'follows'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    followed_id = db.Column(db.Integer)
    created_time = db.Column(db.DateTime(timezone=True), default=sql.func.now())
    release_time = db.Column(db.String(), default=local_time(time.time()))
    # 关注了哪些用户，配合user_id使用
    follows = db.relationship('User')
    # 有哪些粉丝，配合followed_id使用
    # fans = db.relationship('User')

    def __repr__(self):
        class_name = self.__class__.__name__
        return u'<{}: {}>'.format(class_name, self.id)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


def backup_db():
    backup_path = '{}.{}'.format(time.time(), db_path)
    shutil.copyfile(db_path, backup_path)


def rebuild_db():
    backup_db()
    db.drop_all()
    db.create_all()
    log('rebuild database')


# 第一次运行工程的时候没有数据库
# 所以我们运行 models.py 创建一个新的数据库文件
if __name__ == '__main__':
    rebuild_db()

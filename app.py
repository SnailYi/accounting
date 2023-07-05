# !usr/bin/env python
# -*- coding:utf-8 _*-
"""
@Author:eagleYing
@Blog(个人博客地址): unknown

@File:accounting.py
@Time:2023/7/4 16:54
"""
import os
import sys
import click

from flask import Flask, request, url_for, redirect, flash, render_template, jsonify
from markupsafe import escape  # 用户输入的数据会包含恶意代码，所以不能直接作为响应返回，需要使用 MarkupSafe（Flask 的依赖之一）提供的 escape() 函数对 name 变量进行转义处理
from flask_sqlalchemy import SQLAlchemy  # Python 数据库工具（ORM，即对象关系映射）

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
db = SQLAlchemy(app)


class Business(db.Model):  # 表名将会是 business（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True)  # 主键
    time = db.Column(db.DateTime)  # 时间
    buyer_id = db.Column(db.Integer, db.ForeignKey("user_info.id"))  # 买家id
    seller_id = db.Column(db.Integer, db.ForeignKey("user_info.id"))  # 卖家id
    product = db.Column(db.String(20))  # 产品
    price = db.Column(db.Float)  # 单价
    quantity = db.Column(db.Integer)  # 数量
    remark = db.Column(db.Text)  # 备注
    test = db.Column(db.Text)  # 测试


class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))  # 名字
    phone = db.Column(db.String(20))  # 电话
    address = db.Column(db.Text)  # 地址
    remark = db.Column(db.String(20))  # 备注


@app.cli.command()  # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息


@app.route('/')
def hello():
    return 'Welcome to My Watchlist!'


@app.route("/create_user", methods=["GET", "POST"])
def create_user():
    # 新增用户
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        address = request.form.get("address")
        remark = request.form.get("remark")
        if not name or not phone or not address:
            # flash("请填写必须的内容")
            app.logger.warning(f"create_user 创建用户失败，name={name}, phone={phone}, address={address}, remark={remark}")
            return render_template('index.html', isTrue="失败")
        user = UserInfo(name=name, phone=phone, address=address, remark=remark)
        db.session.add(user)
        db.session.commit()
        # flash("创建用户成功")
        app.logger.warning(f"create_user 创建成功的用户数据为{UserInfo.query.filter_by(name=name).first()}")
        return render_template('index.html', isTrue="成功")


@app.route("/search_all_user", methods=["GET", "POST"])
def search_all_user():
    # 搜索所有的用户
    if request.method == "GET":
        user_data = UserInfo.query.all()
        return render_template('index.html', users=user_data)


@app.route("/search_user", methods=["GET", "POST"])
def search_user():
    # 搜索用户
    if request.method == "GET":
        name = request.args.get("name")
        app.logger.warning(f"search_user params的name={name}")
        user_data = UserInfo.query.filter_by(name=name).first()
        app.logger.warning(
            f"""search_user 查询到的用户name={user_data.name}, phone={user_data.phone}, address={user_data.address}, 
            remark={user_data.remark}""")
        return render_template('update_user.html', user=user_data)


@app.route("/update_user_page", methods=["GET", "POST"])
def update_user_page():
    # 跳转到更新用户页面
    if request.method == "GET":
        name = request.args.get("name")
        user_data = UserInfo.query.filter_by(name=name).first()
        app.logger.warning(
            f"""update_user_page 查询到的用户name={user_data.name}, phone={user_data.phone}, address={user_data.address}, 
            remark={user_data.remark}""")
        return render_template('update_user.html', user=user_data)


@app.route("/update_user", methods=["GET", "POST"])
def update_user():
    # 更新用户信息
    if request.method == "POST":
        # 不能更改名字
        name = request.form.get("name")
        phone = request.form.get("phone")
        address = request.form.get("address")
        remark = request.form.get("remark")
        app.logger.warning(f"update_user 表单收到的数据为name={name}, phone={phone}, address={address}, remark={remark}")
        user_data = UserInfo.query.filter_by(name=name).first()
        user_data.phone = phone
        user_data.address = address
        user_data.remark = remark
        db.session.commit()
        app.logger.warning(f"update_user 更新成功")
        return render_template('index.html', update_user_bool="成功")
    flash("更新用户信息失败")
    app.logger.warning("update_user 更新用户信息失败")
    return render_template('index.html', update_user_bool="失败")

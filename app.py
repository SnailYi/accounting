# !usr/bin/env python
# -*- coding:utf-8 _*-
"""
@Author:eagleYing
@Blog(个人博客地址): unknown

@File:accounting.py
@Time:2023/7/4 16:54
"""
import json
import os
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime

import click

from flask import Flask, request, url_for, redirect, flash, render_template, jsonify
from markupsafe import escape  # 用户输入的数据会包含恶意代码，所以不能直接作为响应返回，需要使用 MarkupSafe（Flask 的依赖之一）提供的 escape() 函数对 name 变量进行转义处理
from flask_sqlalchemy import SQLAlchemy  # Python 数据库工具（ORM，即对象关系映射）
from sqlalchemy.orm import Query, DeclarativeMeta

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
    id: int = db.Column(db.Integer, primary_key=True)  # 主键
    time: str = db.Column(db.DateTime, default=datetime.now)  # 时间
    buyer_id: int = db.Column(db.Integer, db.ForeignKey("user_info.id"))  # 买家id
    seller_id: int = db.Column(db.Integer, db.ForeignKey("user_info.id"))  # 卖家id
    product: str = db.Column(db.String(20))  # 产品
    price: float = db.Column(db.Float)  # 单价
    quantity: int = db.Column(db.Integer)  # 数量
    remark: str = db.Column(db.Text)  # 备注
    test: str = db.Column(db.Text)  # 测试


class UserInfo(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)  # 主键
    name: str = db.Column(db.String(20))  # 名字
    phone: str = db.Column(db.String(20))  # 电话
    address: str = db.Column(db.Text)  # 地址
    remark: str = db.Column(db.String(20))  # 备注


class AlchemyJsonEncoder(json.JSONEncoder):
    def default(self, obj):
            if isinstance(obj.__class__, DeclarativeMeta):
                # an SQLAlchemy class
                fields = {}
                for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                    data = obj.__getattribute__(field)
                    try:
                        json.dumps(data)  # this will fail on non-encodable values, like other classes
                        fields[field] = data
                    except TypeError:
                        fields[field] = None
                # a json-encodable dict
                return fields

            return json.JSONEncoder.default(self, obj)


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
        create_user_data = UserInfo.query.filter_by(name=name).first()
        app.logger.warning(f"create_user 创建成功的用户数据为{create_user_data}")
        return {"status": 1, "UserInfo": json.loads(json.dumps(create_user_data, cls=AlchemyJsonEncoder))}
        # return render_template('index.html', isTrue="成功")


@app.route("/delete_user", methods=["GET"])
def delete_user():
    if request.method == "GET":
        id = int(request.args.get("id"))
        name = request.args.get("name")
        try:
            user_data = UserInfo.query.filter_by(id=id).filter_by(name=name).first()
            app.logger.warning(f"delete_user 类型为{type(user_data)}，数据为{user_data}")
            db.session.delete(user_data)
            db.session.commit()
            return {"status": 1, "data": "删除成功"}
        except:
            return {"status": 500, "data": "删除失败"}


@app.route("/search_all_user", methods=["GET", "POST"])
def search_all_user():
    # 搜索所有的用户
    if request.method == "GET":
        user_data = UserInfo.query.all()
        app.logger.warning(f"search_all_user 类型为{type(user_data)}，数据为{user_data}")
        return {"status": 1, "data": json.loads(json.dumps(user_data, cls=AlchemyJsonEncoder))}


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


@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if request.method == "POST":
        buyer_id = request.form.get("buyer_id")
        seller_id = request.form.get("seller_id")
        product = request.form.get("product")
        unit_price = request.form.get("unit_price")
        quantity = request.form.get("quantity")
        remark = request.form.get("remark")
        if not buyer_id or seller_id or product or unit_price or quantity or remark:
            app.logger.warning("create_account 必要的参数没有填写")
            return render_template('index.html')
        account = Business(buyer_id=buyer_id, seller_id=seller_id, product=product, price=unit_price, quantity=quantity,
                           remark=remark)
        db.session.add(account)
        db.session.commit()
        app.logger.warning("create_account 创建生意记录成功")
        return render_template("index.html")

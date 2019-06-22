from flask import Blueprint

# 创建蓝图对象
api = Blueprint('api_1_0', __name__)

# 导入蓝图的视图函数，使用推迟导入的方法防止循环嵌套
from . import demo, verify_code, passport, profile, houses, orders, pays
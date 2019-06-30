from flask import Flask
from config import config_map
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import CSRFProtect
import redis
import logging
from logging.handlers import RotatingFileHandler
from .utils.commons import RegexConverter

# 创建数据库连接
db = SQLAlchemy()

# 创建变量避免导入错误，在函数中进行初始化
redis_store = None

# 配置日志信息
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
stream_log_handler = logging.StreamHandler()
# 创建日志记录的格式       日志等级    输入日志信息的文件名 行数    日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)
# 为全局的日志工具对象（flask app使用的）添加控制台显示记录器
logging.getLogger().addHandler(stream_log_handler)
# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)  # 调试debug级，会受flask的debug=True影响，强制忽略设置的等级

def creat_app(config_name):
	'''
	工厂模式，处理不同模式的app创建
	:param config_name: str 配置模式的名称('develop', 'product')
	:return: object flask的app对象
	'''
	app = Flask(__name__)
	config_class = config_map.get(config_name)
	app.config.from_object(config_class)

	# 绑定SQLAlchemy的app对象
	db.init_app(app) 

	# 初始化redis工具，创建Redis连接对象用于缓存
	global redis_store
	redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)

	# 利用flask_session扩展将session数据保存到redis中
	Session(app)

	# 为flask补充CSRF防护
	CSRFProtect(app)

	# 为flask添加自定义的转换器
	app.url_map.converters['re'] = RegexConverter

	# 注册蓝图，推迟导入，防止循环嵌套
	from . import api_1_0
	app.register_blueprint(api_1_0.api, url_prefix='/api/v1.0')

	# 注册提供静态文件的蓝图
	from .web_html import html
	app.register_blueprint(html)

	return app

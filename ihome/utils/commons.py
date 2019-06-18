from werkzeug.routing import BaseConverter
from ihome.utils.response_code import RET
from flask import session, g, jsonify
import functools



class RegexConverter(BaseConverter):
    def __init__(self, url_map, regex):
        super(RegexConverter, self).__init__(url_map)
        self.regex = regex

# 验证登录状态装饰器
def login_required(view_function):
	@functools.wraps(view_function)
	def wrapper(*args, **kwargs):
		# 判断用户登录状态
		user_id = session.get('user_id')
		if user_id:
			# 此处使用g对象，节省了在视图函数中对于session的又一次查询
			g.user_id = user_id
			return view_function(*args, **kwargs)
		else:
			return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
	return wrapper
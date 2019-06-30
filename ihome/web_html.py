from flask import Blueprint, current_app, make_response
from flask_wtf import csrf

html = Blueprint('html', __name__)

@html.route('/<re(r".*"):html_file_name>')
def get_html(html_file_name):
	'''提供html文件'''
	if not html_file_name:
		# 当输入的url为空时，将其设置为主页
		html_file_name = 'index.html'
	if html_file_name != 'favicon.ico':
		# 设置html静态文件的访问路径
		html_file_name = 'html/' + html_file_name
	# 创建csrf_token值，并设置cookie，用于前端从cookie中获取csrf_token值并设置到请求体中，但flaskwtf的csrf机制并不从cookie中取值
	csrf_token = csrf.generate_csrf()
	resp = make_response(current_app.send_static_file(html_file_name))
	resp.set_cookie('csrf_token', csrf_token)

	return resp

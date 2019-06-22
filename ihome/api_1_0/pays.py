from . import api
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.models import User, House, Area, Facility, HouseImage, Order
from ihome import db, constants, redis_store
from flask import g, current_app, request, jsonify, session
from datetime import datetime
from alipay import AliPay
import time
import json
import os


@api.route('/orders/<int:order_id>/payment', methods=['POST'])
@login_required
def order_pay(order_id):
	'''发起支付宝支付'''
	# 获取参数
	user_id = g.user_id

	# 校验订单状态
	try:
		order = Order.query.filter(Order.id == order_id, Order.user_id == user_id, Order.status == 'WAIT_PAYMENT').first()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	if not order:
		return jsonify(errno=RET.NODATA, errmsg='订单信息有误')

	# 处理支付接口
	alipay = AliPay(appid='2016092900620771',  # 应用ID
        			app_notify_url=None,  # 默认回调url
        			app_private_key_path=os.path.join(os.path.dirname(__file__), 'keys/app_private_key.pem'),  #应用私钥
        			alipay_public_key_path=os.path.join(os.path.dirname(__file__), 'keys/alipay_public_key.pem'), #支付宝公钥
        			sign_type="RSA2",  # RSA 或者 RSA2 -- 这里注意一点：2018年1月5日后创建的应用只支持RSA2的格式；
        			debug=True)  # 默认False -- 设置为True则是测试模式
	
	# 手机网站支付
	total_amount = str(order.amount/100.0)
	order_string = alipay.api_alipay_trade_wap_pay(
    				out_trade_no=order_id, # 订单编号
    				total_amount=total_amount, # 总金额，以元为单位的字符串
    				subject='爱家租房_{}'.format(order_id), # 订单标题
    				return_url="http://127.0.0.1:5000/orders.html", # 返回的链接地址
    				notify_url=None) # 可选, 不填则使用默认notify url
	# 合成跳转地址
	pay_url = constants.API_PAY_ADDRESS + order_string

	return jsonify(errno=RET.OK, errmsg='OK', data={'pay_url': pay_url})

# 此处应有支付宝的回调处理，即根据支付结果修改订单支付状态
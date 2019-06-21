from . import api
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.models import User, House, Area, Facility, HouseImage, Order
from ihome import db, constants, redis_store
from flask import g, current_app, request, jsonify, session
from datetime import datetime
import time
import json

@api.route('/orders', methods=['POST'])
@login_required
def save_order():
	'''保存订单'''
	# 获取与校验参数完整性
	user_id = g.user_id
	order_data = request.get_json()
	if not order_data:
		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

	house_id = order_data.get('house_id')
	start_date = order_data.get('start_date')
	end_date = order_data.get('end_date')
	if not all([house_id, start_date, end_date]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

	# 校验日期
	try:
		start_date = datetime.strptime(start_date, '%Y-%m-%d')
		end_date = datetime.strptime(end_date, '%Y-%m-%d')
		assert start_date <= end_date
		# 此处计算预定天数，应明确标识对天数的设定(如中午12点之前不计入当天等)
		days = (end_date - start_date).days + 1
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.PARAMERR, errmsg="时间格式错误")

	# 校验房屋
	try:
		house = House.query.get(house_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="获取数据失败")
	if not house:
		return jsonify(errno=RET.NODATA, errmsg='房屋信息有误')

	# 判断房东信息
	if house.user_id == user_id:
		return jsonify(errno=RET.ROLEERR, errmsg='房东不可以预定自己的房间')

	# 判断订单冲突情况
	try:
		count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date, Order.end_date >= start_date).count()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="获取数据失败")
	print(count)
	if count > 0:
		return jsonify(errno=RET.DATAERR, errmsg='房屋已被预定，存在冲突')

	# 生成订单
	amount = days * house.price
	order = Order(
		user_id=user_id,
		house_id=house_id,
		begin_date=start_date,
		end_date=end_date,
		days=days,
		house_price=house.price,
		amount=amount,
	)
	try:
		db.session.add(order)
		db.session.commit()
	except Exception as e:
		current_app.logger.error(e)
		db.session.rollback()
		return jsonify(errno=RET.DBERR, errmsg="保存订单失败")

	return jsonify(errno=RET.OK, errmsg='OK', data={'order_id':order.id})

# /api/v1.0/user/orders?role=
@api.route('/user/orders', methods=['GET'])
@login_required
def get_user_orders():
	'''查询用户的订单数据'''
	user_id = g.user_id
	# 将用户下的订单和用户名下的房屋的订单接口放置在一起，但需要同时传入参数用于区分
	role = request.args.get('role', '')

	# 查询数据库
	try:
		if role == 'landlord':
			houses = House.query.filter_by(user_id=user_id).all()
			# 此处为了对查询出来的order可以进行排序，多进行一次查询，而不用house.orders
			houses_id = [house.id for house in houses]
			orders = Order.query.filter(Order.house_id.in_(houses_id)).order_by(Order.create_time.desc()).all()
		else:
			orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

	# 返回订单数据
	orders_dict_li = list()
	if orders:
		for order in orders:
			orders_dict_li.append(order.to_dict())

	return jsonify(errno=RET.OK, errmsg='OK', data={'orders':orders_dict_li})


@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_required
def accept_reject_order(order_id):
    """接单、拒单"""
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # action参数表明客户端请求的是接单还是拒单的行为
    action = req_data.get("action")
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 根据订单号查询订单，并且要求订单处于等待接单状态
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="无法获取订单数据")

    # 确保房东只能修改属于自己房子的订单
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")

    if action == "accept":
        # 接单，将订单状态设置为等待评论(待支付)
        order.status = "WAIT_COMMENT"
    elif action == "reject":
        # 拒单，要求房东传递拒单原因
        reason = req_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        order.status = "REJECTED"
        order.comment = reason

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

    return jsonify(errno=RET.OK, errmsg="OK")


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    """保存订单评论信息"""
    user_id = g.user_id
    # 获取参数
    req_data = request.get_json()
    comment = req_data.get("comment")  # 评价信息

    # 检查参数
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 需要确保只能评论自己下的订单，而且订单处于待评价状态才可以
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id, Order.status == "WAIT_COMMENT").first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="无法获取订单数据")

    if not order:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")

    try:
        # 将订单的状态设置为已完成
        order.status = "COMPLETE"
        # 保存订单的评价信息
        order.comment = comment
        # 将房屋的完成订单数增加1
        house.order_count += 1
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

    # 因为房屋详情中有订单的评价信息，为了让最新的评价信息展示在房屋详情中，所以删除redis中关于本订单房屋的详情缓存
    try:
        redis_store.delete("house_detail_%s" % order.house.id)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg="OK")
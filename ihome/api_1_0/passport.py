from . import api
from flask import request, current_app, jsonify, session
from ihome.utils.response_code import RET
from ihome import redis_store, constants, db
from ihome.models import User
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash
import re


@api.route('/users', methods=['POST'])
def register():
    # 获取请求的json数据，转换为字典
    req_dict = request.get_json()
    mobile = req_dict.get('mobile')
    sms_code = req_dict.get('sms_code')
    password = req_dict.get('passwd')
    password2 = req_dict.get('passwd2')

    # 校验参数完整性
    if not all([mobile, sms_code, password, password2]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 校验手机号格式
    if not re.match(r'1[34578]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    # 校验两次密码
    if password2 != password:
        return jsonify(errno=RET.PARAMERR, errmsg="两次密码不一致")

    # 此处可以继续添加密码长度格式等校验条件
    # 获取短信验证码
    try:
        real_sms_code = redis_store.get('sms_code_{}'.format(mobile)).decode()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="redis数据库异常")

    # 判断短信验证码是否失效
    if not redis_store:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码失效")

    # 删除redis中的短信验证码，防止重复校验
    try:
        redis_store.delete("sms_code_{}".format(mobile))
    except Exception as e:
        current_app.logger.error(e)

    # 判断用户填写短信验证码是否一致
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码错误")

    # 判断手机号是否注册过，将此处判断与添加写在一起，减少一次对于数据库的操作
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg="数据库异常，注册失败")
    # else:
    #     if user:
    #         # 表示手机号已存在
    #         return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")

    # 判断并添加用户信息
    try:
        user = User(name=mobile, mobile=mobile)
        user.password = password
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        # 表示手机号重复，回滚数据库操作
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # 保存登录状态
    session['name'] = mobile
    session['mobile'] = mobile
    session['user_id'] = user.id

    return jsonify(errno=RET.OK, errmsg="注册成功")


@api.route('/sessions', methods=['POST'])
def login():
    '''用户登录'''
    # 参数获取与校验
    req_dict = request.get_json()
    mobile = req_dict.get('mobile')
    password = req_dict.get('password')
    # 校验参数完整性
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    # 校验手机号格式
    if not re.match(r'1[34578]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    # 判断错误次数是否超过限制，如果超过则10分钟内禁止此IP登录
    user_ip = request.remote_addr
    try:
        access_nums = redis_store.get('access_nums_{}'.format(user_ip))
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nums:
            if int(access_nums.decode()) >= constants.LOGIN_ERROR_TIMES:
                return jsonify(errno=RET.REQERR, errmsg="错误次数过多，请稍候重试")

    # 验证手机号与密码
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    # 将用户名与密码验证放置在一处，若失败返回提示信息并记录次数
    if (not user) or (not user.check_password(password)):
        try:
            redis_store.incr('access_nums_{}'.format(user_ip))
            redis_store.expire('access_nums_{}'.format(user_ip), constants.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=RET.DBERR, errmsg="用户名或密码错误")

    # 若成功保存登录状态
    session['name'] = user.name
    session['mobile'] = user.mobile
    session['user_id'] = user.id

    return jsonify(errno=RET.OK, errmsg="登录成功")


@api.route('/session', methods=['GET'])
def check_login():
    '''检查登录状态，由于针对特定资源访问，因此不加复数'''
    # 因为首页可以让未登录用户访问，因此必须在视图内完成登录验证
    name = session.get('name')
    if name:
        return jsonify(errno=RET.OK, errmsg="true", data={'name': name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg='false')

@api.route('/session', methods=['DELETE'])
def log_out():
    '''登出'''
    # 防止出现浏览器缓存，session中的csrf值被删除而页面不发送请求不重新设置新的csrf值产生验证错误
    csrf_token = session.get('csrf_token')
    session.clear()
    session['csrf_token'] = csrf_token
    return jsonify(errno=RET.OK, errmsg="true")

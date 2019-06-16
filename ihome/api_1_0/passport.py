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
    # 校验短信验证码
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
    print(real_sms_code, type(real_sms_code), sms_code, type(sms_code))
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
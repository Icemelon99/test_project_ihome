from . import api
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.models import User
from ihome import db, constants
from flask import g, current_app, request, jsonify
import time

@api.route('/users/avatar', methods=['POST'])
@login_required
def set_user_avatar():
    '''用户上传图片设置头像，以多媒体表单形式传送'''
    user_id = g.user_id
    image_file = request.files.get('avatar')

    if not image_file:
        return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")

    # 此处将图片保存到第三方服务器，由于无法连接，模拟
    image_name = 'avatar_{}_{}'.format(user_id, int(time.time()))
    image_file.save('./ihome/static/images/{}'.format(image_name))

    # 保存文件名到数据库中
    try:
        User.query.filter_by(id=user_id).update({'avatar_url':image_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片失败")

    # 保存成功，返回数据
    avatar_url = constants.UPLOAD_IMAGE_URL+image_name
    print(avatar_url)
    return jsonify(errno=RET.OK, errmsg="保存成功", data={'avatar_url': avatar_url})


@api.route('/users/name', methods=['POST'])
@login_required
def set_user_name():
    '''设置用户名'''
    req_dict = request.get_json()
    name = req_dict.get('name')
    user_id = g.user_id

    if not name:
        return jsonify(errno=RET.PARAMERR, errmsg="请输入用户名")

    # 此处应对用户名规范进行校验/整理，如禁止输入空格

    # 将用户输入的内容保存到数据库中，因为name字段设定为unique，因此默认用户名不能重复，此处应添加专门捕获用户名重复的异常
    try:
        user = User.query.filter_by(id=user_id).update({'name': name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存用户名失败")

    # 保存成功，修改session中的数据，返回
    session['name'] = name
    return jsonify(errno=RET.OK, errmsg="保存成功", data={'name': name})

# 此处应存在一个profile页面和auth页面的GET请求，在前段页面打开时即$(document).ready()发送请求用于访问相应的数据，在有数据的情况下将其显示，且身份验证若有数据时将输入框设置为不可修改/删除输入框

@api.route('/users/auth', methods=['POST'])
@login_required
def set_user_auth():
    '''设置用户实名认证，并需要设置当已认证过后无法修改'''
    req_dict = request.get_json()
    real_name = req_dict.get('real_name')
    id_card = req_dict.get('id_card')
    user_id = g.user_id

    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="数据不完整")

    # 此处应校验身份证格式与用户真名信息，第三方服务

    # 校验完成后，设置当真实姓名和身份证号都为空时才可以更新，保存到数据库
    try:
        user = User.query.filter_by(id=user_id, real_name=None, id_card=None).update({'real_name': real_name, 'id_card': id_card})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="实名认证失败")

    if not user:
        return jsonify(errno=RET.NODATA, errmsg='已进行实名认证')

    # 保存成功，返回
    return jsonify(errno=RET.OK, errmsg="保存成功", data={'real_name': real_name, 'id_card': id_card})


@api.route('/users/profile', methods=['GET'])
@login_required
def get_user_profile():
    '''获取用户信息'''
    # 从g对象或session中获取用户id
    user_id = g.user_id

    # 从数据库中获取信息
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    # 添加对user的校验
    if not user:
        return jsonify(errno=RET.NODATA, errmsg='无效操作')
    # 组织参数，此处可以在模型类中设置将对象转换为字典数据，返回应答
    name = user.name
    avatar_url = user.to_url()
    mobile = user.mobile
    resp_data = {
        'name': name,
        'avatar_url': avatar_url,
        'mobile': mobile
    }
    return jsonify(errno=RET.OK, errmsg="获取成功", data=resp_data)


@api.route("/users/auth", methods=["GET"])
@login_required
def get_user_auth():
    """获取用户的实名认证信息"""
    user_id = g.user_id

    # 在数据库中查询信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户实名信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.auth_to_dict())
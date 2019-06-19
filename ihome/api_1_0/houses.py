from . import api
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.models import User, House, Area, Facility, HouseImage
from ihome import db, constants, redis_store
from flask import g, current_app, request, jsonify, session
import time
import json


@api.route('/areas')
def get_area_info():
    '''获取城区信息'''

    # 尝试从redis中获取缓存
    try:
        resp_json = redis_store.get('area_info').decode()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            print('hit redis area info')
            return resp_json, 200, {"Content-Type": "application/json"}

    # 查询数据库，读取城区信息
    try:
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # 组织数据
    area_dict_li = list()
    for area in area_li:
        area_dict_li.append(area.to_dict())

    # 将数据保存到redis中，作为缓存使用，将响应结果直接转换为json字符串
    resp_dict = dict(errno=RET.OK, errmsg="获取成功", data=area_dict_li)
    resp_json = json.dumps(resp_dict)
    try:
        redis_store.setex('area_info', constants.AREA_INFO_REDIS_EXPIRE, resp_json)
    except Exception as e:
        current_app.logger.error(e)
    
    return resp_json, 200, {"Content-Type": "application/json"}


@api.route('/houses/info', methods=['POST'])
@login_required
def save_house_info():
    """保存房屋的基本信息
    前端发送过来的json数据
    {
        "title":"",
        "price":"",
        "area_id":"",
        "address":"",
        "room_count":"",
        "acreage":"",
        "unit":"",
        "capacity":"",
        "beds":"",
        "deposit":"",
        "min_days":"",
        "max_days":"",
        "facility":["7","8"]
    }
    """
    # 获取数据
    user_id = g.user_id
    house_data = request.get_json()
    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数
    max_days = house_data.get("max_days")  # 最大入住天数

    # 校验参数完整性
    if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 校验金额
    try:
        price = int(100*float(price))
        deposit = int(100*float(deposit))
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 校验城区ID
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if not area:
        return jsonify(errno=RET.NODATA, errmsg='城区信息有误')

    # 其余参数校验

    # 保存房屋基本信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )
    db.session.add(house)

    # 处理房屋设施信息
    facility_ids = house_data.get('facility')

    if facility_ids:
        # 过滤设施编号
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库异常")

        # 保存设施数据到房屋设施中
        if facilities:
            house.facilities = facilities

    # 将基本信息和设施信息处理完毕后，在最后再进行操作数据库
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    return jsonify(errno=RET.OK, errmsg="保存成功", data={'house_id':house.id})

@api.route('/houses/image', methods=['POST'])
@login_required
def save_house_image():
    '''保存房屋的图片'''
    image_file = request.files.get('house_image')
    house_id = request.form.get('house_id')

    # 校验参数完整性
    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断房屋id的正确性
    try:
        house = House.query.filter_by(id=house_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋信息有误')

    # 此处将图片保存到第三方服务器，由于无法连接，模拟
    image_name = 'house_image_{}_{}'.format(house_id, int(time.time()))
    image_file.save('./ihome/static/images/{}'.format(image_name))

    # 保存文件名到数据库中
    house_image = HouseImage(house_id=house_id, url=image_name)
    db.session.add(house_image)

    # 处理房屋的主图片
    if not house.index_image_url:
        house.index_image_url = image_name
        db.session.add(house)

    # 将图片提交到数据库
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片失败")

    image_url = house_image.to_url()

    return jsonify(errno=RET.OK, errmsg="保存成功", data={'image_url':image_url})

@api.route('/users/houses', methods=['GET'])
@login_required
def get_user_houses():
    '''获取房东发布的房源信息，需要实名认证后才可发布'''
    user_id = g.user_id

    # 查询房源信息并判断用户是否存在
    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

    houses_li = list()

    if houses:
        for house in houses:
            houses_li.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg="保存成功", data={'houses':houses_li})

@api.route('/houses/index', methods=['GET'])
def get_house_index():
    '''获取主页房源信息'''
    # 获取缓存
    try:
        resp_json = redis_store.get('index_info').decode()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            print('hit redis home page info')
            return resp_json, 200, {"Content-Type": "application/json"}

    # 查询根据热度排序的房屋信息
    try:
        houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_INDEX_IMAGES).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

    if not houses:
        return jsonify(errno=RET.NODATA, errmsg='查询无数据')

    houses_li = list()

    if houses:
        for house in houses:
            if not house.index_image_url:
                continue
            houses_li.append(house.to_basic_dict())

    # 将数据保存到redis中，作为缓存使用，将响应结果直接转换为json字符串
    resp_dict = dict(errno=RET.OK, errmsg="获取成功", data=houses_li)
    resp_json = json.dumps(resp_dict)
    try:
        redis_store.setex('index_info', constants.HOME_PAGE_REDIS_EXPIRE, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}


@api.route('houses/<int:house_id>', methods=['GET'])
def get_house_detail(house_id):
    '''获取房屋详情信息'''
    # 前端在房屋详情页面展示时，若浏览页面的用户不是该房屋的房东，则显示预定按钮
    # 需要从前端将url中的house_id保存在其发送请求的url中
    # 尝试获取用户登录信息，若存在则返回user_id，若不存在则返回-1
    user_id = session.get('user_id', '-1')

    # 获取缓存
    try:
        house_json = redis_store.get('house_detail_{}'.format(house_id)).decode()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if house_json: 
            resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, house_json), \
           200, {"Content-Type": "application/json"}
            return resp

    # 校验参数
    if not all([user_id, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 获取房屋详细信息
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋信息有误')

    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据出错")


    # 将数据保存到redis中，作为缓存使用
    house_json = json.dumps(house_data)
    try:
        redis_store.setex('house_detail_{}'.format(house_id), constants.HOUSE_DETAIL_REDIS_EXPIRE, house_json)
    except Exception as e:
        current_app.logger.error(e)

    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, house_json), \
           200, {"Content-Type": "application/json"}
    return resp



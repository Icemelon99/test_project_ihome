from . import api
from ihome.utils.response_code import RET
from ihome import redis_store, constants
from flask import current_app, jsonify, make_response, send_file
from captcha.image import ImageCaptcha
import random

# 127.0.0.1:5000/api/v1.0/image_codes/<image_code_id> GET
@api.route('/image_codes/<image_code_id>')
def get_image_codes(image_code_id):
    '''获取图片验证码
    image_code_id 图片验证码编号
    return 正常时返回图片验证码，异常时返回json错误信息'''
    # 获取参数，检验参数已完成，若无则无法进入视图函数
    # 生成验证码图片
    image = ImageCaptcha(fonts=['./ihome/utils/captcha/fonts/actionj.ttf', './ihome/utils/captcha/fonts/Georgia.ttf'])
    str1 = 'abcd123efghijk45lmn6opqrst789uvwxyz0'
    text = ''
    for i in range(0, 4):
        text += str1[random.randrange(0, len(str1))]
    image_data = image.generate(text)
    # 将验证码真实值与编号保存在redis中，并设置有效期
    try:
        redis_store.setex('image_code_{}'.format(image_code_id), constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(err_num=RET.DBERR, err_msg='保存图片验证码信息失败')
    # 返回应答
    # resp = make_response(image_data)
    # resp.heads['Content-Type'] = 'image/jpg'
    resp = send_file(image_data,
                     attachment_filename='image_code.jpg',
                     mimetype='image/jpg')
    return resp
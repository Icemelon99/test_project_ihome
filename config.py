import redis
# 将开发模式和调试模式的配置信息中相同的部分复用
class Config:
	'''配置信息'''
	SECRET_KEY = 'WER43TTHYUIP0-[-;IJTRGWFE3EWDAFG*(&REF343'
	# 数据库配置信息
	SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/ihome'
	SQLALCHEMY_TRACK_MODIFICATIONS = True
	# redis配置信息
	REDIS_HOST = '127.0.0.1'
	REDIS_PORT = 6379
	# session配置存储到redis中
	SESSION_TYPE = 'redis'
	SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
	SESSION_USE_SIGNER = True # 对session_id进行隐藏处理
	PERMANENT_SESSION_LIFETIME = 60*60*24 # 设置session的有效时间

class DevelopmentConfig(Config):
	'''开发模式配置信息'''
	DEBUG = True

class ProductionConfig(Config):
	'''生产环境配置信息'''
	pass

config_map = {
	'develop': DevelopmentConfig,
	'product': ProductionConfig,
}
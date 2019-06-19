from celery import Celery
from ihome.tasks import config

# 定义celery对象
app = Celery('ihome')
# 引入配置信息
app.config_from_object(config)
# 自动搜寻异步任务，对应任务名固定为tasks.py
app.autodiscover_tasks(['ihome.tasks.sms'])

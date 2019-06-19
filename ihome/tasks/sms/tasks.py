from ihome.tasks.main import app
import time

@app.task
def send_msg(sms_code, mobile):
	'''发送短信的异步任务'''
	time.sleep(5)
	print('send message {} to {}'.format(sms_code, mobile))
	return 0
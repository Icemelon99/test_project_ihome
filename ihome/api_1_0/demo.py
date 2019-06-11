from . import api
from ihome import db, models


@api.route('/demo')
def demo():
	return 'demo page'
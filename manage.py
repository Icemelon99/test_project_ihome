from flask import Flask
from ihome import creat_app, db
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

# 创建flask的应用对象，设置脚本
app = creat_app('develop')
manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)



if __name__ == '__main__':
	manager.run()
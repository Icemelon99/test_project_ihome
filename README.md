#### 基于flask前后端分离的租房网站  
  
网站名：ihome  
框架：flask  
用途：学习交流  
语言：python3  
开发环境：ubuntu 18.04  
依赖包：见ihome_freeze.txt  
完成功能：用户系统，房屋系统，订单系统，第三方支付  
使用工具：nginx, celery, redis, MySQL, Gunicorn, 第三方图片存储  
开发博客：参[学习笔记](https://blog.csdn.net/weixin_44806420/article/category/9063125)  
部署：使用nginx处理静态文件与页面，使用nginx负载均衡服务器分发动态请求给gunicorn+flaskapp，部署架构如下：
![](https://img-blog.csdnimg.cn/2019063011325416.png)

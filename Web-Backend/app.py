# /unified_service/app.py

import os
import logging
import config
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from routes import api as api_blueprint
from services import nebula_service, search_service,mongodb_service
from flask.json.provider import DefaultJSONProvider


# 自定义 JSONProvider，确保输出中文
class CustomJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs.setdefault("ensure_ascii", False)  # 关闭 ASCII 转义
        return super().dumps(obj, **kwargs)

def create_app():
    """工厂函数，用于创建和配置Flask应用"""
    print("开始创建Flask应用...")
    app = Flask(__name__)
    print("Flask应用实例创建成功")
    
    # 1. 加载配置
    print("加载配置...")
    app.config.from_object(config.Config)
    app.config.from_object(Config)
    print(f"配置加载完成: {app.config['LOG_LEVEL']}日志级别, MongoDB: {app.config['MONGO_HOST']}:{app.config['MONGO_PORT']}/{app.config['MONGO_DBNAME']}/{app.config['MONGO_COLLECTION']}")
    
    # 全局替换 JSONProvider
    print("配置JSONProvider...")
    app.json = CustomJSONProvider(app)
    print("JSONProvider配置完成")
    
    # 2. 配置日志
    print("配置日志...")
    logging.basicConfig(
        level=app.config['LOG_LEVEL'],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    print("日志配置完成")
    
    # 3. 设置环境变量
    print("设置环境变量...")
    os.environ['HF_ENDPOINT'] = app.config['HF_ENDPOINT']
    print(f"环境变量设置完成: HF_ENDPOINT={os.environ['HF_ENDPOINT']}")

    # 4. 初始化CORS
    print("初始化CORS...")
    CORS(app, resources={r"/api/*": {"origins": "*"}}) # 仅对/api路径下的路由启用CORS
    print("CORS初始化完成")

    # 5. 在应用上下文中初始化服务
    print("在应用上下文中初始化服务...")
    with app.app_context():
<<<<<<< HEAD
        nebula_service.init_nebula_pool(app.config)
        search_service.init_search_clients(app.config)
        # mongodb_service.init_mongodb_pool(app.config)
=======
        print("开始初始化MongoDB服务...")
        # 注释掉其他数据库服务，只保留MongoDB
        # nebula_service.init_nebula_pool(app.config)
        # search_service.init_search_clients(app.config)  # 暂时注释掉，因为Elasticsearch服务器不可用
        mongo_result = mongodb_service.init_mongodb_pool(app.config)
        print(f"MongoDB服务初始化结果: {mongo_result}")
>>>>>>> 8f76e98f0749dc1bee3f9c818f81fb2b6abd29bc

    # 6. 注册Blueprint
    print("注册Blueprint...")
    # 为所有路由添加 /api 前缀
    app.register_blueprint(api_blueprint, url_prefix='/api')
    print("Blueprint注册完成")

    # ✅ 关键：提供 uploads 目录的静态文件访问
    print("配置uploads目录静态文件访问...")
    @app.route('/uploads/<filename>')
    def uploaded_files(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    print("uploads目录静态文件访问配置完成")

    print("应用创建完成，准备返回应用实例")
    
    return app

print("开始创建应用实例...")
app = create_app()
print("应用实例创建完成")

if __name__ == '__main__':
    print("进入主函数，准备启动开发服务器...")
    # 使用 gunicorn 或 uwsgi 部署时，不会执行这部分
    # 仅用于开发环境
    # 修改host为127.0.0.1而不是0.0.0.0，避免Windows套接字问题
    print("开发服务器配置: host=127.0.0.1, port=5000, debug=True")
    try:
        print("正在启动开发服务器...")
        app.run(host='127.0.0.1', port=5000, debug=True)
        print("开发服务器启动成功")
    except Exception as e:
        print(f"开发服务器启动失败: {e}")
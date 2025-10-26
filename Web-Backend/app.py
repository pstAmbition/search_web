# /unified_service/app.py
import os
import logging
import config
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from routes import api as api_blueprint
from services import nebula_service, search_service,mongodb_service,neo4j_service
#from services import neo4j_service
from flask.json.provider import DefaultJSONProvider


# 自定义 JSONProvider，确保输出中文
class CustomJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs.setdefault("ensure_ascii", False)  # 关闭 ASCII 转义
        return super().dumps(obj, **kwargs)

def create_app():
    """工厂函数，用于创建和配置Flask应用"""
    app = Flask(__name__)
    
    # 1. 加载配置
    app.config.from_object(config.Config)
    app.config.from_object(Config)
    
    # 确保静态文件目录配置被正确加载
    # 如果Config类中的属性没有自动加载到app.config中，这里进行手动添加
    if 'fake_video_dir' not in app.config:
        app.config['fake_video_dir'] = Config.fake_video_dir
    if 'fake_img_dir' not in app.config:
        app.config['fake_img_dir'] = Config.fake_img_dir
    # 全局替换 JSONProvider
    app.json = CustomJSONProvider(app)
    
    # 2. 配置日志
    logging.basicConfig(
        level=app.config['LOG_LEVEL'],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 3. 设置环境变量
    os.environ['HF_ENDPOINT'] = app.config['HF_ENDPOINT']

    # 4. 初始化CORS
    CORS(app, resources={r"/fake/*": {"origins": "*"},r"/api/*": {"origins": "*"}}) # 仅对/api路径下的路由启用CORS

    # 5. 在应用上下文中初始化服务
    with app.app_context():
        # 根据需要启动相应服务
        nebula_service.init_nebula_pool(app.config)
        search_service.init_search_clients(app.config)
        mongodb_service.init_mongodb_pool(app.config)
        neo4j_service.init_neo4j_pool(app.config)

    # 6. 注册Blueprint
    # 为所有路由添加 /api 前缀
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # ✅ 关键：提供 uploads 目录的静态文件访问
    @app.route('/uploads/<filename>')
    def uploaded_files(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # ✅ 添加：提供 fake/video 目录的静态文件访问（使用配置文件中的路径）
    @app.route('/fake/video/<filename>')
    def fake_video_files(filename):
        # 直接使用配置文件中定义的路径，便于部署时修改
        return send_from_directory(app.config['fake_video_dir'], filename)
    
    # ✅ 添加：提供 fake/img 目录的静态文件访问（使用配置文件中的路径）
    @app.route('/fake/img/<filename>')
    def fake_img_files(filename):
        # 直接使用配置文件中定义的路径，便于部署时修改
        return send_from_directory(app.config['fake_img_dir'], filename)

    app.logger.info("应用启动成功，运行在 http://127.0.0.1:5000")
    
    return app

app = create_app()

if __name__ == '__main__':
    # 使用 gunicorn 或 uwsgi 部署时，不会执行这部分
    # 仅用于开发环境
    app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(host='127.0.0.1', port=5000, debug=True)

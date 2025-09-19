# /unified_service/app.py

import os
import logging
from flask import Flask
from flask_cors import CORS
from config import Config
from routes import api as api_blueprint
from services import nebula_service, search_service
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
    app.config.from_object(Config)
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
    CORS(app, resources={r"/api/*": {"origins": "*"}}) # 仅对/api路径下的路由启用CORS

    # 5. 在应用上下文中初始化服务
    with app.app_context():
        nebula_service.init_nebula_pool(app.config)
        search_service.init_search_clients(app.config)

    # 6. 注册Blueprint
    # 为所有路由添加 /api 前缀
    app.register_blueprint(api_blueprint, url_prefix='/api')

    app.logger.info("应用启动成功，运行在 http://0.0.0.0:5000")
    
    return app

app = create_app()

if __name__ == '__main__':
    # 使用 gunicorn 或 uwsgi 部署时，不会执行这部分
    # 仅用于开发环境
    app.run(host='0.0.0.0', port=5001, debug=True)
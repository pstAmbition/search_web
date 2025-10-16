# /unified_service/config.py

import os

class Config:
    """
    统一的配置类
    """
    # Flask 配置
    JSON_AS_ASCII = False
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 限制最大文件为100MB

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    VIDEO_ALLOWED_EXTENSIONS = {'mov', 'mp4', 'avi', 'mkv', 'flv'}
    PICTURE_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    TXT_ALLOWED_EXTENSIONS = {'txt'}

    # 日志配置
    LOG_LEVEL = "INFO"

    # Hugging Face Mirror 配置
    HF_ENDPOINT = 'https://hf-mirror.com'
    
    # NebulaGraph 配置
    NEBULA_HOST = '172.18.112.199'
    NEBULA_PORT = 9669
    NEBULA_USER = 'root'
    NEBULA_PASSWORD = 'p' # 示例密码，请替换为您的真实密码
    NEBULA_SPACE = 'Social_Network_1'
    NEBULA_POOL_SIZE = 10
    
    # Neo4j 配置
<<<<<<< HEAD
    NEO4J_HOST =  'localhost'
    NEO4J_PORT =  7687
    NEO4J_USER = 'neo4j'
    NEO4J_PASSWORD =  'password'
    # 静态文件目录配置（使用原始字符串避免转义问题）
    fake_video_dir = r'D:\work\虚假信息项目\虚假信息库\web_system\search_web\Web-Backend\fake\video'
    fake_img_dir = r'D:\work\虚假信息项目\虚假信息库\web_system\search_web\Web-Backend\fake\img'
=======
    NEO4J_HOST = os.environ.get('NEO4J_HOST', '172.18.112.199')
    NEO4J_PORT = int(os.environ.get('NEO4J_PORT', 7688))
    NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'password')

>>>>>>> bac64e8ef3cb84afe254e5a86877b08b62cb153b
    # Milvus 配置
    MILVUS_URI = "http://172.18.112.199:31800"
    MILVUS_TOKEN = "root:Milvus" # 示例token，请按需修改
    MILVUS_VIDEO_COLLECTION = 'video_1010'
    MILVUS_IMAGE_COLLECTION = 'image_0911'

    # Elasticsearch 配置
    ES_HOSTS = ['http://172.18.112.199:9201']
    ES_AUTH = ('elastic', 'miti963258741') # 示例认证，请替换为您的真实认证信息
    ES_INDEX = 'sns_search_article'

    # MongoDB 配置
    MONGO_HOST = '172.18.112.199'
    # MONGO_HOST = '127.0.0.1'
    MONGO_PORT = 27017
    MONGO_USER = ''  # 本地开发环境可以留空
    MONGO_PASSWORD = ''  # 本地开发环境可以留空
    MONGO_DBNAME = 'admin'  # 用户实际数据库名
    MONGO_COLLECTION = 'event'  # 用户实际集合名

    # Towhee Video Search 配置
    TOWHEE_LEVELDB_PATH = '/data/data/sunye/video_backup.db' # 重要：请替换为您的真实路径
    TOWHEE_DEVICE = 0 # 使用GPU 0, 如果没有GPU请设置为None
import os
from flask import Flask, jsonify
import redis

app = Flask(__name__)

# 1. 从环境变量读取配置
# 这些变量正是我们在 docker-compose.yml 的 environment 字段中注入的
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

# 2. 初始化 Redis 客户端
# decode_responses=True 可以让存取的数据直接是字符串而不是 bytes
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
except Exception as e:
    redis_client = None
    print(f"Redis 初始化失败: {e}")

# 3. 定义前端调用的 API 路由
@app.route('/api/ping', methods=['GET'])
def ping():
    """
    处理 Nginx 代理过来的 GET /api/ping 请求
    """
    # 顺便检查一下 Redis 是否真的连通了，方便本地排错
    redis_status = "connected"
    try:
        if redis_client:
            redis_client.ping()
        else:
            redis_status = "not configured"
    except redis.ConnectionError:
        redis_status = "disconnected"

    # 按照任务书要求返回 JSON 格式 
    return jsonify({
        "status": "ok",
        "redis_connection": redis_status
    })

if __name__ == '__main__':
    # ⚠️ 关键点：在 Docker 容器内运行 Flask，必须绑定到 0.0.0.0
    # 如果用默认的 127.0.0.1，容器外部（包括 Nginx）将无法访问到它
    app.run(host='0.0.0.0', port=5000)
import json
from venv import logger

from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import numpy as np
import joblib
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
import os
# 初始化应用
app = Flask(__name__)


# ================= 配置类 =================
class Config:
    MODEL_PATH = 'medic_predict_model.pkl'
    FEATURE_MEANS_PATH = 'feature_means.npy'
    FEATURE_STDS_PATH = 'feature_stds.npy'
    LOG_FILE = 'app.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    CORS_ORIGINS = ['http://localhost:8080']  # 根据实际前端地址配置

    @classmethod
    def validate_paths(cls):
        required_files = [
            cls.MODEL_PATH,
            cls.FEATURE_MEANS_PATH,
            cls.FEATURE_STDS_PATH
        ]
        for path in required_files:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Required file missing: {path}")

app.config.from_object(Config)

# ================= 安全配置 =================
CORS(app, resources={
    r"/predict": {  # 精确匹配需要CORS的端点
        "origins": "http://localhost:5173",
        "methods": ["POST", "OPTIONS"],  # 精确指定允许的方法
        "allow_headers": ["Content-Type", "X-Request-ID"],  # 明确允许自定义头
        "supports_credentials": True,
        "expose_headers": ["X-Request-ID"],  # 暴露自定义头
        "max_age": 600
    }
})


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        data = request.get_json()
        features = data.get('feature_vector', [])
        if len(features) != 132 or any(v not in (0, 1) for v in features):
            abort(400, description="Invalid feature vector")
        response = jsonify({"status": "preflight accepted"})

        # 动态设置允许的头部
        requested_headers = request.headers.get("Access-Control-Request-Headers", "")
        response.headers.add("Access-Control-Allow-Headers", requested_headers)

        # 确保与CORS配置一致
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Max-Age", "600")
        return response, 200



# ================= 日志配置 =================
def configure_logging():
    """配置结构化日志记录"""
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(module)s:%(lineno)d] %(message)s'
    )

    file_handler = RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=Config.LOG_MAX_SIZE,
        backupCount=Config.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)


configure_logging()


# ================= 全局资源 =================
class MLResources:
    """机器学习资源单例"""
    _instance = None

    def __init__(self):
        try:
            self.model = joblib.load(Config.MODEL_PATH)
            self.feature_means = np.load(Config.FEATURE_MEANS_PATH)
            self.feature_stds = np.load(Config.FEATURE_STDS_PATH)

            # 验证特征维度
            if len(self.feature_means) != 132 or len(self.feature_stds) != 132:
                raise ValueError("特征参数维度不匹配")

            # 验证模型是否具有特征重要性
            self.has_feature_importance = hasattr(self.model, 'feature_importances_')

        except Exception as e:
            app.logger.error(f"资源加载失败: {str(e)}")
            raise

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# ================= 装饰器 =================
def validate_json(f):
    """验证JSON请求装饰器"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            app.logger.warning("非JSON请求")
            return jsonify({"error": "仅支持JSON格式"}), 400
        return f(*args, **kwargs)

    return wrapper


# ================= 全局异常处理 =================
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"未处理异常: {str(e)}", exc_info=True)
    return jsonify(error="服务器内部错误"), 500


@app.route('/')
def home():
    """服务根端点"""
    return jsonify(
        status="running",
        message="Medical Prediction Service",
        version="1.0.0"
    )
# ================= API端点 =================
@app.route('/predict', methods=['POST','OPTIONS'])
@validate_json
def predict():
    """
    病例预测接口
    ---
    tags: [预测服务]
    parameters:
      - in: body
        name: features
        required: true
        schema:
          type: array
          items: {type: number}
          example: [0.1, 0.5, ...] # 132个特征值
    responses:
      200:
        description: 预测结果
        schema:
          $ref: '#/definitions/Prediction'
      400:
        description: 无效输入
      500:
        description: 服务器错误
    """
    data = request.get_json()
    logger.info(f"收到请求数据: {json.dumps(data, indent=2)}")

    if 'feature_vector' not in data:
        logger.error("缺少feature_vector字段")
        return jsonify({"error": "Missing feature_vector"}), 400
    features = data['feature_vector']
    if len(features) != 132 or not all(v in (0, 1) for v in features):
        logger.error(f"无效特征数据: 长度={len(features)}, 类型={set(features)}")
        return jsonify({"error": "Invalid feature format"}), 400
    app.logger.info(
        f"特征统计 - 长度: {len(features)}, "
        f"非零值: {sum(1 for x in features if x != 0)}, "
        f"示例值: {features[:5]}..."
    )
    print("[DEBUG] 特征数组长度:", len(features))
    app.logger.debug(f"收到请求头: {dict(request.headers)}")
    if request.method == 'OPTIONS':
        return jsonify({'status': 'preflight accepted'}), 200
    try:
        # 获取并验证数据
        data = request.get_json()
        app.logger.info(f"收到预测请求，数据长度: {len(data) if isinstance(data, list) else '无效'}")

        # 详细数据校验
        if not isinstance(features, list) or len(features) != 132:
            return jsonify({"error": "需要132维特征数组"}), 400

        # 添加类型校验
        if not all(isinstance(x, (int, float)) for x in features):
            return jsonify({"error": "特征值必须为数字"}), 400

        if len(data) != 132:
            raise ValueError(f"需要132个特征值，收到{len(data)}个")

        if not all(isinstance(x, (int, float)) for x in data):
            raise ValueError("包含非数值类型特征值")

        # 加载资源
        ml_res = MLResources.get_instance()

        # 转换为NumPy数组
        features = np.array(data, dtype=np.float32).reshape(1, -1)
        print("Received features:", features)
        print("Non-zero indices:", [i for i, x in enumerate(features) if x != 0])
        # 特征标准化
        try:
            features = (features - ml_res.feature_means) / ml_res.feature_stds
        except ValueError as e:
            app.logger.error(f"特征标准化失败: {str(e)}")
            return jsonify(error="特征处理失败"), 400

        # 执行预测
        try:
            prediction = ml_res.model.predict(features)[0]
            probabilities = ml_res.model.predict_proba(features)[0]
        except Exception as e:
            app.logger.error(f"预测失败: {str(e)}")
            return jsonify(error="模型预测失败"), 500

        # 构建响应
        response = {
            "risk_level": "high" if prediction == 1 else "low",
            "accuracy": round(float(probabilities.max()) * 100, 2),
            "suggested_treatment": "手术治疗" if prediction == 1 else "保守治疗",
            "risk_scores": {
                "high": round(float(probabilities[1]) * 100, 2),
                "low": round(float(probabilities[0]) * 100, 2)
            }
        }

        # 添加特征重要性（如果可用）
        if ml_res.has_feature_importance:
            response["features"] = [
                {
                    "index": i,
                    "importance": round(float(imp), 4),
                    "normalized_importance": round(float(imp / ml_res.model.feature_importances_.max()), 4)
                }
                for i, imp in enumerate(ml_res.model.feature_importances_)
            ]

        app.logger.info(f"成功完成预测，风险等级: {response['risk_level']}")
        return jsonify(response)

    except ValueError as e:
        app.logger.warning(f"输入验证失败: {str(e)}")
        return jsonify(error=str(e)), 400
    except Exception as e:
        # 记录详细错误日志
        app.logger.error(f"Prediction error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
@app.after_request
def add_cors_headers(response):
    response.headers["X-Requested-With"] = "XMLHttpRequest"
    app.logger.debug(f"Response headers: {dict(response.headers)}")
    return response
# ================= 健康检查 =================
@app.route('/health')
def health_check():
    """服务健康检查端点"""
    try:
        ml_res = MLResources.get_instance()
        return jsonify(
            status="healthy",
            model_type=type(ml_res.model).__name__,
            features_dimension=ml_res.feature_means.shape[0],
            last_loaded=str(ml_res.model.__dict__.get('_last_loaded', '未知'))
            )
    except Exception as e:
        app.logger.error(f"健康检查失败: {str(e)}")
        return jsonify(status="unhealthy", error=str(e)), 500


# ================= 启动配置 =================
if __name__ == '__main__':
    # 预加载资源
    try:
        MLResources.get_instance()
        app.logger.info("服务启动准备就绪")
    except Exception as e:
        app.logger.critical(f"服务启动失败: {str(e)}")
        exit(1)

    # 生产环境配置
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
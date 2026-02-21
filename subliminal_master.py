# -*- coding: utf-8 -*-
"""
Subliminal Master - 潜意识音频合成引擎
Dadan Technology Co., Ltd.

功能：
1. 双轨道输入（肯定句音频 + 背景音乐）
2. 高频调制处理（17.5kHz-19.5kHz）
3. Theta波双耳搏动生成器（430Hz/434Hz）
4. 音量控制滑动条
5. 音轨对齐和循环功能
6. 无损WAV导出

核心逻辑：
隐藏轨（处理后的肯定句）+ 显性轨（背景音乐）+ 频率诱导（可选的双耳搏动）= 最终成品
"""

import os
import sys
import subprocess
import json
import re
import uuid
import time
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from jinja2 import Template

from config import Config
from logger import logger, log_processing_start, log_error
from audio_processor import mix_subliminal_audio, validate_audio_file
from file_cleaner import file_cleaner


def check_dependencies():
    """
    检查必要的依赖是否已安装
    
    返回:
        bool: 所有依赖是否都已安装
    """
    required_packages = ['pydub', 'numpy', 'scipy', 'flask']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"缺少依赖: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True


def install_dependencies():
    """自动检测并安装缺少的Python库"""
    required_packages = ['pydub', 'numpy', 'scipy', 'flask']
    
    print("正在检查系统依赖...")
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"检测到缺失库: {package}，正在自动安装...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"{package} 安装完成。")


if __name__ == '__main__':
    try:
        install_dependencies()
    except Exception as e:
        print(f"环境初始化失败: {e}")
        sys.exit(1)

Config.ensure_folders()
file_cleaner.start()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH


def allowed_file(filename):
    """检查文件是否允许上传"""
    return Config.is_allowed_file(filename)


def sanitize_filename(filename):
    """
    安全处理文件名，添加唯一前缀防止冲突
    
    参数:
        filename: 原始文件名
    
    返回:
        str: 安全的唯一文件名
    """
    filename = secure_filename(filename)
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    unique_prefix = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_"
    return unique_prefix + filename


ERROR_MESSAGES = {
    'missing_files': '请上传肯定句音频和背景音乐',
    'empty_filename': '请选择音频文件',
    'invalid_format': '不支持的文件格式，请上传 MP3、WAV、M4A、AAC 或 FLAC 文件',
    'file_too_large': '文件太大，请上传小于 200MB 的文件',
    'invalid_audio': '音频文件无效或已损坏',
    'config_error': '配置参数格式错误',
    'process_failed': '音频处理失败，请稍后重试',
    'download_failed': '文件下载失败'
}


def get_friendly_error(error_key, detail=None):
    """
    获取用户友好的错误消息
    
    参数:
        error_key: 错误键名
        detail: 详细信息（可选）
    
    返回:
        str: 友好的错误消息
    """
    msg = ERROR_MESSAGES.get(error_key, '操作失败，请稍后重试')
    if detail:
        msg = f"{msg}（{detail}）"
    return msg


@app.route('/')
def index():
    """主页"""
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        template = Template(template_content)
        return template.render(
            version=Config.APP_VERSION,
            config=Config.get_config_dict()
        )
    except Exception as e:
        logger.error(f"渲染模板失败: {e}")
        return "页面加载失败，请刷新重试", 500


@app.route('/process', methods=['POST'])
def process():
    """处理音频文件"""
    try:
        if request.content_length and request.content_length > Config.MAX_CONTENT_LENGTH:
            return jsonify({'success': False, 'error': get_friendly_error('file_too_large')})
        
        if 'affirmation' not in request.files or 'background' not in request.files:
            return jsonify({'success': False, 'error': get_friendly_error('missing_files')})
        
        affirmation_file = request.files['affirmation']
        background_file = request.files['background']
        
        if affirmation_file.filename == '' or background_file.filename == '':
            return jsonify({'success': False, 'error': get_friendly_error('empty_filename')})
        
        if not allowed_file(affirmation_file.filename):
            return jsonify({'success': False, 'error': get_friendly_error('invalid_format')})
        
        if not allowed_file(background_file.filename):
            return jsonify({'success': False, 'error': get_friendly_error('invalid_format')})
        
        try:
            config = json.loads(request.form.get('config', '{}'))
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': get_friendly_error('config_error')})
        
        affirmation_filename = sanitize_filename(affirmation_file.filename)
        background_filename = sanitize_filename(background_file.filename)
        
        affirmation_path = os.path.join(Config.UPLOAD_FOLDER, affirmation_filename)
        background_path = os.path.join(Config.UPLOAD_FOLDER, background_filename)
        
        affirmation_file.save(affirmation_path)
        background_file.save(background_path)
        
        valid, result = validate_audio_file(affirmation_path)
        if not valid:
            return jsonify({'success': False, 'error': get_friendly_error('invalid_audio', '肯定句')})
        
        valid, result = validate_audio_file(background_path)
        if not valid:
            return jsonify({'success': False, 'error': get_friendly_error('invalid_audio', '背景音乐')})
        
        log_processing_start(logger, affirmation_filename, background_filename, config)
        
        def progress_callback(step, total, message):
            logger.info(f"[{step}/{total}] {message}")
        
        success, result = mix_subliminal_audio(
            affirmation_path, 
            background_path, 
            config,
            progress_callback
        )
        
        if success:
            return jsonify({
                'success': True,
                'output_filename': result['output_filename'],
                'file_size_mb': result['file_size_mb'],
                'duration_sec': result['duration_sec']
            })
        else:
            return jsonify({'success': False, 'error': get_friendly_error('process_failed', result)})
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        log_error(logger, str(e), error_trace)
        return jsonify({'success': False, 'error': get_friendly_error('process_failed')})


@app.route('/download/<filename>')
def download(filename):
    """下载处理后的文件"""
    try:
        safe_filename = secure_filename(filename)
        
        if not safe_filename.endswith('.wav'):
            return '无效的文件类型', 400
        
        if '..' in safe_filename or '/' in safe_filename or '\\' in safe_filename:
            return '无效的文件名', 400
        
        file_path = os.path.join(Config.OUTPUT_FOLDER, safe_filename)
        
        abs_output_folder = os.path.abspath(Config.OUTPUT_FOLDER)
        abs_file_path = os.path.abspath(file_path)
        
        if not abs_file_path.startswith(abs_output_folder):
            return '访问被拒绝', 403
        
        if not os.path.exists(file_path):
            return '文件不存在', 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=safe_filename
        )
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return get_friendly_error('download_failed'), 404


@app.route('/health')
def health():
    """健康检查接口"""
    return jsonify({'status': 'ok', 'version': Config.APP_VERSION})


@app.route('/api/config')
def get_config():
    """获取配置信息"""
    return jsonify(Config.get_config_dict())


if __name__ == '__main__':
    print("="*60)
    print(f" 🚀 {Config.APP_NAME} v{Config.APP_VERSION} 启动")
    print("="*60)
    print(f"\n请在浏览器中打开: http://localhost:{Config.PORT}")
    print("\n按 Ctrl+C 停止服务器\n")
    
    app.run(
        host=Config.HOST, 
        port=Config.PORT, 
        debug=Config.DEBUG
    )

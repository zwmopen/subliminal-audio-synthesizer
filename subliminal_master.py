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
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from jinja2 import Template

from config import Config
from logger import logger, log_processing_start, log_error
from audio_processor import mix_subliminal_audio, validate_audio_file
from file_cleaner import file_cleaner

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

try:
    install_dependencies()
except Exception as e:
    print(f"环境初始化失败: {e}")
    input("按回车键退出...")
    sys.exit(1)

Config.ensure_folders()

file_cleaner.start()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

def allowed_file(filename):
    """检查文件是否允许上传"""
    return Config.is_allowed_file(filename)

def sanitize_filename(filename):
    """安全处理文件名"""
    filename = secure_filename(filename)
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    return filename

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
        return f"模板加载失败: {e}", 500

@app.route('/process', methods=['POST'])
def process():
    """处理音频文件"""
    try:
        if 'affirmation' not in request.files or 'background' not in request.files:
            return jsonify({'success': False, 'error': '缺少音频文件'})
        
        affirmation_file = request.files['affirmation']
        background_file = request.files['background']
        
        if affirmation_file.filename == '' or background_file.filename == '':
            return jsonify({'success': False, 'error': '请选择音频文件'})
        
        if not allowed_file(affirmation_file.filename):
            return jsonify({'success': False, 'error': f'不支持的文件格式: {affirmation_file.filename}'})
        
        if not allowed_file(background_file.filename):
            return jsonify({'success': False, 'error': f'不支持的文件格式: {background_file.filename}'})
        
        try:
            config = json.loads(request.form.get('config', '{}'))
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': '配置参数格式错误'})
        
        affirmation_filename = sanitize_filename(affirmation_file.filename)
        background_filename = sanitize_filename(background_file.filename)
        
        affirmation_path = os.path.join(Config.UPLOAD_FOLDER, affirmation_filename)
        background_path = os.path.join(Config.UPLOAD_FOLDER, background_filename)
        
        affirmation_file.save(affirmation_path)
        background_file.save(background_path)
        
        valid, result = validate_audio_file(affirmation_path)
        if not valid:
            return jsonify({'success': False, 'error': f'肯定句音频无效: {result}'})
        
        valid, result = validate_audio_file(background_path)
        if not valid:
            return jsonify({'success': False, 'error': f'背景音乐无效: {result}'})
        
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
            return jsonify({'success': False, 'error': result})
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        log_error(logger, str(e), error_trace)
        return jsonify({'success': False, 'error': str(e)})

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
        
        if not os.path.exists(file_path):
            return '文件不存在', 404
        
        if not os.path.abspath(file_path).startswith(os.path.abspath(Config.OUTPUT_FOLDER)):
            return '访问被拒绝', 403
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=safe_filename
        )
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return str(e), 404

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

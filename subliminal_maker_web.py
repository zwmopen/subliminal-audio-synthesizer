# -*- coding: utf-8 -*-
"""
Dadan Technology Co., Ltd. - Subliminal Audio Generator
达丹科技 - 潜意识音频生成器 (Web界面版)

功能：
1. 自动将人声肯定语转化为静默阈下音频 (17.5kHz载波调制)
2. 自动生成 Theta 双耳节拍 (4Hz差频)
3. 自动混音并输出
4. 支持用户输入参数调整
5. Web可视化界面
6. 全自动依赖管理和环境检查

Author: Gemini (Your AI Thought Partner)
Date: 2026-02-11

使用说明：
1. 运行此脚本
2. 在浏览器中打开 http://localhost:5000
3. 上传音频文件或选择文件夹
4. 调整参数并开始处理
5. 下载处理后的音频文件
"""

import os
import sys
import subprocess
import time
import math
import json
import threading
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import io
import base64

# --- 第一步：自动环境检查与依赖安装 ---
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
    import numpy as np
    from scipy.io import wavfile
    from scipy import signal
    from pydub import AudioSegment
    from pydub.generators import Sine
    from flask import Flask, render_template_string, request, jsonify, send_file
except Exception as e:
    print(f"环境初始化失败: {e}")
    import traceback
    traceback.print_exc()
    input("按回车键退出...")
    sys.exit(1)

# --- 第二步：配置 ---

CONFIG = {
    'carrier_freq': 17500,
    'binaural_left_freq': 430,
    'binaural_right_freq': 434,
    'binaural_volume_db': -15,
    'voice_volume_db': 0,
    'supported_extensions': ('.mp3', '.wav', '.m4a', '.aac'),
    'output_folder': '已处理',
    'upload_folder': 'uploads'
}

# 创建Flask应用
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 最大100MB

# 确保必要的文件夹存在
for folder in [CONFIG['upload_folder'], CONFIG['output_folder']]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- 第三步：核心逻辑函数 ---

def generate_binaural_beat(duration_ms, left_freq, right_freq, volume_db):
    """生成双耳节拍立体声轨道"""
    print(f"   -> 正在生成双耳节拍 ({left_freq}Hz / {right_freq}Hz)...")
    
    left_channel = Sine(left_freq).to_audio_segment(duration=duration_ms)
    right_channel = Sine(right_freq).to_audio_segment(duration=duration_ms)
    binaural_beat = AudioSegment.from_mono_audiosegments(left_channel, right_channel)
    binaural_beat = binaural_beat + volume_db
    
    return binaural_beat

def process_silent_subliminal(audio_segment, carrier_freq):
    """使用振幅调制将音频移至高频段"""
    print(f"   -> 正在进行高频调制 (载波: {carrier_freq}Hz)...")
    
    target_sample_rate = 44100
    audio = audio_segment.set_channels(1).set_frame_rate(target_sample_rate)
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    
    duration_sec = len(samples) / target_sample_rate
    t = np.linspace(0, duration_sec, len(samples), endpoint=False)
    carrier = np.sin(2 * np.pi * carrier_freq * t)
    
    modulated_signal = samples * carrier
    
    max_val = np.max(np.abs(modulated_signal))
    if max_val > 0:
        modulated_signal = (modulated_signal / max_val) * (2**15 - 1)
    
    modulated_samples = modulated_signal.astype(np.int16)
    processed_audio = audio._spawn(modulated_samples.tobytes())
    
    return processed_audio

def process_audio_file(file_path, config):
    """处理单个音频文件"""
    try:
        print(f"🎧 正在处理: {os.path.basename(file_path)}")
        
        original_audio = AudioSegment.from_file(file_path)
        
        silent_audio = process_silent_subliminal(original_audio, config['carrier_freq'])
        silent_audio = silent_audio + config['voice_volume_db']

        duration_ms = len(original_audio)
        binaural_beat = generate_binaural_beat(
            duration_ms, 
            config['binaural_left_freq'], 
            config['binaural_right_freq'],
            config['binaural_volume_db']
        )

        if len(silent_audio) > len(binaural_beat):
            silent_audio = silent_audio[:len(binaural_beat)]
        else:
            binaural_beat = binaural_beat[:len(silent_audio)]

        final_mix = silent_audio.overlay(binaural_beat)

        output_filename = f"Subliminal_{os.path.splitext(os.path.basename(file_path))[0]}.wav"
        output_path = os.path.join(CONFIG['output_folder'], output_filename)
        
        final_mix.export(output_path, format="wav")
        
        print(f"✅ 完成! 已保存至: {output_filename}")
        return True, output_path
    except Exception as e:
        print(f"❌ 处理 {os.path.basename(file_path)} 时出错: {e}")
        return False, str(e)

# --- 第四步：Web界面 ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>潜意识音频生成器</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: #e0e5ec;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 
                20px 20px 60px #bebebe,
                -20px -20px 60px #ffffff;
        }
        
        h1 {
            text-align: center;
            color: #2d3436;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        
        .subtitle {
            text-align: center;
            color: #636e72;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        
        .section {
            background: #e0e5ec;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 
                inset 8px 8px 16px #bebebe,
                inset -8px -8px 16px #ffffff;
        }
        
        .section-title {
            font-size: 1.3em;
            color: #2d3436;
            margin-bottom: 15px;
            font-weight: bold;
        }
        
        .upload-area {
            border: 3px dashed #a3b1c6;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: #e0e5ec;
        }
        
        .upload-area:hover {
            border-color: #6c5ce7;
            background: #d1d9e6;
        }
        
        .upload-area.dragover {
            border-color: #6c5ce7;
            background: #d1d9e6;
        }
        
        .file-list {
            margin-top: 20px;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .file-item {
            background: #d1d9e6;
            padding: 10px 15px;
            margin: 5px 0;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .file-item .filename {
            color: #2d3436;
            font-weight: 500;
        }
        
        .file-item .remove-btn {
            background: #ff7675;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
        }
        
        .param-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        
        .param-item {
            display: flex;
            flex-direction: column;
        }
        
        .param-item label {
            color: #2d3436;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .param-item input {
            background: #e0e5ec;
            border: none;
            padding: 12px 15px;
            border-radius: 10px;
            font-size: 1em;
            color: #2d3436;
            box-shadow: 
                inset 4px 4px 8px #bebebe,
                inset -4px -4px 8px #ffffff;
        }
        
        .param-item input:focus {
            outline: none;
            box-shadow: 
                inset 6px 6px 12px #bebebe,
                inset -6px -6px 12px #ffffff;
        }
        
        .param-hint {
            color: #636e72;
            font-size: 0.85em;
            margin-top: 5px;
        }
        
        .btn {
            background: #e0e5ec;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            color: #2d3436;
            box-shadow: 
                6px 6px 12px #bebebe,
                -6px -6px 12px #ffffff;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            box-shadow: 
                4px 4px 8px #bebebe,
                -4px -4px 8px #ffffff;
        }
        
        .btn:active {
            box-shadow: 
                inset 4px 4px 8px #bebebe,
                inset -4px -4px 8px #ffffff;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
            color: white;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ff7675 0%, #d63031 100%);
            color: white;
        }
        
        .button-group {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 20px;
        }
        
        .progress-container {
            margin-top: 20px;
            display: none;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e0e5ec;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 
                inset 4px 4px 8px #bebebe,
                inset -4px -4px 8px #ffffff;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
            width: 0%;
            transition: width 0.3s ease;
        }
        
        .status-text {
            text-align: center;
            margin-top: 10px;
            color: #2d3436;
            font-weight: 500;
        }
        
        .result-container {
            margin-top: 20px;
            display: none;
        }
        
        .result-item {
            background: #d1d9e6;
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .result-item .filename {
            color: #2d3436;
            font-weight: 500;
        }
        
        .download-btn {
            background: linear-gradient(135deg, #0984e3 0%, #6c5ce7 100%);
            color: white;
            text-decoration: none;
            padding: 8px 20px;
            border-radius: 8px;
            font-weight: 500;
        }
        
        .alert {
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 1.8em;
            }
            
            .button-group {
                flex-direction: column;
            }
            
            .btn {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎧 潜意识音频生成器</h1>
        <p class="subtitle">将人声肯定语转化为静默阈下音频</p>
        
        <div id="alertBox" class="alert"></div>
        
        <div class="section">
            <div class="section-title">📁 上传音频文件</div>
            <div class="upload-area" id="uploadArea">
                <p>点击或拖拽音频文件到此处</p>
                <p style="color: #636e72; margin-top: 10px;">支持格式: MP3, WAV, M4A, AAC</p>
                <input type="file" id="fileInput" multiple accept=".mp3,.wav,.m4a,.aac" style="display: none;">
            </div>
            <div class="file-list" id="fileList"></div>
        </div>
        
        <div class="section">
            <div class="section-title">⚙️ 参数设置</div>
            <div class="param-grid">
                <div class="param-item">
                    <label>载波频率 (Hz)</label>
                    <input type="number" id="carrierFreq" value="17500">
                    <span class="param-hint">建议: 17500-19500</span>
                </div>
                <div class="param-item">
                    <label>左耳频率 (Hz)</label>
                    <input type="number" id="leftFreq" value="430">
                </div>
                <div class="param-item">
                    <label>右耳频率 (Hz)</label>
                    <input type="number" id="rightFreq" value="434">
                    <span class="param-hint">差频: 4Hz Theta波</span>
                </div>
                <div class="param-item">
                    <label>双耳节拍音量 (dB)</label>
                    <input type="number" id="binauralVol" value="-15">
                    <span class="param-hint">建议: -15 左右</span>
                </div>
                <div class="param-item">
                    <label>人声音量 (dB)</label>
                    <input type="number" id="voiceVol" value="0">
                    <span class="param-hint">0 为原始音量</span>
                </div>
            </div>
        </div>
        
        <div class="button-group">
            <button class="btn btn-primary" id="processBtn" onclick="startProcessing()">
                🎵 开始处理
            </button>
            <button class="btn btn-danger" onclick="clearFiles()">
                清空列表
            </button>
        </div>
        
        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <p class="status-text" id="statusText">准备处理...</p>
        </div>
        
        <div class="result-container" id="resultContainer">
            <div class="section-title">📥 处理结果</div>
            <div id="resultList"></div>
        </div>
    </div>
    
    <script>
        let uploadedFiles = [];
        
        // 文件上传区域事件
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });
        
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });
        
        function handleFiles(files) {
            const validExtensions = ['.mp3', '.wav', '.m4a', '.aac'];
            
            for (let file of files) {
                const ext = '.' + file.name.split('.').pop().toLowerCase();
                if (validExtensions.includes(ext)) {
                    uploadedFiles.push(file);
                }
            }
            
            updateFileList();
        }
        
        function updateFileList() {
            const fileList = document.getElementById('fileList');
            fileList.innerHTML = '';
            
            uploadedFiles.forEach((file, index) => {
                const item = document.createElement('div');
                item.className = 'file-item';
                item.innerHTML = `
                    <span class="filename">${file.name}</span>
                    <button class="remove-btn" onclick="removeFile(${index})">删除</button>
                `;
                fileList.appendChild(item);
            });
        }
        
        function removeFile(index) {
            uploadedFiles.splice(index, 1);
            updateFileList();
        }
        
        function clearFiles() {
            uploadedFiles = [];
            updateFileList();
            document.getElementById('resultContainer').style.display = 'none';
            document.getElementById('progressContainer').style.display = 'none';
        }
        
        function showAlert(message, type) {
            const alertBox = document.getElementById('alertBox');
            alertBox.textContent = message;
            alertBox.className = `alert alert-${type}`;
            alertBox.style.display = 'block';
            
            setTimeout(() => {
                alertBox.style.display = 'none';
            }, 5000);
        }
        
        async function startProcessing() {
            if (uploadedFiles.length === 0) {
                showAlert('请先上传音频文件！', 'error');
                return;
            }
            
            const processBtn = document.getElementById('processBtn');
            const progressContainer = document.getElementById('progressContainer');
            const progressFill = document.getElementById('progressFill');
            const statusText = document.getElementById('statusText');
            const resultContainer = document.getElementById('resultContainer');
            const resultList = document.getElementById('resultList');
            
            processBtn.disabled = true;
            progressContainer.style.display = 'block';
            resultContainer.style.display = 'none';
            resultList.innerHTML = '';
            
            const config = {
                carrier_freq: parseFloat(document.getElementById('carrierFreq').value),
                binaural_left_freq: parseFloat(document.getElementById('leftFreq').value),
                binaural_right_freq: parseFloat(document.getElementById('rightFreq').value),
                binaural_volume_db: parseFloat(document.getElementById('binauralVol').value),
                voice_volume_db: parseFloat(document.getElementById('voiceVol').value)
            };
            
            const results = [];
            
            for (let i = 0; i < uploadedFiles.length; i++) {
                const file = uploadedFiles[i];
                const progress = ((i + 1) / uploadedFiles.length * 100).toFixed(1);
                
                progressFill.style.width = progress + '%';
                statusText.textContent = `正在处理: ${file.name} (${i + 1}/${uploadedFiles.length})`;
                
                const formData = new FormData();
                formData.append('file', file);
                formData.append('config', JSON.stringify(config));
                
                try {
                    const response = await fetch('/process', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    results.push(result);
                } catch (error) {
                    results.push({
                        success: false,
                        filename: file.name,
                        error: error.message
                    });
                }
            }
            
            // 显示结果
            resultContainer.style.display = 'block';
            
            let successCount = 0;
            results.forEach(result => {
                const item = document.createElement('div');
                item.className = 'result-item';
                
                if (result.success) {
                    successCount++;
                    item.innerHTML = `
                        <span class="filename">✅ ${result.filename}</span>
                        <a href="/download/${result.output_filename}" class="download-btn">下载</a>
                    `;
                } else {
                    item.innerHTML = `
                        <span class="filename">❌ ${result.filename} - ${result.error}</span>
                    `;
                }
                
                resultList.appendChild(item);
            });
            
            statusText.textContent = `处理完成: ${successCount}/${uploadedFiles.length} 个文件成功`;
            processBtn.disabled = false;
            
            if (successCount === uploadedFiles.length) {
                showAlert(`全部处理成功！共 ${successCount} 个文件`, 'success');
            } else {
                showAlert(`处理完成: ${successCount}/${uploadedFiles.length} 个文件成功`, 'error');
            }
        }
    </script>
</body>
</html>
"""

# --- 第五步：Flask路由 ---

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process():
    """处理音频文件"""
    try:
        file = request.files['file']
        config = json.loads(request.form['config'])
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        upload_path = os.path.join(CONFIG['upload_folder'], filename)
        file.save(upload_path)
        
        # 处理文件
        success, result = process_audio_file(upload_path, config)
        
        if success:
            return jsonify({
                'success': True,
                'filename': filename,
                'output_filename': os.path.basename(result)
            })
        else:
            return jsonify({
                'success': False,
                'filename': filename,
                'error': result
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'filename': file.filename if file else 'unknown',
            'error': str(e)
        })

@app.route('/download/<filename>')
def download(filename):
    """下载处理后的文件"""
    try:
        return send_file(
            os.path.join(CONFIG['output_folder'], filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return str(e), 404

# --- 第六步：主程序 ---

if __name__ == '__main__':
    print("="*60)
    print(" 🚀 达丹科技 - 潜意识音频生成器 (Web版) 启动")
    print("="*60)
    print("\n请在浏览器中打开: http://localhost:5000")
    print("\n按 Ctrl+C 停止服务器\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

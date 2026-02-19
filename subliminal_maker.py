# -*- coding: utf-8 -*-
"""
Dadan Technology Co., Ltd. - Subliminal Audio Generator
达丹科技 - 潜意识音频生成器 (拟态风格版)

功能：
1. 自动将人声肯定语转化为静默阈下音频 (17.5kHz载波调制)
2. 自动生成 Theta 双耳节拍 (4Hz差频)
3. 自动混音并输出
4. 支持用户输入参数调整
5. 拟态风格可视化界面
6. 全自动依赖管理和环境检查

Author: Gemini (Your AI Thought Partner)
Date: 2026-02-11

使用说明：
1. 将此脚本放在包含录音文件的文件夹中
2. 双击运行脚本
3. 可选择使用默认参数或自定义参数
4. 脚本会自动处理所有音频文件并生成"已处理"文件夹
5. 全程无需手动操作，全自动完成

详细说明见下方配置区和注释
"""

import os
import sys
import subprocess
import time
import math

# --- 第一步：自动环境检查与依赖安装 ---
def install_dependencies():
    """自动检测并安装缺少的Python库"""
    # 基础依赖
    required_packages = ['pydub', 'numpy', 'scipy']
    
    print("正在检查系统依赖...")
    
    # 安装基础依赖
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
    
    # 尝试导入GUI库 - 分步导入避免messagebox问题
    try:
        print("尝试导入tkinter...")
        import tkinter as tk
        print("tkinter导入成功")
        
        print("尝试导入ttk...")
        from tkinter import ttk
        print("ttk导入成功")
        
        print("尝试导入filedialog...")
        from tkinter import filedialog
        print("filedialog导入成功")
        
        # messagebox可能有问题，延迟导入
        messagebox_available = False
        try:
            print("尝试导入messagebox...")
            from tkinter import messagebox
            messagebox_available = True
            print("messagebox导入成功")
        except Exception as e:
            print(f"警告: messagebox导入失败: {e}")
            print("将使用print输出替代messagebox")
        
        GUI_AVAILABLE = True
        print("检测到GUI环境，将以图形界面模式运行...")
    except ImportError as e:
        print(f"警告: 无法导入GUI库，将以命令行模式运行: {e}")
        GUI_AVAILABLE = False
except Exception as e:
    print(f"环境初始化失败: {e}")
    import traceback
    traceback.print_exc()
    input("按回车键退出...")
    sys.exit(1)

# --- 第二步：用户可编辑配置区 (USER CONFIG) ---

# 注意：以下配置为默认值，运行时会显示在界面中供用户调整
# 如果不需要调整，直接使用默认参数或自定义参数
# 详细说明见注释

CONFIG = {
    # [静默音频参数]
    # 载波频率：视频建议 17500Hz - 19500Hz。
    # 这会将你的人声搬运到这个频率附近，使其变得"听不见"。
    # 频率越高，越不容易被听到，但也要考虑音频设备的播放能力
    'carrier_freq': 17500, 
    
    # [双耳节拍参数 - Theta波]
    # 左耳频率 (Hz)
    'binaural_left_freq': 430,
    # 右耳频率 (Hz) - 差值即为脑波频率 (434 - 430 = 4Hz Theta)
    # Theta波 (4-8Hz) 有助于放松、冥想和潜意识接收
    'binaural_right_freq': 434,
    # 双耳节拍的音量 (dB)，建议不要太响，作为背景音
    # 负值表示低于原始音量，-15dB 大约是原始音量的 1/3
    'binaural_volume_db': -15,

    # [原始人声参数]
    # 处理后的人声音量 (dB)。因为调制后能量会分散，可能需要稍微提升一点，或者保持默认
    # 0表示保持原始音量，正值表示增大音量，负值表示减小音量
    'voice_volume_db': 0,

    # [文件设置]
    # 支持的输入格式
    'supported_extensions': ('.mp3', '.wav', '.m4a', '.aac'),
    # 输出文件夹名称 - 按照用户要求修改为"已处理"
    'output_folder': '已处理'
}

# --- 第三步：核心逻辑函数 (请勿随意修改，除非你懂信号处理) ---

def generate_binaural_beat(duration_ms, left_freq, right_freq, volume_db):
    """
    生成双耳节拍立体声轨道
    
    参数:
        duration_ms: 音频时长 (毫秒)
        left_freq: 左声道频率 (Hz)
        right_freq: 右声道频率 (Hz)
        volume_db: 音量调整值 (dB)
    
    返回:
        AudioSegment: 生成的双耳节拍音频
    """
    print(f"   -> 正在生成双耳节拍 ({left_freq}Hz / {right_freq}Hz)...")
    
    # 生成左声道正弦波
    left_channel = Sine(left_freq).to_audio_segment(duration=duration_ms)
    # 生成右声道正弦波
    right_channel = Sine(right_freq).to_audio_segment(duration=duration_ms)
    
    # 合并为立体声
    binaural_beat = AudioSegment.from_mono_audiosegments(left_channel, right_channel)
    
    # 调整音量
    binaural_beat = binaural_beat + volume_db
    return binaural_beat

def process_silent_subliminal(audio_segment, carrier_freq):
    """
    使用振幅调制 (Amplitude Modulation) 将音频移至高频段。
    这是实现 'Silent Subliminal' 的科学方法。
    
    参数:
        audio_segment: 原始音频 (AudioSegment)
        carrier_freq: 载波频率 (Hz)
    
    返回:
        AudioSegment: 处理后的静默阈下音频
    """
    print(f"   -> 正在进行高频调制 (载波: {carrier_freq}Hz)...")
    
    # 1. 预处理：确保是单声道，并统一采样率
    # 44100Hz是标准CD音质采样率，足够处理高频信号
    target_sample_rate = 44100
    audio = audio_segment.set_channels(1).set_frame_rate(target_sample_rate)
    
    # 2. 转换为 Numpy 数组进行数学运算
    # pydub 获取的是 int 数据，我们需要 float 来做乘法
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    
    # 3. 生成载波 (Carrier Wave)
    # 创建一个与音频等长的正弦波作为载波
    duration_sec = len(samples) / target_sample_rate
    t = np.linspace(0, duration_sec, len(samples), endpoint=False)
    carrier = np.sin(2 * np.pi * carrier_freq * t)
    
    # 4. 振幅调制 (AM): 原始信号 * 载波
    # 这会将频谱搬移到 载波频率 ± 原始频率 的位置
    # 例如：原始人声频率范围是 300-3000Hz，调制后会移到 17500±3000Hz 范围
    # 这个范围的声音通常超出人类听觉范围，因此变得"听不见"
    modulated_signal = samples * carrier
    
    # 5. 标准化防止爆音
    # 调制后信号的振幅可能会变化，需要标准化到16位音频范围
    max_val = np.max(np.abs(modulated_signal))
    if max_val > 0:
        modulated_signal = (modulated_signal / max_val) * (2**15 - 1) # 还原到 16-bit 范围
    
    # 6. 转回 AudioSegment
    modulated_samples = modulated_signal.astype(np.int16)
    processed_audio = audio._spawn(modulated_samples.tobytes())
    
    return processed_audio

# --- 第四步：用户输入参数界面 ---

class NeumorphismStyle:
    """拟态风格样式类"""
    
    # 颜色配置
    BG_COLOR = "#e0e5ec"  # 主背景色
    LIGHT_SHADOW = "#ffffff"  # 亮阴影
    DARK_SHADOW = "#a3b1c6"  # 暗阴影
    TEXT_COLOR = "#2d3436"  # 文字颜色
    ACCENT_COLOR = "#6c5ce7"  # 强调色
    
    @staticmethod
    def create_neumorphic_frame(parent, **kwargs):
        """创建拟态风格框架"""
        frame = tk.Frame(
            parent,
            bg=NeumorphismStyle.BG_COLOR,
            **kwargs
        )
        return frame
    
    @staticmethod
    def create_neumorphic_button(parent, text, command, **kwargs):
        """创建拟态风格按钮"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=NeumorphismStyle.BG_COLOR,
            fg=NeumorphismStyle.TEXT_COLOR,
            activebackground=NeumorphismStyle.BG_COLOR,
            activeforeground=NeumorphismStyle.TEXT_COLOR,
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            font=("微软雅黑", 10, "bold"),
            **kwargs
        )
        
        # 添加拟态阴影效果
        def on_enter(e):
            btn.config(bg="#d1d9e6")
        
        def on_leave(e):
            btn.config(bg=NeumorphismStyle.BG_COLOR)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    @staticmethod
    def create_neumorphic_entry(parent, textvariable, **kwargs):
        """创建拟态风格输入框"""
        entry = tk.Entry(
            parent,
            textvariable=textvariable,
            bg=NeumorphismStyle.BG_COLOR,
            fg=NeumorphismStyle.TEXT_COLOR,
            insertbackground=NeumorphismStyle.TEXT_COLOR,
            relief=tk.FLAT,
            bd=0,
            font=("微软雅黑", 10),
            **kwargs
        )
        return entry

def show_message(title, message, msg_type="info"):
    """显示消息（兼容messagebox不可用的情况）"""
    if messagebox_available:
        try:
            from tkinter import messagebox
            if msg_type == "info":
                messagebox.showinfo(title, message)
            elif msg_type == "warning":
                messagebox.showwarning(title, message)
            elif msg_type == "error":
                messagebox.showerror(title, message)
        except Exception:
            print(f"[{title}] {message}")
    else:
        print(f"[{title}] {message}")

def get_user_inputs_gui():
    """
    显示GUI界面，获取用户输入参数
    
    返回:
        dict: 用户调整后的配置参数
    """
    # 创建主窗口
    root = tk.Tk()
    root.title("达丹科技 - 潜意识音频生成器")
    root.geometry("700x600")
    root.resizable(True, True)
    root.configure(bg=NeumorphismStyle.BG_COLOR)
    
    # 存储选中的文件
    selected_files = []
    
    # 创建主框架
    main_frame = NeumorphismStyle.create_neumorphic_frame(root, padx=40, pady=30)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 创建标题
    title_frame = NeumorphismStyle.create_neumorphic_frame(main_frame)
    title_frame.pack(fill=tk.X, pady=(0, 20))
    
    title_label = tk.Label(
        title_frame,
        text="🎧 潜意识音频生成器",
        font=("微软雅黑", 20, "bold"),
        bg=NeumorphismStyle.BG_COLOR,
        fg=NeumorphismStyle.TEXT_COLOR
    )
    title_label.pack(pady=10)
    
    subtitle_label = tk.Label(
        title_frame,
        text="将人声肯定语转化为静默阈下音频",
        font=("微软雅黑", 10),
        bg=NeumorphismStyle.BG_COLOR,
        fg="#636e72"
    )
    subtitle_label.pack(pady=(0, 10))
    
    # 创建文件选择区域
    file_frame = NeumorphismStyle.create_neumorphic_frame(main_frame)
    file_frame.pack(fill=tk.X, pady=10)
    
    file_label = tk.Label(
        file_frame,
        text="📁 选择音频文件或文件夹",
        font=("微软雅黑", 12, "bold"),
        bg=NeumorphismStyle.BG_COLOR,
        fg=NeumorphismStyle.TEXT_COLOR
    )
    file_label.pack(anchor=tk.W, pady=(0, 10))
    
    # 文件列表显示区域
    file_list_frame = NeumorphismStyle.create_neumorphic_frame(file_frame)
    file_list_frame.pack(fill=tk.X, pady=5)
    
    file_listbox = tk.Listbox(
        file_list_frame,
        bg=NeumorphismStyle.BG_COLOR,
        fg=NeumorphismStyle.TEXT_COLOR,
        selectbackground="#d1d9e6",
        selectforeground=NeumorphismStyle.TEXT_COLOR,
        relief=tk.FLAT,
        bd=0,
        font=("微软雅黑", 9),
        height=4
    )
    file_listbox.pack(fill=tk.X, padx=5, pady=5)
    
    # 文件选择按钮框架
    file_btn_frame = NeumorphismStyle.create_neumorphic_frame(file_frame)
    file_btn_frame.pack(fill=tk.X, pady=10)
    
    def select_files():
        """选择文件"""
        files = filedialog.askopenfilenames(
            title="选择音频文件",
            filetypes=[
                ("音频文件", "*.mp3 *.wav *.m4a *.aac"),
                ("所有文件", "*.*")
            ]
        )
        if files:
            selected_files.clear()
            selected_files.extend(files)
            update_file_list()
    
    def select_folder():
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择包含音频文件的文件夹")
        if folder:
            selected_files.clear()
            # 扫描文件夹中的所有音频文件
            for root_dir, _, files in os.walk(folder):
                for filename in files:
                    if any(filename.lower().endswith(ext) for ext in CONFIG['supported_extensions']):
                        file_path = os.path.join(root_dir, filename)
                        selected_files.append(file_path)
            update_file_list()
    
    def update_file_list():
        """更新文件列表显示"""
        file_listbox.delete(0, tk.END)
        for file_path in selected_files:
            file_listbox.insert(tk.END, os.path.basename(file_path))
        if selected_files:
            file_count_label.config(text=f"已选择 {len(selected_files)} 个文件")
        else:
            file_count_label.config(text="未选择文件")
    
    select_files_btn = NeumorphismStyle.create_neumorphic_button(
        file_btn_frame,
        text="选择文件",
        command=select_files
    )
    select_files_btn.pack(side=tk.LEFT, padx=5)
    
    select_folder_btn = NeumorphismStyle.create_neumorphic_button(
        file_btn_frame,
        text="选择文件夹",
        command=select_folder
    )
    select_folder_btn.pack(side=tk.LEFT, padx=5)
    
    clear_btn = NeumorphismStyle.create_neumorphic_button(
        file_btn_frame,
        text="清空列表",
        command=lambda: (selected_files.clear(), update_file_list())
    )
    clear_btn.pack(side=tk.LEFT, padx=5)
    
    file_count_label = tk.Label(
        file_btn_frame,
        text="未选择文件",
        font=("微软雅黑", 9),
        bg=NeumorphismStyle.BG_COLOR,
        fg="#636e72"
    )
    file_count_label.pack(side=tk.RIGHT, padx=5)
    
    # 创建参数框架
    params_frame = NeumorphismStyle.create_neumorphic_frame(main_frame)
    params_frame.pack(fill=tk.X, pady=10)
    
    params_label = tk.Label(
        params_frame,
        text="⚙️ 参数设置",
        font=("微软雅黑", 12, "bold"),
        bg=NeumorphismStyle.BG_COLOR,
        fg=NeumorphismStyle.TEXT_COLOR
    )
    params_label.pack(anchor=tk.W, pady=(0, 10))
    
    # 参数设置区域
    params_grid = NeumorphismStyle.create_neumorphic_frame(params_frame)
    params_grid.pack(fill=tk.X)
    
    # 载波频率设置
    carrier_label = tk.Label(
        params_grid,
        text="载波频率 (Hz):",
        font=("微软雅黑", 10),
        bg=NeumorphismStyle.BG_COLOR,
        fg=NeumorphismStyle.TEXT_COLOR
    )
    carrier_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    
    carrier_var = tk.DoubleVar(value=CONFIG['carrier_freq'])
    carrier_entry = NeumorphismStyle.create_neumorphic_entry(params_grid, carrier_var, width=15)
    carrier_entry.grid(row=0, column=1, padx=5, pady=5)
    
    carrier_hint = tk.Label(
        params_grid,
        text="(建议: 17500-19500)",
        font=("微软雅黑", 9),
        bg=NeumorphismStyle.BG_COLOR,
        fg="#636e72"
    )
    carrier_hint.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
    
    # 左耳频率设置
    left_freq_label = tk.Label(
        params_grid,
        text="左耳频率 (Hz):",
        font=("微软雅黑", 10),
        bg=NeumorphismStyle.BG_COLOR,
        fg=NeumorphismStyle.TEXT_COLOR
    )
    left_freq_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    
    left_freq_var = tk.DoubleVar(value=CONFIG['binaural_left_freq'])
    left_freq_entry = NeumorphismStyle.create_neumorphic_entry(params_grid, left_freq_var, width=15)
    left_freq_entry.grid(row=1, column=1, padx=5, pady=5)
    
    # 右耳频率设置
    right_freq_label = tk.Label(
        params_grid,
        text="右耳频率 (Hz):",
        font=("微软雅黑", 10),
        bg=NeumorphismStyle.BG_COLOR,
        fg=NeumorphismStyle.TEXT_COLOR
    )
    right_freq_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    
    right_freq_var = tk.DoubleVar(value=CONFIG['binaural_right_freq'])
    right_freq_entry = NeumorphismStyle.create_neumorphic_entry(params_grid, right_freq_var, width=15)
    right_freq_entry.grid(row=2, column=1, padx=5, pady=5)
    
    theta_hint = tk.Label(
        params_grid,
        text=f"(差频: {CONFIG['binaural_right_freq'] - CONFIG['binaural_left_freq']}Hz Theta波)",
        font=("微软雅黑", 9),
        bg=NeumorphismStyle.BG_COLOR,
        fg="#636e72"
    )
    theta_hint.grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
    
    # 双耳节拍音量设置
    binaural_vol_label = tk.Label(
        params_grid,
        text="双耳节拍音量 (dB):",
        font=("微软雅黑", 10),
        bg=NeumorphismStyle.BG_COLOR,
        fg=NeumorphismStyle.TEXT_COLOR
    )
    binaural_vol_label.grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    
    binaural_vol_var = tk.DoubleVar(value=CONFIG['binaural_volume_db'])
    binaural_vol_entry = NeumorphismStyle.create_neumorphic_entry(params_grid, binaural_vol_var, width=15)
    binaural_vol_entry.grid(row=3, column=1, padx=5, pady=5)
    
    binaural_vol_hint = tk.Label(
        params_grid,
        text="(建议: -15 左右)",
        font=("微软雅黑", 9),
        bg=NeumorphismStyle.BG_COLOR,
        fg="#636e72"
    )
    binaural_vol_hint.grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
    
    # 人声音量设置
    voice_vol_label = tk.Label(
        params_grid,
        text="人声音量 (dB):",
        font=("微软雅黑", 10),
        bg=NeumorphismStyle.BG_COLOR,
        fg=NeumorphismStyle.TEXT_COLOR
    )
    voice_vol_label.grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
    
    voice_vol_var = tk.DoubleVar(value=CONFIG['voice_volume_db'])
    voice_vol_entry = NeumorphismStyle.create_neumorphic_entry(params_grid, voice_vol_var, width=15)
    voice_vol_entry.grid(row=4, column=1, padx=5, pady=5)
    
    voice_vol_hint = tk.Label(
        params_grid,
        text="(0 为原始音量)",
        font=("微软雅黑", 9),
        bg=NeumorphismStyle.BG_COLOR,
        fg="#636e72"
    )
    voice_vol_hint.grid(row=4, column=2, sticky=tk.W, padx=5, pady=5)
    
    # 状态显示区域
    status_frame = NeumorphismStyle.create_neumorphic_frame(main_frame)
    status_frame.pack(fill=tk.X, pady=10)
    
    status_var = tk.StringVar(value="就绪 - 请选择音频文件")
    status_label = tk.Label(
        status_frame,
        textvariable=status_var,
        font=("微软雅黑", 10),
        bg=NeumorphismStyle.BG_COLOR,
        fg=NeumorphismStyle.TEXT_COLOR
    )
    status_label.pack(pady=10)
    
    # 进度条
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(
        status_frame,
        variable=progress_var,
        maximum=100,
        length=400
    )
    progress_bar.pack(pady=5)
    
    # 处理结果
    result_var = tk.StringVar(value="")
    result_label = tk.Label(
        status_frame,
        textvariable=result_var,
        font=("微软雅黑", 10),
        bg=NeumorphismStyle.BG_COLOR,
        fg="#00b894"
    )
    result_label.pack(pady=5)
    
    # 按钮框架
    button_frame = NeumorphismStyle.create_neumorphic_frame(main_frame)
    button_frame.pack(fill=tk.X, pady=10)
    
    # 处理单个文件
    def process_single_file(file_path, config):
        """处理单个音频文件"""
        try:
            print(f"🎧 正在处理: {os.path.basename(file_path)}")
            status_var.set(f"处理中: {os.path.basename(file_path)}")
            root.update()
            
            # 获取文件所在目录
            file_dir = os.path.dirname(file_path)
            output_dir = os.path.join(file_dir, CONFIG['output_folder'])
            
            # 创建输出文件夹
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 加载音频
            original_audio = AudioSegment.from_file(file_path)
            
            # 核心处理 A: 制作静默阈下音频
            silent_audio = process_silent_subliminal(original_audio, config['carrier_freq'])
            # 调整人声音量
            silent_audio = silent_audio + config['voice_volume_db']

            # 核心处理 B: 制作双耳节拍
            # 生成与原音频等长的双耳节拍
            duration_ms = len(original_audio)
            binaural_beat = generate_binaural_beat(
                duration_ms, 
                config['binaural_left_freq'], 
                config['binaural_right_freq'],
                config['binaural_volume_db']
            )

            # 核心处理 C: 混合
            # 确保两者长度一致
            if len(silent_audio) > len(binaural_beat):
                silent_audio = silent_audio[:len(binaural_beat)]
            else:
                binaural_beat = binaural_beat[:len(silent_audio)]

            # 叠加
            final_mix = silent_audio.overlay(binaural_beat)

            # 导出
            output_filename = f"Subliminal_{os.path.splitext(os.path.basename(file_path))[0]}.wav"
            output_path = os.path.join(output_dir, output_filename)
            
            # 导出为 WAV
            final_mix.export(output_path, format="wav")
            
            print(f"✅ 完成! 已保存至: {output_filename}")
            return True
        except Exception as e:
            print(f"❌ 处理 {os.path.basename(file_path)} 时出错: {e}")
            return False
    
    # 开始处理按钮
    def start_processing():
        """开始处理选中的文件"""
        if not selected_files:
            show_message("提示", "请先选择音频文件或文件夹！", "warning")
            return
        
        # 更新状态
        status_var.set("正在处理...")
        result_var.set("")
        progress_var.set(0)
        root.update()
        
        # 获取用户输入的配置
        user_config = {
            'carrier_freq': carrier_var.get(),
            'binaural_left_freq': left_freq_var.get(),
            'binaural_right_freq': right_freq_var.get(),
            'binaural_volume_db': binaural_vol_var.get(),
            'voice_volume_db': voice_vol_var.get(),
            'output_folder': CONFIG['output_folder']
        }
        
        # 处理文件
        success_count = 0
        total_files = len(selected_files)
        
        for i, file_path in enumerate(selected_files):
            if process_single_file(file_path, user_config):
                success_count += 1
            
            # 更新进度
            progress = (i + 1) / total_files * 100
            progress_var.set(progress)
            root.update()
        
        # 更新结果
        result_var.set(f"处理完成: {success_count}/{total_files} 个文件成功")
        status_var.set("处理完成")
        
        # 显示成功消息
        show_message(
            "成功",
            f"处理完成!\n{success_count}/{total_files} 个文件成功处理\n\n输出目录: 各文件所在位置的'已处理'文件夹",
            "info"
        )
    
    start_button = NeumorphismStyle.create_neumorphic_button(
        button_frame,
        text="🎵 开始处理",
        command=start_processing
    )
    start_button.pack(side=tk.LEFT, padx=10)
    
    # 退出按钮
    def exit_app():
        root.destroy()
    
    exit_button = NeumorphismStyle.create_neumorphic_button(
        button_frame,
        text="退出",
        command=exit_app
    )
    exit_button.pack(side=tk.RIGHT, padx=10)
    
    # 显示窗口
    root.mainloop()
    
    # 返回默认配置（GUI模式下直接在界面中处理）
    return CONFIG

def get_user_inputs_cli():
    """
    命令行模式下获取用户输入参数
    
    返回:
        dict: 用户调整后的配置参数
    """
    print("\n" + "="*60)
    print("参数配置")
    print("="*60)
    print("按回车键使用默认值，或输入新值")
    print("\n")
    
    # 复制默认配置
    user_config = CONFIG.copy()
    
    # 获取载波频率
    try:
        input_val = input(f"载波频率 (Hz) [{CONFIG['carrier_freq']}]: ")
        if input_val.strip():
            user_config['carrier_freq'] = float(input_val)
    except ValueError:
        print("输入无效，使用默认值")
    
    # 获取左声道频率
    try:
        input_val = input(f"左耳频率 (Hz) [{CONFIG['binaural_left_freq']}]: ")
        if input_val.strip():
            user_config['binaural_left_freq'] = float(input_val)
    except ValueError:
        print("输入无效，使用默认值")
    
    # 获取右声道频率
    try:
        input_val = input(f"右耳频率 (Hz) [{CONFIG['binaural_right_freq']}]: ")
        if input_val.strip():
            user_config['binaural_right_freq'] = float(input_val)
    except ValueError:
        print("输入无效，使用默认值")
    
    # 获取双耳节拍音量
    try:
        input_val = input(f"双耳节拍音量 (dB) [{CONFIG['binaural_volume_db']}]: ")
        if input_val.strip():
            user_config['binaural_volume_db'] = float(input_val)
    except ValueError:
        print("输入无效，使用默认值")
    
    # 获取人声音量
    try:
        input_val = input(f"人声音量 (dB) [{CONFIG['voice_volume_db']}]: ")
        if input_val.strip():
            user_config['voice_volume_db'] = float(input_val)
    except ValueError:
        print("输入无效，使用默认值")
    
    print("\n" + "="*60)
    return user_config

# --- 第五步：音频处理函数 ---

def process_audio_files(config, progress_var=None, status_var=None):
    """
    处理音频文件
    
    参数:
        config: 配置参数
        progress_var: 进度条变量（GUI模式）
        status_var: 状态变量（GUI模式）
    
    返回:
        tuple: (成功处理的文件数, 总文件数)
    """
    # 1. 获取当前路径
    current_dir = os.getcwd()
    output_dir = os.path.join(current_dir, config['output_folder'])

    # 2. 创建输出文件夹
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出文件夹: {config['output_folder']}")
        if status_var:
            status_var.set(f"创建输出文件夹: {config['output_folder']}")

    # 3. 扫描文件
    files = [f for f in os.listdir(current_dir) if f.lower().endswith(CONFIG['supported_extensions'])]
    
    if not files:
        error_msg = "当前文件夹下没有找到音频文件 (.mp3, .wav 等)。"
        print("❌ " + error_msg)
        if status_var:
            status_var.set(error_msg)
        if GUI_AVAILABLE:
            show_message("错误", error_msg, "error")
        return 0, 0

    print(f"📂 发现 {len(files)} 个音频文件，准备开始处理...\n")
    if status_var:
        status_var.set(f"发现 {len(files)} 个音频文件")

    # 4. 循环处理
    success_count = 0
    total_files = len(files)
    
    for i, filename in enumerate(files):
        try:
            print(f"🎧 正在处理: {filename}")
            if status_var:
                status_var.set(f"处理中: {filename}")
            
            start_time = time.time()
            
            # --- 加载音频 ---
            file_path = os.path.join(current_dir, filename)
            original_audio = AudioSegment.from_file(file_path)
            
            # --- 核心处理 A: 制作静默阈下音频 ---
            silent_audio = process_silent_subliminal(original_audio, config['carrier_freq'])
            # 调整人声音量
            silent_audio = silent_audio + config['voice_volume_db']

            # --- 核心处理 B: 制作双耳节拍 ---
            # 生成与原音频等长的双耳节拍
            duration_ms = len(original_audio)
            binaural_beat = generate_binaural_beat(
                duration_ms, 
                config['binaural_left_freq'], 
                config['binaural_right_freq'],
                config['binaural_volume_db']
            )

            # --- 核心处理 C: 混合 --- 确保两者长度一致 (通常是一致的，但为了安全)
            if len(silent_audio) > len(binaural_beat):
                silent_audio = silent_audio[:len(binaural_beat)]
            else:
                binaural_beat = binaural_beat[:len(silent_audio)]

            # 叠加 (Overlay)
            final_mix = silent_audio.overlay(binaural_beat)

            # --- 导出 ---
            output_filename = f"Subliminal_{filename.split('.')[0]}.wav" # 推荐输出wav保证无损质量
            output_path = os.path.join(output_dir, output_filename)
            
            # 导出为 WAV (最高质量，避免MP3压缩损失高频信息)
            final_mix.export(output_path, format="wav")
            
            elapsed = time.time() - start_time
            print(f"✅ 完成! 已保存至: {output_filename} (耗时: {elapsed:.2f}秒)\n")
            success_count += 1
            
            # 更新进度
            if progress_var:
                progress = (i + 1) / total_files * 100
                progress_var.set(progress)
                
        except Exception as e:
            print(f"❌ 处理 {filename} 时出错: {e}")
            # 如果是 ffmpeg 错误，给出提示
            if "ffmpeg" in str(e).lower():
                print("   (提示: 请检查系统是否安装了 FFmpeg 并配置了环境变量)")
            
            # 更新进度
            if progress_var:
                progress = (i + 1) / total_files * 100
                progress_var.set(progress)

    return success_count, total_files

# --- 第六步：主程序 (Main Execution) ---

def main():
    """
    主程序入口
    """
    print("="*60)
    print(" 🚀 达丹科技 - 潜意识音频生成器 启动")
    print("="*60)
    print("正在检查系统环境...")

    # 根据GUI可用性选择运行模式
    if GUI_AVAILABLE:
        print("检测到GUI环境，启动可视化界面...")
        get_user_inputs_gui()
    else:
        print("未检测到GUI环境，启动命令行模式...")
        user_config = get_user_inputs_cli()
        success_count, total_files = process_audio_files(user_config)
        
        print("="*60)
        print(f"🎉 全部完成! 成功处理 {success_count}/{total_files} 个文件。")
        print(f"📁 输出目录: {CONFIG['output_folder']}")
        print("="*60)
        input("按回车键结束...")

if __name__ == "__main__":
    main()

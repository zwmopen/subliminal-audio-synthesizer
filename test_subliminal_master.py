# -*- coding: utf-8 -*-
"""
Subliminal Master 功能测试脚本
直接测试核心音频处理功能
"""

import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subliminal_master import (
    generate_binaural_beat,
    process_silent_subliminal,
    normalize_audio,
    loop_audio,
    mix_subliminal_audio,
    CONFIG
)
from pydub import AudioSegment

def test_binaural_beat_generation():
    """测试双耳搏动生成"""
    print("\n" + "="*60)
    print("测试1: 双耳搏动生成")
    print("="*60)
    
    try:
        # 生成5秒的双耳搏动
        beat = generate_binaural_beat(
            duration_ms=5000,
            left_freq=430,
            right_freq=434,
            volume_db=-15
        )
        
        print(f"✅ 双耳搏动生成成功")
        print(f"   时长: {len(beat)/1000}秒")
        print(f"   声道: {beat.channels}")
        print(f"   采样率: {beat.frame_rate}Hz")
        return True
    except Exception as e:
        print(f"❌ 双耳搏动生成失败: {e}")
        return False

def test_silent_subliminal_processing():
    """测试高频调制处理"""
    print("\n" + "="*60)
    print("测试2: 高频调制处理")
    print("="*60)
    
    try:
        # 加载测试音频
        test_audio_path = os.path.join("test_audio", "affirmation_test.wav")
        if not os.path.exists(test_audio_path):
            print(f"❌ 测试音频不存在: {test_audio_path}")
            return False
        
        audio = AudioSegment.from_wav(test_audio_path)
        print(f"   原始音频时长: {len(audio)/1000}秒")
        
        # 处理音频
        processed = process_silent_subliminal(audio, carrier_freq=17500)
        
        print(f"✅ 高频调制处理成功")
        print(f"   处理后时长: {len(processed)/1000}秒")
        print(f"   声道: {processed.channels}")
        print(f"   采样率: {processed.frame_rate}Hz")
        return True
    except Exception as e:
        print(f"❌ 高频调制处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_normalize_audio():
    """测试音频标准化"""
    print("\n" + "="*60)
    print("测试3: 音频标准化")
    print("="*60)
    
    try:
        # 创建一个简单的音频
        audio = AudioSegment.silent(duration=1000)  # 1秒静音
        
        # 标准化
        normalized = normalize_audio(audio, target_db=-20)
        
        print(f"✅ 音频标准化成功")
        print(f"   目标dB: -20")
        print(f"   实际dBFS: {normalized.dBFS:.2f}")
        return True
    except Exception as e:
        print(f"❌ 音频标准化失败: {e}")
        return False

def test_loop_audio():
    """测试音频循环"""
    print("\n" + "="*60)
    print("测试4: 音频循环")
    print("="*60)
    
    try:
        # 创建一个2秒的音频
        audio = AudioSegment.silent(duration=2000)
        
        # 循环到5秒
        looped = loop_audio(audio, target_duration_ms=5000)
        
        print(f"✅ 音频循环成功")
        print(f"   原始时长: {len(audio)/1000}秒")
        print(f"   目标时长: 5秒")
        print(f"   实际时长: {len(looped)/1000}秒")
        
        if len(looped) == 5000:
            print("   ✅ 时长精确匹配")
            return True
        else:
            print(f"   ⚠️ 时长不匹配: {len(looped)}ms")
            return False
    except Exception as e:
        print(f"❌ 音频循环失败: {e}")
        return False

def test_full_mix():
    """测试完整混音流程"""
    print("\n" + "="*60)
    print("测试5: 完整混音流程")
    print("="*60)
    
    try:
        affirmation_path = os.path.join("test_audio", "affirmation_test.wav")
        background_path = os.path.join("test_audio", "background_test.wav")
        
        if not os.path.exists(affirmation_path):
            print(f"❌ 肯定句音频不存在: {affirmation_path}")
            return False
        if not os.path.exists(background_path):
            print(f"❌ 背景音乐不存在: {background_path}")
            return False
        
        config = {
            'carrier_freq': 17500,
            'subliminal_volume_db': -23,
            'background_volume_db': 0,
            'enable_binaural': True,
            'binaural_left_freq': 430,
            'binaural_right_freq': 434,
            'binaural_volume_db': -15
        }
        
        print("开始混音处理...")
        success, result = mix_subliminal_audio(affirmation_path, background_path, config)
        
        if success:
            print(f"\n✅ 完整混音成功")
            print(f"   输出文件: {result}")
            print(f"   文件大小: {os.path.getsize(result)/1024:.2f}KB")
            
            # 验证输出文件
            output_audio = AudioSegment.from_wav(result)
            print(f"   时长: {len(output_audio)/1000}秒")
            print(f"   声道: {output_audio.channels}")
            print(f"   采样率: {output_audio.frame_rate}Hz")
            return True
        else:
            print(f"❌ 完整混音失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 完整混音测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Subliminal Master 功能测试")
    print("="*60)
    
    tests = [
        ("双耳搏动生成", test_binaural_beat_generation),
        ("高频调制处理", test_silent_subliminal_processing),
        ("音频标准化", test_normalize_audio),
        ("音频循环", test_loop_audio),
        ("完整混音流程", test_full_mix)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 执行出错: {e}")
            results.append((name, False))
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    run_all_tests()

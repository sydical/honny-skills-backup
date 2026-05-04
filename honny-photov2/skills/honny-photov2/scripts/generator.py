#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import requests
from datetime import datetime

# 配置
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_ID = os.environ.get('WORKFLOW_ID', '2047002838944980993')
MEMORY_DIR = os.path.expanduser('~/data/disk/workspace/memory')
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '5'))
RETRY_DELAY_MS = int(os.environ.get('RETRY_DELAY_MS', '30000'))

class HonnyPhotoV2:
    """Honny Photo V2 生成器"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.runninghub.cn"
        self.run_url = f"{self.base_url}/openapi/v2/run/ai-app/{WORKFLOW_ID}"
        self.query_url = f"{self.base_url}/openapi/v2/query"
        self.upload_url = f"{self.base_url}/openapi/v2/media/upload/binary"
        
    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def get_today_memory_file(self):
        """获取当天记忆文件"""
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(MEMORY_DIR, f"{today}.md")
    
    def get_reference_from_memory(self):
        """从记忆获取参考图 URL"""
        memory_file = self.get_today_memory_file()
        if not os.path.exists(memory_file):
            return None
        
        with open(memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找参考图 URL
        for line in content.split('\n'):
            if 'honny_reference_image' in line or '参考图' in line:
                # 提取 URL
                parts = line.split('http')
                if len(parts) > 1:
                    return 'http' + parts[1].split()[0]
        return None
    
    def save_reference_to_memory(self, url):
        """保存参考图 URL 到记忆"""
        memory_file = self.get_today_memory_file()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 读取现有内容或创建新文件
        existing_content = ""
        if os.path.exists(memory_file):
            with open(memory_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # 添加参考图记录
        new_content = f"\n## Honny Photo\n- 参考图URL: {url}\n"
        
        with open(memory_file, 'w', encoding='utf-8') as f:
            f.write(existing_content + new_content)
        
        print(f"✅ 参考图 URL 已保存到记忆")
    
    def upload_image(self, image_path):
        """上传图片到 RunningHub (v2 media upload API)"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        print(f"📤 正在上传参考图: {image_path}")
        
        # 获取文件名
        filename = os.path.basename(image_path)
        
        with open(image_path, 'rb') as f:
            files = {'file': (filename, f, 'image/png')}
            headers = {'Authorization': f"Bearer {self.api_key}"}
            response = requests.post(self.upload_url, files=files, headers=headers, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                # v2 API 返回 download_url
                file_url = result['data'].get('url') or result['data'].get('download_url')
                print(f"✅ 参考图上传成功: {file_url}")
                print(f"⏰ URL 有效期: 24小时")
                return file_url
            else:
                raise Exception(f"上传失败: {result.get('errorMessage')}")
        else:
            raise Exception(f"上传请求失败: {response.status_code}, {response.text}")
    
    def find_avatar(self, user_dir):
        """查找用户目录下的 avatar 图片"""
        avatar_names = ['avatar.jpg', 'avatar.png', 'avatar.jpeg', 
                       'avatar.gif', '头像.jpg', '头像.png', 'photo.jpg', 'photo.png']
        
        # 常见图片文件
        common_images = ['photo.jpg', 'photo.png', 'photo.jpeg', 'img.jpg', 'img.png',
                       'photo_1.jpg', 'photo_1.png', 'p1.jpg', 'p1.png']
        
        # 首先检查指定的 avatar 名称
        for name in avatar_names:
            path = os.path.join(user_dir, name)
            if os.path.exists(path):
                return path
        
        # 扫描所有图片文件
        try:
            for f in os.listdir(user_dir):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    path = os.path.join(user_dir, f)
                    if os.path.isfile(path) and os.path.getsize(path) > 10000:  # 大于 10KB
                        return path
        except:
            pass
        
        return None
    
    def generate_image(self, reference_url, prompt, width=720, height=1280):
        """生成图片"""
        print(f"🎨 正在生成图片...")
        print(f"📝 提示词: {prompt}")
        
        payload = {
            "nodeInfoList": [
                {
                    "nodeId": "1",
                    "fieldName": "image",
                    "fieldValue": reference_url,
                    "description": "参考图"
                },
                {
                    "nodeId": "8", 
                    "fieldName": "text",
                    "fieldValue": prompt,
                    "description": "提示词"
                },
                {
                    "nodeId": "13",
                    "fieldName": "width",
                    "fieldValue": str(width),
                    "description": "图片宽度"
                },
                {
                    "nodeId": "13",
                    "fieldName": "height", 
                    "fieldValue": str(height),
                    "description": "图片高度"
                }
            ],
            "instanceType": "default",
            "usePersonalQueue": "false"
        }
        
        # 提交任务（带重试机制）
        for attempt in range(MAX_RETRIES):
            response = requests.post(
                self.run_url, 
                headers=self.get_headers(), 
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"请求失败: {response.status_code}")
            
            result = response.json()
            
            # 检查队列是否满 (code 429)
            if result.get('code') == 429:
                wait_seconds = RETRY_DELAY_MS / 1000
                print(f"⏳ 队列已满，{wait_seconds}秒后重试 ({attempt + 1}/{MAX_RETRIES})...")
                time.sleep(RETRY_DELAY_MS / 1000)
                continue
            
            if result.get('code') != 0:
                raise Exception(f"API错误: {result.get('message')}")
            
            # 成功
            break
        
        if result.get('code') == 429:
            raise Exception(f"队列已满，重试{MAX_RETRIES}次后仍失败")
        
        task_id = result['data']['taskId']
        print(f"📋 任务ID: {task_id}")
        
        # 轮询结果
        return self.wait_for_result(task_id)
    
    def wait_for_result(self, task_id, max_wait=300):
        """等待任务完成"""
        print("⏳ 等待生成...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.post(
                self.query_url,
                headers=self.get_headers(),
                data=json.dumps({"taskId": task_id}),
                timeout=30
            )
            
            if response.status_code != 200:
                time.sleep(5)
                continue
            
            result = response.json()
            status = result['data']['status']
            
            if status == "SUCCESS":
                elapsed = time.time() - start_time
                print(f"✅ 生成完成！耗时: {elapsed:.1f}秒")
                
                outputs = result['data'].get('outputs', [])
                if outputs and len(outputs) > 0:
                    return outputs[0].get('url')
                return None
            
            elif status == "FAILED":
                error = result['data'].get('errorMessage', '未知错误')
                raise Exception(f"生成失败: {error}")
            
            else:
                print(f"⏳ 状态: {status}...")
                time.sleep(5)
        
        raise Exception("等待超时")
    
    def optimize_prompt(self, original_prompt, feedback=None):
        """优化提示词"""
        # 基于反馈优化
        if feedback:
            # 简单的优化逻辑
            optimizations = []
            
            if "不够" in feedback or "少" in feedback:
                optimizations.append("细节丰富")
            if "模糊" in feedback:
                optimizations.append("高清细节")
            if "丑" in feedback or "难看" in feedback:
                optimizations.append("美丽精致")
            if "不像" in feedback:
                optimizations.append("高度相似")
                
            if optimizations:
                return original_prompt + "，" + "，".join(optimizations)
        
        # 默认优化：添加质量词
        quality_words = "完美构图，超级高清，杰作，顶级画质"
        if quality_words not in original_prompt:
            return original_prompt + "，" + quality_words
        
        return original_prompt
    
    def run(self, prompt, user_dir=None, optimize=True, iteration=1):
        """运行完整流程"""
        
        # 1. 检查/获取参考图
        reference_url = self.get_reference_from_memory()
        
        if not reference_url:
            print("📷 首次使用，需要上传参考图...")
            
            # 查找用户目录
            if user_dir is None:
                user_dir = os.path.expanduser("~")
            
            # 查找 avatar
            avatar_path = self.find_avatar(user_dir)
            
            if avatar_path:
                reference_url = self.upload_image(avatar_path)
                self.save_reference_to_memory(reference_url)
            else:
                # 使用默认/示例参考图
                print("⚠️ 未找到参考图，使用默认设置")
                reference_url = ""
        
        # 2. 优化提示词
        current_prompt = prompt
        if optimize and iteration > 0:
            current_prompt = self.optimize_prompt(prompt)
        
        # 3. 生成图片
        image_url = self.generate_image(reference_url, current_prompt)
        
        return {
            "image_url": image_url,
            "prompt": current_prompt,
            "reference_url": reference_url,
            "iteration": iteration
        }


def main():
    """测试"""
    api_key = os.environ.get('RUNNINGHUB_API_KEY')
    if not api_key:
        print("❌ 请设置 RUNNINGHUB_API_KEY 环境变量")
        sys.exit(1)
    
    generator = HonnyPhotoV2(api_key)
    
    # 测试生成
    prompt = "美丽的小女生照片"
    result = generator.run(prompt)
    
    print(f"\n🎉 生成成功!")
    print(f"🖼️ 图片: {result['image_url']}")
    print(f"📝 提示词: {result['prompt']}")


if __name__ == '__main__':
    main()

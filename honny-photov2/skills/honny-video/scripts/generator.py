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
WORKFLOW_ID = os.environ.get('WORKFLOW_ID', '2016727774387511297')
MEMORY_DIR = os.path.expanduser('~/data/disk/workspace/memory')
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '5'))
RETRY_DELAY_MS = int(os.environ.get('RETRY_DELAY_MS', '60000'))


class HonnyVideo:
    """Honny Video 生成器 - 图生视频"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.runninghub.cn"
        self.run_url = f"{self.base_url}/openapi/v2/run/ai-app/{WORKFLOW_ID}"
        self.query_url = f"{self.base_url}/openapi/v2/query"
        
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
            if '参考图URL' in line:
                parts = line.split('http')
                if len(parts) > 1:
                    return 'http' + parts[1].split()[0]
        return None
    
    def submit_task(self, image_url, prompt):
        """提交图生视频任务"""
        print(f"🎬 正在提交视频生成任务...")
        print(f"📷 图片: {image_url[:60]}...")
        print(f"📝 提示词: {prompt}")
        
        payload = {
            "nodeInfoList": [
                {
                    "nodeId": "106",
                    "fieldName": "image",
                    "fieldValue": image_url,
                    "description": "传图"
                },
                {
                    "nodeId": "6",
                    "fieldName": "text",
                    "fieldValue": prompt,
                    "description": "言出法随"
                }
            ],
            "instanceType": "default",
            "usePersonalQueue": "false"
        }
        
        # 带重试机制
        for attempt in range(MAX_RETRIES):
            response = requests.post(
                self.run_url, 
                headers=self.get_headers(), 
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ 请求失败: {response.status_code}")
                time.sleep(RETRY_DELAY_MS / 1000)
                continue
            
            result = response.json()
            
            # 检查队列是否满 (errorCode 421)
            if result.get('errorCode') == '421':
                wait_seconds = RETRY_DELAY_MS / 1000
                print(f"⏳ 队列已满，{wait_seconds}秒后重试 ({attempt + 1}/{MAX_RETRIES})...")
                time.sleep(RETRY_DELAY_MS / 1000)
                continue
            
            if result.get('errorCode'):
                print(f"❌ API错误: {result.get('errorMessage')}")
                return None
            
            if result.get('taskId'):
                task_id = result['taskId']
                print(f"✅ 任务ID: {task_id}")
                return task_id
        
        print(f"❌ 提交失败，已重试{MAX_RETRIES}次")
        return None
    
    def wait_for_result(self, task_id, max_wait=600):
        """等待视频生成完成"""
        print("⏳ 等待生成中...")
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
            
            # 检查是否有 data 字段
            if 'data' not in result:
                time.sleep(5)
                continue
            
            status = result['data'].get('status')
            print(f"⏳ 状态: {status}...")
            
            if status == "SUCCESS":
                elapsed = time.time() - start_time
                print(f"✅ 生成完成！耗时: {elapsed:.1f}秒")
                
                outputs = result['data'].get('outputs', [])
                if outputs and len(outputs) > 0:
                    return outputs[0].get('url')
                return None
            
            elif status == "FAILED":
                error = result['data'].get('errorMessage', '未知错误')
                print(f"❌ 生成失败: {error}")
                return None
            
            else:
                time.sleep(5)
        
        print("⏰ 等待超时")
        return None
    
    def generate(self, image_url, prompt):
        """生成视频"""
        # 1. 提交任务
        task_id = self.submit_task(image_url, prompt)
        if not task_id:
            return None
        
        # 2. 等待结果
        video_url = self.wait_for_result(task_id)
        
        return {
            "video_url": video_url,
            "prompt": prompt,
            "task_id": task_id
        }


def main():
    """测试"""
    api_key = os.environ.get('RUNNINGHUB_API_KEY')
    if not api_key:
        print("❌ 请设置 RUNNINGHUB_API_KEY 环境变量")
        sys.exit(1)
    
    generator = HonnyVideo(api_key)
    
    # 测试生成
    prompt = "一个女孩在玩耍"
    image_url = "test_image_url.png"
    
    result = generator.generate(image_url, prompt)
    
    if result and result.get('video_url'):
        print(f"\n🎉 生成成功!")
        print(f"🎥 视频: {result['video_url']}")
    else:
        print("\n❌ 生成失败")


if __name__ == '__main__':
    main()

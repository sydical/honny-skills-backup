#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Honny Wan Video 图生视频生成器 - 支持分镜脚本
- 每个任务独立 List-{task_id}.md 文件
- 每60秒自动查询任务进度
"""

import os
import sys
import json
import time
import glob
import requests
from datetime import datetime

# 配置
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_ID = os.environ.get('RUNNINGHUB_VIDEO_WORKFLOW_ID', '2048133528671490050')
OUTPUT_DIR = os.path.expanduser('~/.openclaw/workspace-companion2/data/videos')


class WanVideoGenerator:
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

    def upload_image(self, image_path):
        """上传参考图，返回 download_url"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")

        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/png')}
            headers = {'Authorization': f"Bearer {self.api_key}"}
            response = requests.post(self.upload_url, files=files, headers=headers, timeout=120)

        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                return result['data'].get('url') or result['data'].get('download_url', '')
        raise Exception(f"上传失败: {response.status_code} {response.text}")

    def submit_task(self, reference_url, prompt, duration=8):
        """提交视频生成任务"""
        payload = {
            "nodeInfoList": [
                {"nodeId": "13", "fieldName": "image", "fieldValue": reference_url},
                {"nodeId": "36", "fieldName": "text", "fieldValue": prompt},
                {"nodeId": "15", "fieldName": "value", "fieldValue": str(duration)}
            ],
            "instanceType": "default",
            "usePersonalQueue": "false"
        }

        for attempt in range(3):
            response = requests.post(self.run_url, headers=self.get_headers(),
                                   data=json.dumps(payload), timeout=30)
            result = response.json()

            if result.get('errorCode') == '421':
                print(f"⏳ 队列已满，10秒后重试 ({attempt + 1}/3)...")
                time.sleep(10)
                continue

            if result.get('errorCode') not in (0, None) and not result.get('taskId'):
                raise Exception(f"提交失败: {result.get('errorMessage')}")

            task_id = result.get('taskId') or result.get('data', {}).get('taskId', '')
            if not task_id:
                raise Exception(f"无taskId: {result}")
            return task_id

        raise Exception("视频生成失败，队列满")

    def query_task(self, task_id):
        """查询任务状态"""
        response = requests.post(self.query_url, headers=self.get_headers(),
                                data=json.dumps({'taskId': task_id}), timeout=30)
        return response.json()

    # ========== List-{task_id}.md 管理 ==========

    def create_task_file(self, task_id, prompt, duration, ref_url):
        """创建 List-{task_id}.md"""
        filepath = os.path.join(SKILL_DIR, f'List-{task_id}.md')
        content = f"""# 视频任务队列

## 基本信息
- task_id: {task_id}
- status: QUEUED
- submitted_at: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- duration: {duration}s
- reference_url: {ref_url[:80]}...

## 分镜提示词
{prompt}

## 结果
- video_url: (待生成)
- coins: (待消耗)
- elapsed: (待计算)
- completed_at: (待完成)
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def update_task_file(self, task_id, status=None, video_url=None,
                        coins=None, elapsed=None, error=None):
        """更新 List-{task_id}.md"""
        filepath = os.path.join(SKILL_DIR, f'List-{task_id}.md')
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if status:
            content = content.replace(f'status: QUEUED', f'status: {status}')
            content = content.replace(f'status: RUNNING', f'status: {status}')

        if video_url:
            content = content.replace('- video_url: (待生成)', f'- video_url: {video_url}')
        if coins:
            content = content.replace('- coins: (待消耗)', f'- coins: {coins}')
        if elapsed:
            content = content.replace('- elapsed: (待计算)', f'- elapsed: {elapsed}s')
        if error:
            content = content.replace('- video_url: (待生成)', f'- error: {error}\n- video_url: (失败)')
        if status == 'SUCCESS':
            content = content.replace('- completed_at: (待完成)',
                                      f'- completed_at: {datetime.now().strftime("%Y-%m-%d %H:%M")}')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def list_all_task_files(self):
        """列出所有 List-*.md 文件"""
        pattern = os.path.join(SKILL_DIR, 'List-*.md')
        return sorted(glob.glob(pattern))

    def load_task_from_file(self, filepath):
        """从文件读取任务信息"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        task_id = None
        status = None
        for line in content.split('\n'):
            if line.startswith('- task_id:'):
                task_id = line.split(':', 1)[1].strip()
            elif line.startswith('- status:'):
                status = line.split(':', 1)[1].strip()
        return task_id, status

    def poll_all_active(self):
        """轮询所有待完成任务的进度"""
        task_files = self.list_all_task_files()
        if not task_files:
            print("📋 暂无待完成的任务")
            return

        active = []
        for filepath in task_files:
            tid, status = self.load_task_from_file(filepath)
            if status in ('QUEUED', 'RUNNING'):
                active.append((tid, filepath))

        if not active:
            print("📋 所有任务已完成")
            return

        print(f"🔄 检查 {len(active)} 个待完成任务...")
        for task_id, filepath in active:
            result = self.query_task(task_id)
            data = result.get('data', result)
            status = data.get('status', 'UNKNOWN')

            if status == 'SUCCESS':
                elapsed = data.get('usage', {}).get('taskCostTime', '')
                coins = data.get('usage', {}).get('consumeCoins', '')
                outputs = data.get('outputs', [])
                url = ''
                if outputs:
                    url = outputs[0].get('url') or outputs[0].get('fieldValue', '')
                self.update_task_file(task_id, status='SUCCESS', video_url=url,
                                    coins=coins, elapsed=elapsed)
                print(f"  ✅ {task_id[:20]}... 完成，消耗 {coins} 积分")

            elif status == 'FAILED':
                error = data.get('errorMessage', '未知错误')
                self.update_task_file(task_id, status='FAILED', error=error)
                print(f"  ❌ {task_id[:20]}... 失败: {error}")

            elif status in ('QUEUED', 'RUNNING'):
                print(f"  ⏳ {task_id[:20]}... {status}")
                # 首次查询到非QUEUED时更新为RUNNING
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if 'status: QUEUED' in content and status == 'RUNNING':
                    self.update_task_file(task_id, status='RUNNING')

    def run(self, reference_url, prompt, duration=8, poll_interval=60):
        """运行完整流程"""

        # 1. 提交任务
        print(f"📤 提交任务...")
        task_id = self.submit_task(reference_url, prompt, duration)
        print(f"✅ 任务已提交: {task_id}")

        # 2. 创建 List-{task_id}.md
        self.create_task_file(task_id, prompt, duration, reference_url)
        print(f"📋 已创建 List-{task_id}.md")

        # 3. 立即开始轮询
        print(f"⏳ 等待任务执行...")
        start_time = time.time()
        while True:
            result = self.query_task(task_id)
            data = result.get('data', result)
            status = data.get('status', 'UNKNOWN')

            if status == 'SUCCESS':
                elapsed = time.time() - start_time
                coins = data.get('usage', {}).get('consumeCoins', '')
                outputs = data.get('outputs', [])
                url = outputs[0].get('url') or outputs[0].get('fieldValue', '') if outputs else ''
                self.update_task_file(task_id, status='SUCCESS', video_url=url,
                                    coins=coins, elapsed=f'{elapsed:.1f}')
                print(f"✅ 生成完成！耗时: {elapsed:.1f}秒，消耗 {coins} 积分")
                print(f"🎞️ 视频: {url}")
                return {'task_id': task_id, 'url': url, 'coins': coins, 'elapsed': elapsed}

            elif status == 'FAILED':
                error = data.get('errorMessage', '未知错误')
                self.update_task_file(task_id, status='FAILED', error=error)
                raise Exception(f"生成失败: {error}")

            elif status == 'RUNNING' and poll_interval < 60:
                # 初始阶段频繁查询
                print(f"⏳ 状态: {status}...")
                time.sleep(poll_interval)
            else:
                print(f"⏳ 状态: {status}，60秒后再查...")
                self.update_task_file(task_id, status=status)
                time.sleep(poll_interval)


def main():
    """命令行入口"""
    api_key = os.environ.get('RUNNINGHUB_API_KEY')
    if not api_key:
        workspace_env = os.path.expanduser("~/.openclaw/workspace-companion2/.env")
        if os.path.exists(workspace_env):
            with open(workspace_env) as f:
                for line in f:
                    if line.startswith('RUNNINGHUB_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break

    if not api_key:
        print("❌ 请设置 RUNNINGHUB_API_KEY 环境变量")
        sys.exit(1)

    generator = WanVideoGenerator(api_key)

    if '--watch-all' in sys.argv:
        print("🔄 开始监控所有视频任务（每60秒查询一次，Ctrl+C 退出）...")
        while True:
            generator.poll_all_active()
            print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 等待60秒...\n")
            time.sleep(60)
        return

    if len(sys.argv) < 3:
        print("用法: python3 wan_video.py <参考图路径> <分镜提示词> [时长秒数] [输出目录]")
        print("       python3 wan_video.py --watch-all  # 监控所有任务")
        print("示例: python3 wan_video.py ./photo.jpg '0-2s: 镜头推进...' 8 ./output/")
        sys.exit(1)

    ref_path = sys.argv[1]
    prompt = sys.argv[2]
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    output_dir = sys.argv[4] if len(sys.argv) > 4 else OUTPUT_DIR

    if not os.path.exists(ref_path):
        print(f"❌ 参考图不存在: {ref_path}")
        sys.exit(1)

    # 上传参考图
    print(f"📤 上传参考图: {ref_path}")
    ref_url = generator.upload_image(ref_path)
    print(f"✅ 参考图已上传: {ref_url[:60]}...")

    # 生成视频
    result = generator.run(ref_url, prompt, duration)
    print(f"\n🎉 生成成功!")
    print(f"🎞️ 视频: {result['url']}")
    print(f"⏱️ 耗时: {result['elapsed']:.1f}秒")
    print(f"💰 消耗: {result['coins']} 积分")


if __name__ == '__main__':
    main()

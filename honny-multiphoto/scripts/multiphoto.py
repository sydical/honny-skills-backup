#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Honny Multi-Photo 批量生成器 - 一致性模特同场景不同表情/动作4图生成
- 自动管理任务队列 List.md
- 每60秒自动查询待完成任务状态
- 任务间隔5分钟，避免API并发限制
- 只需提供模特参考图，自动生成同场景不同表情/动作的4图
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# 配置
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
LIST_FILE = os.path.join(SKILL_DIR, 'List.md')
WORKFLOW_ID = '2050987699099713538'
OUTPUT_DIR = os.path.expanduser('~/.openclaw/workspace-companion2/data/images/multiphoto')
TASK_INTERVAL = 300  # 5分钟任务间隔


class MultiPhotoGenerator:
    """一致性模特同场景多图生成器 - 只需提供模特参考图即可生成4图"""
    
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

    def submit_task(self, reference_url):
        """提交生成任务（仅需参考图）"""
        payload = {
            "nodeInfoList": [
                {"nodeId": "42", "fieldName": "image", "fieldValue": reference_url, "description": "模特图"}
            ],
            "instanceType": "default",
            "usePersonalQueue": "false"
        }

        response = requests.post(self.run_url, headers=self.get_headers(), data=json.dumps(payload), timeout=30)
        result = response.json()

        if result.get('errorCode') == '421':
            raise Exception("API并发数已达上限，请稍后重试")

        if not result.get('taskId'):
            raise Exception(f"提交失败: {result}")

        return result.get('taskId')

    def query_task(self, task_id):
        """查询任务状态"""
        response = requests.post(self.query_url, headers=self.get_headers(),
                                data=json.dumps({'taskId': task_id}), timeout=30)
        result = response.json()
        
        # 处理两种响应格式：直接results或嵌套在data里
        status = result.get('status', 'UNKNOWN')
        outputs = result.get('results', [])
        
        # 如果有data字段，从中提取
        if 'data' in result:
            data = result['data']
            status = data.get('status', status)
            outputs = data.get('outputs', data.get('results', outputs))
        
        return {'status': status, 'outputs': outputs, 'data': result}

    def download_and_save(self, url, output_path):
        """下载图片"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        r = requests.get(url, timeout=60)
        with open(output_path, 'wb') as f:
            f.write(r.content)
        return output_path

    # ========== List.md 管理 ==========

    def load_list(self):
        """加载 List.md"""
        if not os.path.exists(LIST_FILE):
            return []
        tasks = []
        with open(LIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '|' not in line:
                    continue
                parts = line.split('|')
                if len(parts) >= 4:
                    tasks.append({
                        'task_id': parts[0].strip(),
                        'image_url': parts[1].strip(),
                        'status': parts[2].strip(),
                        'coins': parts[3].strip() if len(parts) > 3 else '',
                        'time': parts[4].strip() if len(parts) > 4 else '',
                        'output_url': parts[5].strip() if len(parts) > 5 else '',
                        'submitted_at': parts[6].strip() if len(parts) > 6 else ''
                    })
        return tasks

    def save_list(self, tasks):
        """保存 List.md"""
        lines = [
            "# 任务队列记录",
            "",
            "## 队列管理规则",
            "- 每行一个任务，格式：`task_id|image_url|status|coins|time|output_url|submitted_at`",
            "- status: `QUEUED` `RUNNING` `SUCCESS` `FAILED`",
            "- 提交间隔5分钟，每60秒查询一次所有待完成任务的进度",
            "",
            "## 字段说明",
            "| task_id | 任务ID |",
            "| image_url | 参考图URL |",
            "| status | 当前状态 |",
            "| coins | 消耗积分 |",
            "| time | 耗时（秒） |",
            "| output_url | 生成结果URL |",
            "| submitted_at | 提交时间 |",
            "",
            "---",
            ""
        ]
        for t in tasks:
            line = f"{t['task_id']}|{t['image_url']}|{t['status']}|{t['coins']}|{t['time']}|{t['output_url']}|{t['submitted_at']}"
            lines.append(line)
        lines.append("")
        lines.append(f"*最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}*")

        with open(LIST_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def add_task(self, task_id, image_url):
        """添加新任务到 List.md"""
        tasks = self.load_list()
        active = [t for t in tasks if t['status'] in ('QUEUED', 'RUNNING')]
        active.append({
            'task_id': task_id,
            'image_url': image_url[:80],
            'status': 'QUEUED',
            'coins': '',
            'time': '',
            'output_url': '',
            'submitted_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        })
        self.save_list(active)

    def update_task(self, task_id, status, coins='', time_str='', output_url=''):
        """更新任务状态"""
        tasks = self.load_list()
        updated = False
        for t in tasks:
            if t['task_id'] == task_id:
                t['status'] = status
                if coins:
                    t['coins'] = coins
                if time_str:
                    t['time'] = time_str
                if output_url:
                    t['output_url'] = output_url
                updated = True
        if updated:
            self.save_list(tasks)

    def get_active_tasks(self):
        """获取所有待完成的任务"""
        tasks = self.load_list()
        return [t for t in tasks if t['status'] in ('QUEUED', 'RUNNING')]

    def poll_all_active(self):
        """轮询所有待完成任务状态"""
        active = self.get_active_tasks()
        if not active:
            return

        print(f"🔄 检查 {len(active)} 个待完成任务...")
        for t in active:
            task_id = t['task_id']
            result = self.query_task(task_id)
            status = result.get('status', 'UNKNOWN')
            outputs = result.get('outputs', [])

            if status == 'SUCCESS':
                coins = ''
                elapsed = ''
                url = ''
                if outputs:
                    coins = outputs[0].get('consumeCoins', '')
                    elapsed = outputs[0].get('taskCostTime', '')
                    url = outputs[0].get('url', '')
                self.update_task(task_id, 'SUCCESS', coins=coins, time_str=str(elapsed), output_url=url)
                print(f"  ✅ {task_id[:20]}... 完成，消耗 {coins} 积分")

            elif status == 'FAILED':
                error = result.get('data', {}).get('errorMessage', '未知错误')
                self.update_task(task_id, 'FAILED')
                print(f"  ❌ {task_id[:20]}... 失败: {error}")

            elif status in ('QUEUED', 'RUNNING'):
                print(f"  ⏳ {task_id[:20]}... {status}")

    def run(self, reference_url, output_dir=None, poll_interval=60):
        """运行完整流程"""

        # 1. 提交任务
        print(f"📤 提交任务...")
        task_id = self.submit_task(reference_url)
        print(f"✅ 任务已提交: {task_id}")

        # 2. 记录到 List.md
        self.add_task(task_id, reference_url)

        # 3. 轮询等待完成
        print(f"⏳ 等待任务执行...")
        start_time = time.time()
        while True:
            result = self.query_task(task_id)
            status = result.get('status', 'UNKNOWN')
            outputs = result.get('outputs', [])

            if status == 'SUCCESS':
                elapsed = time.time() - start_time
                coins = ''
                url = ''
                if outputs:
                    coins = outputs[0].get('consumeCoins', '')
                    url = outputs[0].get('url', '')
                self.update_task(task_id, 'SUCCESS', coins=str(coins), time_str=f'{elapsed:.1f}', output_url=url)
                print(f"✅ 生成完成！耗时: {elapsed:.1f}秒，消耗 {coins} 积分")
                return {'task_id': task_id, 'url': url, 'coins': coins, 'elapsed': elapsed}

            elif status == 'FAILED':
                error = result.get('data', {}).get('errorMessage', '未知错误')
                self.update_task(task_id, 'FAILED')
                raise Exception(f"生成失败: {error}")

            else:
                print(f"⏳ 状态: {status}...")
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

    generator = MultiPhotoGenerator(api_key)

    if '--watch' in sys.argv or '--monitor' in sys.argv:
        print("🔄 开始监控任务队列（每60秒查询一次，Ctrl+C 退出）...")
        while True:
            generator.poll_all_active()
            print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 等待60秒...")
            time.sleep(60)
        return

    if len(sys.argv) < 2:
        print("用法: python3 multiphoto.py <参考图路径> [输出目录]")
        print("       python3 multiphoto.py --watch  # 监控任务队列")
        print("示例: python3 multiphoto.py ./model_photo.jpg ./output/")
        sys.exit(1)

    ref_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_DIR

    if not os.path.exists(ref_path):
        print(f"❌ 参考图不存在: {ref_path}")
        sys.exit(1)

    print(f"📤 上传参考图: {ref_path}")
    ref_url = generator.upload_image(ref_path)
    print(f"✅ 参考图已上传")

    result = generator.run(ref_url, output_dir)
    print(f"\n🎉 生成成功!")
    print(f"🖼️ URL: {result['url']}")
    print(f"⏱️ 耗时: {result['elapsed']:.1f}秒")
    print(f"💰 消耗: {result['coins']} 积分")


if __name__ == '__main__':
    main()
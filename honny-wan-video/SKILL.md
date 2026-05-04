---
name: honny-wan-video
description: >
  根据分镜脚本提示词和参考图生成视频 - RunningHub Wan 2.2 Remix V3 图生视频技能。
  任务提交后自动创建 List-{task_id}.md 记录文件，每60秒自动查询进度，任务完成后更新状态和积分消耗。
  
  触发关键词：生成视频、图生视频、Wan视频、分镜视频、视频生成
allowed-tools:
  - read
  - write
  - edit
  - exec
allowed-edit-paths:
  - ~/.openclaw/skills/honny-wan-video
---

# Honny Wan Video Skill

使用 RunningHub Wan 2.2 Remix V3 模型进行图生视频生成，动作超流畅。

## 功能

| 功能 | 说明 |
|------|------|
| **图生视频** | 上传参考图 + 分镜提示词生成视频 |
| **动作流畅** | Wan 2.2 Remix V3 超流畅算法 |
| **无色差** | 保持原图色彩一致性 |
| **支持时长** | 5秒或10秒视频 |
| **任务队列** | 每任务独立 List-{task_id}.md，每60秒自动查询状态 |

## 工作流

- **工作流ID**：`2048133528671490050`
- **参考图节点**：`nodeId=13`, `fieldName=image`
- **分镜提示词节点**：`nodeId=36`, `fieldName=text`
- **视频时长节点**：`nodeId=15`, `fieldName=value`

## 任务队列 (List-{task_id}.md)

### 管理规则

- 每个任务一个文件：`List-{task_id}.md`
- 提交时自动创建，记录 task_id、prompt、status
- 每60秒查询一次任务进度
- 完成后更新状态、积分消耗、耗时、视频URL

### 文件格式

```markdown
# 视频任务队列

## 基本信息
- task_id: 2050456296850898945
- status: SUCCESS / RUNNING / QUEUED / FAILED
- submitted_at: 2026-05-02 15:20
- completed_at: 2026-05-02 15:25

## 分镜提示词
0-2s: ...
2-4s: ...
...

## 结果
- video_url: https://...
- coins: 12
- elapsed: 60s
```

### 队列监控命令

```bash
# 监控所有视频任务
python3 ~/.openclaw/skills/honny-wan-video/scripts/wan_video.py --watch-all

# 查看所有任务文件
ls ~/.openclaw/skills/honny-wan-video/List-*.md
```

## API 接口说明

### 1. 提交任务

```
POST https://www.runninghub.cn/openapi/v2/run/ai-app/2048133528671490050
Headers: Authorization: Bearer {API_KEY}
Body:
{
  "nodeInfoList": [
    {"nodeId": "13", "fieldName": "image", "fieldValue": "参考图URL"},
    {"nodeId": "36", "fieldName": "text", "fieldValue": "分镜提示词"},
    {"nodeId": "15", "fieldName": "value", "fieldValue": "10"}
  ],
  "instanceType": "default",
  "usePersonalQueue": "false"
}
```

### 2. 查询任务状态

```
POST https://www.runninghub.cn/openapi/v2/query
Body: {"taskId": "任务ID"}
```

## 使用方法

### 命令行

```bash
# 基本用法
python3 ~/.openclaw/skills/honny-wan-video/scripts/wan_video.py \
  <参考图路径> "<分镜提示词>" [时长秒数] [输出路径]

# 示例 - 8秒分镜视频
python3 ~/.openclaw/skills/honny-wan-video/scripts/wan_video.py \
  ./photo.jpg "0-2s: 镜头推进... 2-4s: 发丝飘动..." 8 ./output/

# 示例 - 10秒分镜视频
python3 ~/.openclaw/skills/honny-wan-video/scripts/wan_video.py \
  ./photo.jpg "0-2s: 卧室床边... 2-4s: 窗边..." 10 ./
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 参考图路径 | 参考图片本地路径 | 必须提供 |
| 分镜提示词 | 分镜脚本，建议按时间轴描述 | 必须提供 |
| 时长 | 视频时长（秒） | 8 |
| 输出路径 | 视频保存目录 | ./video_output/ |

## 输出格式

```
🎬 视频生成成功！
📋 任务ID: {taskId}
⏱️ 耗时: {time}秒
💰 消耗: {coins} 积分
🎞️ 视频: {videoUrl}
📋 已创建 List-{taskId}.md
```

## 分镜提示词格式示例

```
0-2秒：远景固定机位缓慢推进，镜头对准女性背影上身，竹编卷帘光影投射在肩颈线条上
2-4秒：镜头继续向前微推进至中景，女性开始轻微抬头，发丝随微弱气流开始轻轻飘动
4-6秒：镜头从侧面缓慢环绕至女性侧前方，景别收缩至近景，女性微微转身露出侧颜
6-8秒：镜头缓慢后退拉开至中景全景，女性身体后仰单手轻撩裙摆，肩颈线条舒展优雅
```

---

*基于 RunningHub Wan 2.2 Remix V3*
*工作流ID: 2048133528671490050*

---
name: honny-multiphoto
description: >
  Honny 多图生成技能 - 一致性模特同场景不同表情不同动作 4图生成。
  支持上传参考图（模特图），生成同模特在同场景下的不同表情、不同动作的四宫格图片。
  任务间隔5分钟，避免API并发限制。

  触发关键词：多图、4图、同场景不同表情、模特多动作、一致性套图
allowed-tools:
  - read
  - write
  - edit
  - exec
allowed-edit-paths:
  - ~/.openclaw/skills/honny-multiphoto
---

# Honny Multi-Photo Skill

使用 RunningHub 工作流进行一致性模特同场景多图生成，支持同一场景下不同表情、不同动作的4宫格图片。

## 功能

| 功能 | 说明 |
|------|------|
| **同场景多动作** | 同一模特在同一场景下的不同表情、不同动作 |
| **人物一致性** | 基于参考图（模特图）保持角色一致性 |
| **4图生成** | 一次生成4张图片（2x2宫格） |
| **任务间隔** | 每任务间隔5分钟，避免API并发限制 |

## 工作流

- **工作流ID**：`2050987699099713538`
- **参考图节点**：`nodeId=42`, `fieldName=image`, `description=模特图`
- **提示词**：无需单独节点，参考图即为模特图
- **任务间隔**：5分钟

## 任务队列 (List.md)

### 管理规则

- 每行一个任务，格式：`task_id|image_url|status|coins|time|output_url|submitted_at`
- status: `QUEUED` `RUNNING` `SUCCESS` `FAILED`
- 每60秒查询一次所有待完成任务的进度
- **提交间隔5分钟**，任务完成后自动更新状态和积分消耗

### 队列监控命令

```bash
# 监控任务队列（持续轮询）
python3 ~/.openclaw/skills/honny-multiphoto/scripts/multiphoto.py --watch

# 查看当前队列
cat ~/.openclaw/skills/honny-multiphoto/List.md
```

## API 接口说明

### 1. 提交任务

```
POST https://www.runninghub.cn/openapi/v2/run/ai-app/2050987699099713538
Headers: Authorization: Bearer {API_KEY}
Content-Type: application/json

Body:
{
  "nodeInfoList": [
    {"nodeId": "42", "fieldName": "image", "fieldValue": "参考图URL或file_id", "description": "模特图"}
  ],
  "instanceType": "default",
  "usePersonalQueue": "false"
}
```

### 2. 查询任务状态

```
POST https://www.runninghub.cn/openapi/v2/query
Headers: Authorization: Bearer {API_KEY}
Body: {"taskId": "任务ID"}
```

### 3. 文件上传

```
POST https://www.runninghub.cn/openapi/v2/media/upload/binary
Headers: Authorization: Bearer {API_KEY}
Form: file=@图片路径
```

## 使用方法

### 命令行

```bash
# 生成4图（只需要提供模特参考图）
python3 ~/.openclaw/skills/honny-multiphoto/scripts/multiphoto.py \
  <参考图路径> [输出目录]

# 示例 - 使用模特图生成同场景4图
python3 ~/.openclaw/skills/honny-multiphoto/scripts/multiphoto.py \
  ./model_photo.jpg ./output/
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 参考图路径 | 参考图片本地路径（模特图） | 必须提供 |
| 输出目录 | 图片保存目录 | ./multiphoto_output/ |

## 输出格式

```
📸 多图生成成功！
📋 任务ID: {taskId}
🖼️ 图片: {url}
💰 消耗: {coins} 积分
⏱️ 耗时: {time}秒
📋 已记录到 List.md
```

---

*基于 RunningHub 一致性多图工作流*
*工作流ID: 2050987699099713538*
*功能：同场景不同表情/动作 4图生成（仅需参考图）*
*任务间隔：5分钟*
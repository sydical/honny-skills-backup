---
name: honny-photov2
description: |
  Honny 照片生成技能 V2 - 使用 RunningHub 工作流根据文本提示词生成照片。
  支持自动优化迭代，每天首次使用自动上传参考图。
  生成后自动注入 iPhone 16 风格 EXIF 信息（可配置）。
  
  触发关键词：生成照片、生成图片、照片生成、AI写真
allowed-tools:
  - read
  - write
  - edit
  - exec
allowed-edit-paths:
  - ~/.openclaw/skills/honny-photov2
  - ~/data/disk/workspace/memory
---

# HonnyPhotoV2 Skill

使用 RunningHub Wan2.2 API 进行图生图生成，支持生成后自动注入手机相机 EXIF 信息。

## 功能

| 功能 | 说明 |
|------|------|
| **参考图生图** | 使用参考图 + 提示词生成图片 |
| **自动优化** | 根据上下文结果自动优化提示词 |
| **参考图管理** | 每天首次自动上传并缓存参考图 |
| **EXIF 注入** | 自动注入 iPhone 16 风格相机信息（可配置） |

## 环境变量配置

在 `~/.openclaw/skills/honny-photov2/.env` 或 `~/.openclaw/workspace-companion2/.env` 中配置：

```bash
# RunningHub API Key（必须）
RUNNINGHUB_API_KEY=你的API密钥

# 工作流 ID（默认）
WORKFLOW_ID=1993965970465243137

# EXIF 注入配置（可选，默认开启）
EXIF_ENABLED=true
EXIF_PHONE_MODEL=iPhone 16
EXIF_PHONE_MAKE=Apple
EXIF_GPS_CITY=福州
```

### EXIF 注入字段

| 字段 | 值 | 说明 |
|------|-----|------|
| Make | Apple | 相机厂商 |
| Model | iPhone 16 | 设备型号 |
| DateTime | 当前时间 | 拍摄时间 |
| ExposureTime | 1/125 | 快门速度 |
| FNumber | 1.78 | 光圈值 |
| ISOSpeedRatings | 64 | ISO |
| FocalLength | 5.1mm | 焦距 |
| GPS | 福州 (26.0753°N, 119.2964°E) | GPS坐标 |

### GPS 城市支持

| 城市 | 纬度 | 经度 |
|------|------|------|
| 福州 | 26.0753 | 119.2964 |
| 北京 | 39.9042 | 116.4074 |
| 上海 | 31.2304 | 121.4737 |
| 深圳 | 22.5431 | 114.0579 |
| 成都 | 30.5728 | 104.0668 |

## 使用方法

### 基本命令

```
拍张照片
生成一张美美的写真
生成一张照片
```

### 高级用法

```
生成照片：可爱风格的
优化提示词后再生成[场景 + 人物主体 + 色彩同源 + 构图分层 + 动态情绪 + 画质参数]
```

## 自动流程

1. **检查参考图缓存**
   - 读取当天记忆中的参考图 URL
   - 如果没有，执行第2步

2. **上传参考图**（每天首次）
   - 查找用户 avatar 文件
   - 上传到 RunningHub
   - 保存 URL 到记忆

3. **生成图片**
   - 使用参考图 + 优化后的提示词
   - 调用工作流 API
   - 返回生成结果

4. **EXIF 注入**（默认开启）
   - 下载图片到本地
   - 注入 iPhone 16 风格 EXIF
   - 保存到指定输出目录

## 输出格式

```
🎨 照片生成成功！

📝 提示词：{优化后的提示词}
🖼️ 图片：{图片URL}
💾 本地：{本地路径}
📱 EXIF：Apple iPhone 16
📅 拍摄时间：{当前时间}
📍 GPS：福州 (26.0753°N, 119.2964°E)
```

## 命令行用法

```bash
# 基本用法（自动 EXIF + 下载到本地）
python3 scripts/generator.py "提示词"

# 指定输出目录
python3 scripts/generator.py "提示词" /path/to/output_dir

# 关闭 EXIF 注入
EXIF_ENABLED=false python3 scripts/generator.py "提示词"
```

## 注意事项

- 需要配置 RUNNINGHUB_API_KEY
- 首次使用需要提供参考图（avatar）
- 生成可能需要等待队列
- EXIF 注入依赖 piexif 和 Pillow 库

---

*基于 RunningHub API v2*
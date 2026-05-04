---
name: netease-music
description: |
  网易云音乐技能 - 歌曲搜索、歌单获取、排行榜、歌词查看。
  支持方案A：轻量版功能集。
  
  触发关键词：网易云音乐、听歌、搜索歌曲、歌词
allowed-tools:
  - read
  - write
  - edit
  - exec
allowed-edit-paths:
  - ~/.openclaw/skills/netease-music
---

# NeteaseCloudMusic Skill

网易云音乐轻量版技能（方案A）

## 功能列表

| 命令 | 功能 | 需要登录 |
|------|------|---------|
| `/music search <关键词>` | 搜索歌曲 | ❌ |
| `/music detail <歌曲ID>` | 歌曲详情 | ❌ |
| `/music lyric <歌曲ID>` | 歌词 | ❌ |
| `/music playlist <歌单ID>` | 歌单歌曲 | ❌ |
| `/music rank` | 排行榜 | ❌ |
| `/music url <歌曲ID>` | 播放链接 | ⚠️ 部分 |

## 环境配置

### .env 文件位置

```
~/.openclaw/skills/netease-music/.env
```

### 配置项

| 变量 | 说明 | 必填 |
|------|------|------|
| `MUSIC_API_URL` | 网易云 API 地址 | ✅ |
| `MUSIC_COOKIE` | 登录 Cookie（可选） | ❌ |

### 获取 Cookie 方法

1. 浏览器登录网易云音乐
2. 按 F12 打开开发者工具
3. Network → 任意请求 → Headers → Cookie
4. 复制完整 Cookie 字符串

---

## 使用示例

```bash
# 搜索歌曲
/music search 周杰伦

# 查看歌词
/music lyric 123456

# 获取排行榜
/music rank
```

---

## 注意事项

1. 免费歌曲可直接播放
2. VIP 歌曲需要配置 Cookie
3. API 可能有频率限制

---

*基于 Binaryify/NeteaseCloudMusicApi 设计*

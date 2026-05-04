# 任务队列记录

## 队列管理规则

- 每行一个任务，格式：`task_id|prompt|status|coins|time|output_url`
- status: `QUEUED` `RUNNING` `SUCCESS` `FAILED`
- 每60秒查询一次所有待完成任务的进度
- 任务完成后更新状态和积分消耗

## 字段说明

| 字段 | 说明 |
|------|------|
| task_id | RunningHub 任务ID |
| prompt | 提示词摘要 |
| status | 当前状态 |
| coins | 消耗积分 |
| time | 耗时（秒） |
| output_url | 生成结果URL |
| submitted_at | 提交时间 |

## 示例

```
2050291848673021954|新中式禅意写真低位仰拍角度|SUCCESS|3|45|https://rh-images.../output.png|2026-05-02 15:00
2050291848673021955|新中式禅意写真高位俯拍角度|RUNNING|||
```

---

*最后更新：每次提交/查询任务时自动同步*

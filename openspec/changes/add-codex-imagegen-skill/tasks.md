## 1. Contract and failing gate

- [x] 1.1 定义完整快照、内置优先与宿主识别边界
- [x] 1.2 增加来源证明校验器，并确认缺少快照时失败

## 2. Package implementation

- [x] 2.1 完整复制 Codex 系统 `imagegen` 技能
- [x] 2.2 增加来源证明并更新技能清单、版本与 README
- [x] 2.3 确认快照保持内置工具优先且不要求内置路径配置 API Key

## 3. Verification and publication boundary

- [x] 3.1 运行 lint、包结构、来源证明与 TRACE 门禁
- [x] 3.2 运行 `openspec validate --strict`
- [x] 3.3 记录正式 tag、Release 与消费锁更新仍需发布授权

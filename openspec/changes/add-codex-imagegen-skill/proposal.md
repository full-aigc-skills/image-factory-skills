## Why

Image Factory 的 Codex 路径应优先使用宿主自带的图片能力，但当前技能包只发布批次治理技能，消费插件无法把同一份 `imagegen` 指令作为受管依赖锁定。直接改消费插件副本又会破坏受管技能的单一事实源与不可变供应链。

## What Changes

- 从 Codex 系统技能复制完整 `imagegen` 快照，包括技能正文、脚本、引用资料、图标、Agent 元数据与许可证。
- 在技能包清单中发布 `imagegen`，并记录逐文件 SHA-256 来源证明。
- 增加一个确定性校验器，保证发布内容与来源证明完全一致。
- 不把技能存在本身当成 Codex 宿主证明；宿主识别与降级策略仍归消费插件 Harness。

## Capabilities

### New Capabilities

- `codex-imagegen-snapshot`: 完整、可审计地发布 Codex `imagegen` 系统技能快照。

### Modified Capabilities

- `verified-skill-release`: 新快照必须通过既有结构、断链和 TRACE 门禁后才能发布。

## Impact

影响 `skills/imagegen/`、`.claude-plugin/plugin.json`、README、来源证明与发布校验脚本。不会修改其他四个 Image Factory 技能，也不会在本变更中发布 GitHub Release。

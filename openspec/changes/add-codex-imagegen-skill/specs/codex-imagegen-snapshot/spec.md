## Purpose

把 Codex 系统 `imagegen` 技能作为完整、可审计且可独立安装的技能包快照发布，同时不把该快照的存在误当成宿主身份。

## ADDED Requirements

### Requirement: The imagegen snapshot is complete and byte-verified

技能包 MUST 包含 `imagegen` 的技能正文、脚本、引用资料、图标、Agent 元数据与许可证。来源证明 MUST 列出每个文件的 SHA-256，发布校验 MUST 拒绝文件缺失、额外文件或内容漂移。

#### Scenario: The packaged snapshot is verified

- **WHEN** 发布门禁校验 `skills/imagegen/`
- **THEN** 实际文件集合与来源证明完全相同，且每个文件摘要匹配

### Requirement: Built-in generation remains the default Codex path

复制后的技能 MUST 保留 Codex 内置 `image_gen` 为默认执行路径，且该路径 MUST NOT 要求 `OPENAI_API_KEY`。CLI/API 路径 MUST 继续要求用户显式选择或确认。

#### Scenario: A normal Codex image request uses the skill

- **WHEN** 用户已确认生图且没有明确要求 CLI/API/model 控制
- **THEN** 技能选择内置 `image_gen`，不要求用户配置 API Key

### Requirement: Snapshot presence does not prove host identity

技能包 MUST NOT 声称只要发现 `imagegen` 目录即可判定当前宿主是 Codex。

#### Scenario: Another host installs the package

- **WHEN** ZCode、Kimi 或其他宿主发现复制后的技能
- **THEN** 宿主身份仍由当前会话的可靠元数据或工具能力决定，而不是由技能目录存在决定

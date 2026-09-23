## MODIFIED Requirements

### Requirement: Skill changes pass deterministic quality gates

本仓创作或修改的技能内容 MUST 通过结构校验、断链检查和确定性 TRACE 评估；发布门禁 MUST 在任一此类技能低于规定阈值时失败。逐字节复制且不可私改的外部受管快照 MAY 低于本仓 TRACE 阈值，但只在其来源证明完整、文件集合与逐文件摘要均验证通过时例外；门禁 MUST 明确报告该例外及实际 TRACE 分数。

#### Scenario: Package is ready for release

- **WHEN** 包内所有技能及其引用资源完成评估
- **THEN** 结构检查无错误，本仓创作的每个技能 TRACE 总分不低于 4.5，任何低于阈值的来源快照均有通过验证的逐文件证明

#### Scenario: A skill has a broken reference

- **WHEN** `SKILL.md` 或随附文档引用不存在的包内资源或违规的跨技能相对路径
- **THEN** 发布检查失败并报告来源文件和目标

#### Scenario: A sourced snapshot drifts

- **WHEN** `imagegen` 快照新增、缺失或修改任一文件而来源证明未同步更新
- **THEN** 发布检查失败并报告发生漂移的文件

#### Scenario: A sourced snapshot scores below the authored-skill threshold

- **WHEN** 完整快照的 TRACE 总分低于 4.5，但来源证明验证通过
- **THEN** 门禁报告实际分数与 `SOURCE-VERIFIED` 例外，不要求修改上游快照，也不把它伪装成达标分数

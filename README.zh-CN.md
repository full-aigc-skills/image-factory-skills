# image-factory-skills

**Image Factory AIGC 技能** — 批量图片生产工作流：质量评判 / 恢复 / 运行编排。

本包包含 **5 个技能**。

## 📦 安装

```bash
npx skills add full-aigc-skills/image-factory-skills
```

## 🎯 技能列表 (5)

| 技能 | 描述 |
|------|------|
| `imagegen` | Codex 内置 `image_gen` 优先的生图与编辑技能完整快照 |
| `image-factory-use` | 路由器：分发图片生产请求到最窄适用 Skill |
| `image-factory-run` | 按已验证计划执行生产、配额、记录、产出 |
| `image-factory-judge` | 质量评判 + 优化循环 |
| `image-factory-recover` | 中断恢复 + 状态对账 |

## 🤖 支持的智能体

适用于 Claude Code / Codex / Cursor / OpenCode / Gemini CLI / GitHub Copilot / Windsurf 等。

<!-- FULL_STACK_DOC_START -->
## 项目定位与边界

`image-factory-skills` 是包含 **5 个可独立安装 Agent Skill** 的源代码仓库，当前清单版本为 `1.1.0`。本仓负责技能的触发说明、工作流、references、examples 与质量门禁；宿主插件的 Hook、MCP、凭据注入和运行时脚本不属于本仓职责。

| 已确认事实 | 值 | 证据 |
|---|---|---|
| 安装包 | `full-aigc-skills/image-factory-skills` | `.claude-plugin/plugin.json`、仓库远端 |
| 可安装技能 | 5 | `skills/*/SKILL.md` |
| 当前版本 | `1.1.0` | `.claude-plugin/plugin.json` |
| 规格事实源 | OpenSpec | `openspec/config.yaml` |
| 许可证 | Apache-2.0 | `LICENSE` |

### 不负责

- 不替代消费插件中的可执行 Harness、MCP 服务、Hook 或供应商客户端；
- 不把 `SKILL.md` 被复制到目录视为宿主已经发现、触发或成功执行；
- 不自动授权网络调用、付费生成、文件覆盖、上传或发布；
- 不允许消费插件直接修改受 `skills.lock.json` 管理的副本。

## 一眼看懂

```text
用户任务
  │
  ▼
name / description 发现技能
  │
  ▼
读取完整 SKILL.md ──► 按需加载 references / examples / scripts
  │
  ▼
执行领域工作流 ──► 收集验证证据 ──► PASS / FAIL / UNVERIFIED
```

## 已验证的安装与发现

```bash
npx skills add full-aigc-skills/image-factory-skills
npx skills add full-aigc-skills/image-factory-skills --skill image-factory-judge
npx skills list --json
```

固定发布版本时使用 GitHub Release/tag，不要把移动的 `main` 当成不可变版本。安装完成后应核对技能数量、名称、资源文件和目标 Agent 列表；Codex、ZCode、Kimi 的真实插件加载仍需分别验证。

## 包结构与加载规则

```text
image-factory-skills/
├── .claude-plugin/plugin.json   # 包名、版本与技能清单
├── skills/<name>/SKILL.md       # 触发条件与主工作流
├── skills/<name>/references/    # 按任务加载的领域知识
├── skills/<name>/examples/      # 请求、验收与恢复示例
├── scripts/                     # 仓库级生成和质量门禁（若存在）
├── openspec/                    # 规格与归档变更
└── LICENSE
```

跨技能协作必须使用技能名和安装命令，不得依赖 `../sibling-skill/` 相对链接，因为用户可能只安装一个技能。

## 质量、发布与安全

```bash
python3 scripts/lint_skills.py
python3 scripts/verify_sourced_snapshots.py
```

发布前还必须检查 frontmatter、相对链接、资源完整性、TRACE 阈值、版本清单以及干净环境安装。正式 tag 不得移动；内容变化应发布新版本，并让消费插件通过 tag、peeled SHA 和摘要更新锁文件。

安全边界：不得提交真实密钥、账号、本机绝对路径或私有仓库地址；脚本应默认最小权限，付费、上传、删除和覆盖动作必须保留显式授权门。

### Release 通知凭据

GitHub Release 发布后，`.github/workflows/notify-consumers.yml` 使用源仓 Actions Secret `SKILLS_SYNC_TOKEN` 向 `full-aigc-plugins/image-factory-plugin` 发送不可变 tag 与 peeled commit SHA。该 token 必须覆盖目标插件仓，并具备目标仓 `Contents: write` 权限；仓库不再识别 `FULL_AIGC_SKILLS_SYNC_TOKEN`。Secret 只通过 GitHub Actions 注入，禁止写入文件、命令输出或日志。

## 故障排查

| 现象 | 检查 | 处理 |
|---|---|---|
| 安装后未发现技能 | frontmatter、Agent 发现目录、是否需要刷新 | 用 `skills list --json` 核对实际发现结果 |
| 只安装单个技能后引用缺失 | 是否存在跨技能相对路径 | 把必需资源移入当前技能，或按名称安装依赖技能 |
| 插件完整性检查失败 | tag、peeled SHA、摘要和本地技能清单 | 在源技能仓发布新版本，再由同步 PR 更新插件 |
| 工具或凭据缺失 | `compatibility`、运行时前置条件 | 报告 `UNVERIFIED`，不要猜测成功 |
| 自动化第二次运行仍产生差异 | 生成器非幂等或清单漂移 | 阻止发布并修复生成/排序规则 |
| Release dispatch 返回 403 | `SKILLS_SYNC_TOKEN` 的目标仓范围、`Contents: write`、组织审批或有效期 | 修正 token 后覆盖同名 Actions Secret，并重跑失败 job |
<!-- FULL_STACK_DOC_END -->

## 📄 License

Apache 2.0

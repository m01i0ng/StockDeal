<!-- Source: .ruler/AGENTS.md -->

# AGENTS.md

## 行为规范

1. **语言规范**:
   - **强制中文回复**。无论用户的输入或当前语境是中文还是英文，所有非代码的输出内容（包括解释、方案及注释）**必须**使用中文。
   - **代码注释**: 代码注释**必须**使用中文。
2. **工具使用**:
   - **第三方库**: 使用 `context7` MCP 获取文档，确保最佳实践。
   - **网页内容**: 使用 `chrome-devtools` MCP 获取，而非直接访问。
   - **文件修改**: **必须**使用编辑工具（如 `replace_string` 等）。
   - **绝对禁止**: 使用 `cat`、`heredoc`、`sed`、`echo` 等命令行方式修改文件。
3. **依赖管理**: 必须使用包管理命令来安装依赖，比如 `pnpm add`、`dotnet add`、`uv add` 等。
4. **开发流程**:
   - **规划**: 任务开始前应明确目标和步骤（可使用 `task.md` 或计划列表）。

## Git 提交规范

### 格式

`<type>(<scope>): <subject>`

### Type 说明

- `feat`: 新增功能
- `fix`: 修复 bug
- `docs`: 文档变更
- `style`: 代码格式调整
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具变动
- `revert`: 回退
- `build`: 打包相关

### 示例

```bash
feat(sensor): 新增传感器管理模块
- 实现 CRUD 功能
- 增加缓存初始化
```

### 分支命名

- 功能: `feature/[描述]` (e.g., `feature/user-auth`)
- 修复: `fix/[IssueID]-[描述]` (e.g., `fix/issue-42`)
- 发布: `release/[版本]`
- 热修: `hotfix/[版本]`

**注意**: ❌ 未经允许不要自动 commit 代码。

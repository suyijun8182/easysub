# 贡献指南

感谢你的贡献！我们欢迎来自社区的任何贡献。

## 行为准则

本项目采纳贡献者公约。参与此项目意味着你同意遵守其条款。请详见 [CODE_OF_CONDUCT](./CODE_OF_CONDUCT.md)。

---

## 如何贡献？

### 报告 Bug

在 [Issues](https://github.com/suyijun8182/easysub/issues) 中创建新 Issue。

**请包含**：
- 清晰的标题
- 问题的详细描述
- 复现步骤
- 实际行为与预期行为
- 环境信息（OS、Docker 版本、浏览器等）
- 相关日志或截图

### 建议功能

在 [Issues](https://github.com/suyijun8182/easysub/issues) 中创建 Feature Request。

**请说明**：
- 功能的用途
- 期望的行为
- 可能的实现方式

### 提交代码

1. **Fork 项目**
   ```bash
   git clone https://github.com/suyijun8182/easysub.git
   ```

2. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或 fix/bug-fix-name
   ```

3. **开发和测试**
   - 遵循现有代码风格
   - 添加测试（如适用）
   - 确保本地测试通过

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加功能描述"
   # 或 "fix: 修复问题描述"
   ```
   
   遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：
   - `feat:` 新功能
   - `fix:` 修复 bug
   - `docs:` 文档更新
   - `style:` 代码格式（不改逻辑）
   - `refactor:` 重构代码
   - `perf:` 性能优化
   - `test:` 添加或更新测试
   - `chore:` 其他更改

5. **推送并创建 Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   然后在 GitHub 上创建 Pull Request

---

## 代码风格

### Python（后端）

遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/)：

```bash
# 使用 black 格式化
pip install black
black backend/

# 使用 flake8 检查
pip install flake8
flake8 backend/
```

### JavaScript（前端）

遵循 [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)：

```bash
# 使用 Prettier 格式化
npm run format

# 使用 ESLint 检查
npm run lint
```

### 通用规则

- 使用有意义的变量名
- 添加注释说明复杂逻辑
- 一次提交只做一件事
- 保持小的、可审查的 Pull Request

---

## 开发环境设置

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖（包含开发依赖）
pip install -r requirements.txt

# 安装代码检查工具
pip install black flake8 pytest

# 运行开发服务器
uvicorn app.main:app --reload --port 8000
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint

# 代码格式化
npm run format
```

---

## 测试

添加新功能时，请添加相应的测试。

### Python 测试

```bash
cd backend
pytest
```

### JavaScript 测试

```bash
cd frontend
npm test
```

---

## Pull Request 流程

1. **本地测试** - 确保代码本地能运行
2. **提交 PR** - 填写 PR 模板，清晰说明更改内容
3. **审查** - 等待 Maintainer 审查
4. **修改反馈** - 根据审查意见做修改
5. **合并** - 审查通过后合并到 main 分支

### PR 模板

```markdown
## 描述
简要说明这个 PR 做了什么

## 相关 Issue
关联的 Issue（如 #123）

## 更改类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新

## 测试
说明如何测试这个更改

## 检查清单
- [ ] 代码遵循项目风格指南
- [ ] 自行审查了代码
- [ ] 添加了必要的注释
- [ ] 本地测试通过
- [ ] 没有新的警告信息
```

---

## 文档贡献

文档和示例与代码一样重要。如果你发现文档有误或不清楚：

1. 在 [Issues](https://github.com/suyijun8182/easysub/issues) 中报告
2. 或直接提交改进的 PR

**文档文件位置**：
- 主要文档：根目录 `.md` 文件
- API 文档：代码注释
- 部署文档：[各厂家NAS安装教程.md](./各厂家NAS安装教程.md)

---

## 本地化贡献

帮助我们支持更多语言：

1. 在 `frontend/src/i18n/index.js` 中新增一个语言对象（参照现有的 `zh` / `en` / `ru`）
2. 翻译所有字符串键
3. 在 `messages` 中注册该语言并加入语言切换项
4. 提交 PR

---

## 设计贡献

改进 UI/UX：

1. 在 Issue 中讨论你的想法
2. 提供设计稿或原型
3. 获得反馈后提交实现 PR

---

## 获取帮助

有问题？

- 📧 在 Issue 中提问
- 💬 在 Discussions 中讨论
- 🔗 查看现有 Issues 和 Discussions

---

## 许可

通过贡献代码，你同意将你的贡献放在项目的 [MIT License](./LICENSE) 下。

---

## 致谢

再次感谢你的贡献！每一个贡献都很重要，无论多小。

你的名字将被添加到：
- CONTRIBUTORS.md
- GitHub Contributors 列表

---

**Happy coding! 🚀**

# Bakapiano · 知识库

Hugo + Hextra 网站。旧博客 22 篇文章已恢复为 Markdown，统一放在 **旧博客（算法竞赛）** 下。

## 当前状态

- 源码使用 `main` 分支；原 Hexo 站点的 `master` 分支保留作回退备份。
- Hugo Extended **0.169.0**，Hextra **v0.13.0**（固定 Git 子模块版本）。
- 原始日期、标题、67 个代码块、9 张插图与文章内标题锚点保留。
- 旧 `/年/月/日/文章/` 地址使用 Hugo aliases 跳转到新栏目。
- 全文搜索、深浅色切换、公式、Markdown 输出与 `llms.txt` 已配置。
- 旧站快照位于相邻的 `../legacy-blog-snapshot`，没有修改。
- Markdown 从公开 HTML 恢复，并非找回了原始源文件；旧文可能原本就有排版、公式或链接问题。

## 本地预览

首次克隆时保留主题子模块：

```powershell
git submodule update --init --recursive
hugo server --disableFastRender
```

这次搭建的 Windows 工作目录内已有独立的 Hugo，无需修改系统环境：

```powershell
.\.tools\hugo\hugo.exe server --disableFastRender
```

打开 `http://localhost:1313/`。常规生产构建：`hugo --gc --minify`。

## 编辑内容

- `content/_index.md`：首页。
- `content/legacy-blog/_index.md`：旧博客栏目说明。
- `content/legacy-blog/*.md`：22 篇旧文章，建议直接编辑这些文件。
- `hugo.yaml`：站点名称、导航、主题、搜索及公式配置。
- `assets/css/custom.css`：少量站点级样式，不修改主题。

新增其他栏目时，在 `content/<栏目名>/_index.md` 设置 `title` 与 `type: docs`，并在 `hugo.yaml` 的导航中添加对应 `pageRef`。

## 发布到现有 GitHub Pages

目标为 `bakapiano/bakapiano.github.io`，正式地址为 `https://bakapiano.github.io/`。

保留远端 `master` 作为旧站快照，使用 `main` 维护新站源码，不强制覆盖或删除旧分支。

1. 将本工程（包括 `.gitmodules` 和主题子模块引用）提交并推送到目标仓库的新源码分支 `main`。
2. 仓库 Settings → Pages → Source 选择 **GitHub Actions**。
3. Actions → Deploy Hextra to GitHub Pages → Run workflow，选择 `main`。
4. 等待部署成功，检查首页、文章、公式、搜索和旧地址跳转。

工作流自动使用 Pages 实际 base URL；如果将来改用项目站或自定义域名，还应同步更新 `hugo.yaml` 的 `baseURL`。

## 迁移来源与复核

`migration/report.json` 记录原仓库提交、22 篇文章映射、代码哈希与图片来源。

```powershell
python -m pip install -r scripts/requirements.txt
hugo --gc --minify
python scripts/verify_migration.py
```

`scripts/migrate_legacy.py` 是一次性恢复脚本。默认拒绝覆盖已存在的文章；只有需要重新生成并且没有人工编辑时才使用 `--overwrite`。

搜索及数学渲染资源已本地化，构建和阅读均不依赖第三方 CDN，见 `THIRD_PARTY.md`。

历史文章中的第三方题库、下载链接未做批量可用性保证；迁移不会擅自修改原文结论或升级旧教程。

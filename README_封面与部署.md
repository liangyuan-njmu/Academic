# Yuan Liang 学术网页 — Publications 封面更新

## 已完成

- 保留了原来的 29 篇论文、个人头像、个人资料及前端编辑功能。
- Publications 缩略图改为竖版封面展示（不裁切图片）。
- 为 10 篇论文查到对应出版卷期及封面来源页面：其中 5 篇页面有可直接引用的封面网址（Cell 1、Oncogene 3、Annals of Translational Medicine 1），另 5 篇可尝试从封面来源页提取图片。已明确区分真正的“当期封面”和仅用于识别期刊的“期刊图像”。
- 另外 5 篇提供了期刊级别的识别图片（**不是当期封面**）。其余 14 篇保留清晰的 Cover pending 提示，不会使用其他卷期封面冒充。
- `cover_sources.json` 逐篇记录 DOI、原始封面网址、出版期次、来源页、验证级别。
- `scripts/fetch_covers.py` 可以联网后下载图片到 `assets/covers/`，然后将网站中的图片路径替换为本地文件。跳过失效的图片，写入 `cover-download-report.json`。

**重要：此执行环境不具备可用的外部图片下载网络，因此 ZIP 内尚未包含出版社原始封面图片文件。网站会直接引用已找到的外部图片网址，并在 GitHub Actions 部署时尝试将图片下载到自己的 assets 目录。如果出版社阻止下载或禁止外链，将显示封面不可用的提示。不能保证全部 29 篇均有可下载封面。**

## GitHub Pages 发布步骤

1. 解压 ZIP，把文件和子目录完整上传到 `https://github.com/liangyuan-njmu/liangyuan-njmu.github.io` 的 `main` 分支，**包括 `.github/workflows/pages.yml`、`scripts/`、`assets/`、`cover_sources.json` 和 `index.html`**。GitHub 网站上传文件时通常需要逐文件添加；用 git push 更方便。
2. 在仓库 Settings → Pages → Build and deployment → Source 设置为 **GitHub Actions**（**不要选择 Deploy from a branch**，因为这个版本的工作流会在部署时自动抓取封面）。
3. 进入 Actions，找到 `Publish academic homepage with journal covers`，确认部署任务显示绿色对勾。
4. 访问 `https://liangyuan-njmu.github.io/`，检查每篇文献旁边的封面。如果某期刊服务器禁止访问，Cover pending 是合理的降级显示。

## 本地下载图片（可选）

```bash
python -m pip install requests beautifulsoup4 pillow
python scripts/fetch_covers.py
```

运行后，下载成功的封面会位于 `assets/covers/paper-XX.webp`，网站 `index.html` 会指向这些本地图片。需将 `index.html` 和 `assets/` 一起上传。

## 后续补齐

对 `cover_sources.json` 中标记为 `pending` 的论文，建议到每篇论文的期刊官网，打开实际发表卷期页面，人工下载原版封面，命名为相应的 `paper-XX.webp`，然后在 Edit → Publications → 图片 URL 中填 `assets/covers/paper-XX.webp`。引用封面时应注意出版社版权和署名要求；封面并不一定随论文开放获取协议授予再发布许可。

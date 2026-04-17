# NotebookLM PPT Workbench

一个用于 `NotebookLM` 演示文稿工作流的个人工作台，用来整理输入素材，并将导出的结果重建为可编辑的 PowerPoint 文件。

整个产品有意拆成两部分：

1. `Workbench`
负责来源整理、提示词编辑、项目历史记录，以及 NotebookLM 的 handoff。
2. `Reconstruction engine`
负责读取导出的 slide 资产，并重建为：
   - 一份更接近原始展示效果的 clone
   - 一份更适合继续编辑的 `.pptx`

当前仓库采用的是 `半自动` 路线：

- 系统负责准备来源和提示词
- 用户在 NotebookLM 内完成生成与导出
- 本地 agent 负责导出后的重建与交付

## 当前 V1 范围

### 第一部分：半自动 NotebookLM 工作台

- 项目列表与项目切换
- 项目详情持久化
- 来源输入支持：
  - 链接
  - 文件路径
  - 图片路径
  - 音频路径
  - 视频路径
- 来源洞察摘要
- 来源版本历史
- 来源版本 diff 视图
- 来源版本完整清单视图
- 来源 compare 视图
- compare 过滤与 compare 摘要回填 Prompt Studio

### 第二部分：可编辑 PPT 重建

- 展示版 clone 输出
- editable rebuild 输出
- 多页重建
- OCR 同行文本合并
- 标题 / 正文层级恢复
- 列表分组与缩进
- 图片保留与 caption 恢复
- 双栏文本处理
- 表格重建支持：
  - `colspan`
  - 首列 `rowspan`
  - 非首列 `rowspan`
  - 多级表头
  - 列宽跟随原始网格
  - 表头样式与边框
  - raw OCR box 优先的表格检测
- 图标卡片恢复支持：
  - 小图标或小图片
  - 标题
  - 说明文字

## 建议先读

- 交付说明：`docs/DELIVERY.md`
- 验收清单：`docs/ACCEPTANCE.md`
- 演示讲稿：`docs/DEMO_SCRIPT.zh-CN.md`

## 本地运行

### 启动后端 agent

```powershell
cd agent
python -m uvicorn app.main:app --reload
```

### 启动前端

```powershell
cd web
npm install
npm run dev
```

## 验证命令

### 后端

```powershell
cd agent
python -m pytest -q
```

### 前端

```powershell
cd web
npm test -- --run
npm run build
```

### 验收脚本

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_manual_acceptance.ps1
```

## 当前版本的推荐使用方式

1. 在工作台中创建项目
2. 输入 brief、来源链接和素材路径
3. 使用 Prompt Studio 整理生成提示词
4. 进入 NotebookLM 手动生成并导出
5. 回到本地工作台上传导出物
6. 生成：
   - 展示版 clone
   - editable rebuild

## 当前版本的真实边界

- NotebookLM 登录与生成流程不是全自动
- 当前最强的恢复对象是：
  - 结构化文本页
  - 表格页
  - 图标卡片页
- 对于装饰性特别强、版式极自由的页面，当前重建仍会更偏向结构化恢复，而不是逐像素还原

## 如果你要快速闭环

优先做这三件事：

1. 准备真实样例素材
2. 跑一轮验收脚本
3. 用演示讲稿完成一次完整展示

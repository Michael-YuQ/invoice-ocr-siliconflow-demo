# 发票 OCR Demo

这是一个适合课堂演示的批量发票识别 demo：

- 扫描一个文件夹里的 PDF / JPG / PNG 发票
- 使用硅基流动的 `deepseek-ai/DeepSeek-OCR`
- 自动抽取公司名、金额、税额、日期、发票号等字段
- 导出 `CSV + JSON + 原始 OCR 文本`

## 1. 安装依赖

```powershell
python -m pip install -r invoice_ocr_demo/requirements.txt
```

## 2. 设置 API Key

PowerShell:

```powershell
$env:SILICONFLOW_API_KEY="你的硅基流动API Key"
```

## 3. 运行

扫描当前目录下的发票：

```powershell
python invoice_ocr_demo/run_invoice_ocr.py --input-dir .
```

递归扫描子目录：

```powershell
python invoice_ocr_demo/run_invoice_ocr.py --input-dir . --recursive
```

只先跑 2 个文件做课堂演示：

```powershell
python invoice_ocr_demo/run_invoice_ocr.py --input-dir . --limit 2
```

只处理文件名里包含“发票”的文件：

```powershell
python invoice_ocr_demo/run_invoice_ocr.py --input-dir . --match 发票
```

## 4. 输出内容

默认输出在 `invoice_ocr_demo/output/`：

- `invoice_results.csv`
- `invoice_results.json`
- `raw_ocr/*.txt`

其中：

- `company_name` 通常优先取销售方公司名
- `seller_name` / `buyer_name` 来自 OCR 文本里的“名称:”
- `total_amount` 尽量取价税合计小写金额
- `pretax_amount` / `tax_amount` 尽量从合计区域提取
- `parse_status` 为 `needs_review` 时，表示 OCR 有结果，但字段抽取不够确定

## 5. 适合你课上讲的点

这个 demo 很适合讲 `AI Coding`：

1. 用 AI 很快搭出“批处理 + API 调用 + 字段抽取 + 导出结果”整条链。
2. 先跑一个最小版本，再逐步加字段、加异常处理、加报表。
3. 可以现场展示“AI 生成代码后，人还要做规则和质量兜底”。

## 6. 注意

- 这个 demo 默认把 PDF 先渲染成第一页图片，再送给 OCR 模型，这样比直接传 PDF 更稳。
- 发票版式很多，正则抽取不可能 100% 通吃；真实业务里建议再加人工校对页，或者再接一层结构化抽取模型。

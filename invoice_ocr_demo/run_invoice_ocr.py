import argparse
import base64
import csv
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import fitz
import requests


API_URL = "https://api.siliconflow.cn/v1/chat/completions"
DEFAULT_MODEL = "deepseek-ai/DeepSeek-OCR"
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".webp"}


@dataclass
class InvoiceRecord:
    file_name: str
    file_path: str
    file_type: str
    company_name: str | None = None
    seller_name: str | None = None
    buyer_name: str | None = None
    invoice_type: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    total_amount: str | None = None
    pretax_amount: str | None = None
    tax_amount: str | None = None
    currency: str | None = None
    summary: str | None = None
    raw_ocr_text_file: str | None = None
    parse_status: str = "ok"
    parse_note: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch OCR invoices from a folder using SiliconFlow DeepSeek OCR."
    )
    parser.add_argument(
        "--input-dir",
        default=".",
        help="Folder containing invoice files. Defaults to current directory.",
    )
    parser.add_argument(
        "--output-dir",
        default="invoice_ocr_demo/output",
        help="Folder used to save CSV, JSON and raw OCR text.",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("SILICONFLOW_API_KEY"),
        help="SiliconFlow API key. Defaults to SILICONFLOW_API_KEY env var.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OCR model id. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan subfolders recursively.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit for number of files to process.",
    )
    parser.add_argument(
        "--dpi-scale",
        type=float,
        default=2.0,
        help="PDF render scale. Higher means clearer image but larger payload. Default: 2.0",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="HTTP timeout in seconds. Default: 120",
    )
    parser.add_argument(
        "--match",
        default=None,
        help="Only process files whose names contain this keyword, for example 发票 or 订单.",
    )
    return parser.parse_args()


def iter_invoice_files(input_dir: Path, recursive: bool) -> Iterable[Path]:
    if input_dir.is_file() and input_dir.suffix.lower() in SUPPORTED_EXTENSIONS:
        yield input_dir
        return

    iterator = input_dir.rglob("*") if recursive else input_dir.glob("*")
    for path in sorted(iterator):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def render_pdf_first_page(pdf_path: Path, dpi_scale: float) -> bytes:
    document = fitz.open(pdf_path)
    try:
        page = document.load_page(0)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(dpi_scale, dpi_scale), alpha=False)
        return pixmap.tobytes("png")
    finally:
        document.close()


def build_data_url(file_path: Path, dpi_scale: float) -> tuple[str, str]:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        image_bytes = render_pdf_first_page(file_path, dpi_scale)
        return "data:image/png;base64," + base64.b64encode(image_bytes).decode("utf-8"), "pdf"

    mime = "image/jpeg" if suffix in {".jpg", ".jpeg"} else f"image/{suffix.lstrip('.')}"
    return "data:" + mime + ";base64," + base64.b64encode(file_path.read_bytes()).decode("utf-8"), "image"


def call_deepseek_ocr(
    *,
    api_key: str,
    model: str,
    data_url: str,
    timeout: int,
) -> str:
    prompts = [
        "这是中国发票。请直接提取关键字段，只返回简洁JSON："
        "company_name,seller_name,buyer_name,invoice_type,invoice_number,invoice_date,total_amount,tax_amount。"
        "缺失填null。",
        "这是中国发票、票据或报销凭证图片。请优先识别这些关键字段附近的文字："
        "发票类型、发票号码、开票日期、购买方名称、销售方名称、金额、税额、价税合计、备注。"
        "不要解释，不要总结，不要编造没有看见的字段。",
    ]
    last_content = ""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for prompt in prompts:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            "temperature": 0,
            "max_tokens": 500,
        }

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        last_content = data["choices"][0]["message"]["content"]
        if not looks_degenerate_ocr(last_content):
            return last_content

    return last_content


def looks_degenerate_ocr(content: str) -> bool:
    stripped = content.strip()
    if not stripped:
        return True
    if "{text}" in stripped or "} }" in stripped or "} {t}" in stripped:
        return True
    chinese_count = len(re.findall(r"[\u4e00-\u9fff]", stripped))
    digit_count = len(re.findall(r"\d", stripped))
    return chinese_count + digit_count < 12


def extract_pdf_text_fallback(pdf_path: Path) -> str:
    document = fitz.open(pdf_path)
    try:
        return "\n".join(page.get_text("text") for page in document)
    finally:
        document.close()


def normalize_ocr_text(content: str) -> str:
    text = content
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"</?(table|tr|td|th|tbody|thead|span|div|p)[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("\xa5", "￥")
    text = text.replace("\\u00a5", "￥")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def parse_json_like_text(text: str) -> dict | None:
    text = text.strip()
    if not text:
        return None

    candidates = []
    if text.startswith("{") and text.endswith("}"):
        candidates.append(text)

    fenced = re.findall(r"\{.*\}", text, flags=re.S)
    candidates.extend(fenced)

    for candidate in candidates:
        try:
            value = json.loads(candidate)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            continue
    return None


def clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip(" \n\r\t:：,，;；")
    value = re.sub(r"\s+", " ", value)
    if not value:
        return None
    if value.lower() in {"null", "none", "n/a", "unknown"}:
        return None
    return value


def normalize_amount(value: str | None) -> str | None:
    value = clean_value(value)
    if value is None:
        return None
    matched = re.search(r"(\d+(?:\.\d{1,2})?)", value.replace(",", ""))
    return matched.group(1) if matched else None


def split_meaningful_lines(text: str) -> list[str]:
    lines = [clean_value(line) for line in text.splitlines()]
    return [line for line in lines if line]


def extract_names(text: str) -> list[str]:
    names = []
    for match in re.finditer(r"名称[:：][ \t]*([^\n]+)", text):
        candidate = clean_value(match.group(1))
        if candidate:
            names.append(candidate)
    return names


def extract_company_candidates(lines: list[str]) -> list[str]:
    patterns = (
        "公司",
        "集团",
        "银行",
        "保险",
        "旅行社",
        "航空",
        "酒店",
        "科技",
        "商贸",
        "中心",
        "事务所",
    )
    candidates = []
    for line in lines:
        if any(token in line for token in patterns):
            if not re.fullmatch(r"[0-9A-Z]{10,}", line):
                candidates.append(line)
    return candidates


def extract_first(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I | re.S)
        if match:
            return clean_value(match.group(1))
    return None


def extract_all_amounts(text: str) -> list[str]:
    values = []
    for match in re.finditer(r"[￥¥]?\s*(\d+\.\d{1,2})", text):
        values.append(match.group(1))
    return values


def parse_invoice_fields_from_text(file_path: Path, text: str) -> InvoiceRecord:
    raw_json = parse_json_like_text(text)
    if raw_json:
        return InvoiceRecord(
            file_name=file_path.name,
            file_path=str(file_path.resolve()),
            file_type=file_path.suffix.lower().lstrip("."),
            company_name=clean_value(raw_json.get("company_name")),
            seller_name=clean_value(raw_json.get("seller_name")),
            buyer_name=clean_value(raw_json.get("buyer_name")),
            invoice_type=clean_value(raw_json.get("invoice_type")),
            invoice_number=clean_value(raw_json.get("invoice_number")),
            invoice_date=clean_value(raw_json.get("invoice_date")),
            total_amount=normalize_amount(raw_json.get("total_amount")),
            pretax_amount=normalize_amount(raw_json.get("pretax_amount")),
            tax_amount=normalize_amount(raw_json.get("tax_amount")),
            currency=clean_value(raw_json.get("currency")) or ("CNY" if "￥" in text or "¥" in text else None),
            summary=clean_value(raw_json.get("summary")),
        )

    lines = split_meaningful_lines(text)
    names = extract_names(text)
    company_candidates = extract_company_candidates(lines)

    invoice_number = extract_first(
        [
            r"发票号码[:：]?\s*([0-9]{8,})",
            r"票据号码[:：]?\s*([0-9]{8,})",
        ],
        text,
    )
    if invoice_number is None:
        for line in lines:
            if re.fullmatch(r"\d{12,}", line):
                invoice_number = line
                break

    invoice_date = extract_first(
        [
            r"开票日期[:：]?\s*([0-9]{4}[-/年.][0-9]{1,2}[-/月.][0-9]{1,2}[日]?)",
            r"日期[:：]?\s*([0-9]{4}[-/年.][0-9]{1,2}[-/月.][0-9]{1,2}[日]?)",
        ],
        text,
    )
    if invoice_date is None:
        for line in lines:
            if re.search(r"\d{4}(?:年|[-/.])\d{1,2}(?:月|[-/.])\d{1,2}日?", line):
                invoice_date = line
                break

    invoice_type = extract_first(
        [
            r"(电子普通发票)",
            r"(电子发票[（(]普通发票[）)])",
            r"(增值税专用发票)",
            r"(增值税普通发票)",
            r"(航空运输电子客票行程单)",
            r"(行程单)",
        ],
        text,
    )

    amount_lines = []
    currency_amounts = []
    for line in lines:
        amount = normalize_amount(line)
        if amount and ("￥" in line or "¥" in line or line == amount):
            amount_lines.append(amount)
        if amount and ("￥" in line or "¥" in line):
            currency_amounts.append(amount)

    total_amount = extract_first(
        [
            r"价税合计.*?[（(]小写[)）]\s*[￥¥]?\s*(\d+\.\d{1,2})",
            r"小写[)）]?\s*[￥¥]?\s*(\d+\.\d{1,2})",
            r"合计.*?[￥¥]\s*(\d+\.\d{1,2})",
        ],
        text,
    )
    if total_amount is None and len(amount_lines) >= 3:
        total_amount = amount_lines[-3]

    tax_amount = extract_first(
        [
            r"税额[:：]?\s*[￥¥]?\s*(\d+\.\d{1,2})",
            r"合计.*?[￥¥]\s*\d+\.\d{1,2}.*?[￥¥]\s*(\d+\.\d{1,2})",
        ],
        text,
    )
    if len(amount_lines) >= 1:
        tax_amount = amount_lines[-1]

    pretax_amount = extract_first(
        [
            r"金额[:：]?\s*[￥¥]?\s*(\d+\.\d{1,2})",
            r"合计.*?[￥¥]\s*(\d+\.\d{1,2})\s*[￥¥]\s*\d+\.\d{1,2}",
        ],
        text,
    )
    if len(amount_lines) >= 2:
        pretax_amount = amount_lines[-2]

    if len(currency_amounts) >= 2:
        numeric_amounts = [float(item) for item in currency_amounts]
        total_value = max(numeric_amounts)
        tax_value = min(numeric_amounts)
        pretax_value = round(total_value - tax_value, 2)
        total_amount = f"{total_value:.2f}"
        pretax_amount = f"{pretax_value:.2f}"
        tax_amount = f"{tax_value:.2f}"

    if total_amount is None:
        amounts = extract_all_amounts(text)
        if amounts:
            total_amount = amounts[-1]
        if len(amounts) >= 2 and pretax_amount is None:
            pretax_amount = amounts[-2]

    if len(names) < 2 and len(company_candidates) >= 2:
        names = company_candidates[:2]

    buyer_name = names[0] if len(names) >= 1 else None
    seller_name = names[1] if len(names) >= 2 else None
    company_name = seller_name or buyer_name or extract_first(
        [
            r"销售方[:：]?\s*([^\n]+)",
            r"购买方[:：]?\s*([^\n]+)",
        ],
        text,
    )
    summary = extract_first(
        [
            r"备注[:：]?\s*([^\n]+)",
            r"\*(.*?)\n",
            r"项目名称[:：]?\s*([^\n]+)",
        ],
        text,
    )

    parse_note = None
    parse_status = "ok"
    if not any([company_name, total_amount, invoice_number, invoice_date]):
        parse_status = "needs_review"
        parse_note = "OCR text was extracted, but key invoice fields were not confidently parsed."

    return InvoiceRecord(
        file_name=file_path.name,
        file_path=str(file_path.resolve()),
        file_type=file_path.suffix.lower().lstrip("."),
        company_name=clean_value(company_name),
        seller_name=clean_value(seller_name),
        buyer_name=clean_value(buyer_name),
        invoice_type=clean_value(invoice_type),
        invoice_number=clean_value(invoice_number),
        invoice_date=clean_value(invoice_date),
        total_amount=normalize_amount(total_amount),
        pretax_amount=normalize_amount(pretax_amount),
        tax_amount=normalize_amount(tax_amount),
        currency="CNY" if ("￥" in text or "¥" in text) else None,
        summary=clean_value(summary),
        parse_status=parse_status,
        parse_note=parse_note,
    )


def save_records(records: list[InvoiceRecord], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "invoice_results.json"
    csv_path = output_dir / "invoice_results.csv"

    payload = [asdict(record) for record in records]
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    fieldnames = list(payload[0].keys()) if payload else list(InvoiceRecord.__dataclass_fields__.keys())
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(payload)

    return json_path, csv_path


def main() -> None:
    args = parse_args()
    if not args.api_key:
        raise SystemExit(
            "Missing API key. Please set SILICONFLOW_API_KEY or pass --api-key."
        )

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    raw_dir = output_dir / "raw_ocr"
    raw_dir.mkdir(parents=True, exist_ok=True)

    files = list(iter_invoice_files(input_dir, args.recursive))
    if args.match:
        files = [file_path for file_path in files if args.match in file_path.name]
    if args.limit is not None:
        files = files[: args.limit]

    if not files:
        raise SystemExit(f"No supported files found in {input_dir}")

    records: list[InvoiceRecord] = []

    print(f"Found {len(files)} file(s) in {input_dir}")
    for index, file_path in enumerate(files, start=1):
        print(f"[{index}/{len(files)}] OCR processing {file_path.name} ...")
        try:
            data_url, file_type = build_data_url(file_path, args.dpi_scale)
            content = call_deepseek_ocr(
                api_key=args.api_key,
                model=args.model,
                data_url=data_url,
                timeout=args.timeout,
            )
            normalized_text = normalize_ocr_text(content)
            used_pdf_text_fallback = False

            if file_path.suffix.lower() == ".pdf" and looks_degenerate_ocr(normalized_text):
                fallback_text = normalize_ocr_text(extract_pdf_text_fallback(file_path))
                if not looks_degenerate_ocr(fallback_text):
                    normalized_text = fallback_text
                    used_pdf_text_fallback = True

            raw_text_path = raw_dir / f"{file_path.stem}.txt"
            raw_text_path.write_text(normalized_text, encoding="utf-8")

            record = parse_invoice_fields_from_text(file_path, normalized_text)
            record.file_type = file_type
            record.raw_ocr_text_file = str(raw_text_path.resolve())
            if used_pdf_text_fallback:
                record.parse_note = clean_value(
                    ((record.parse_note + " ") if record.parse_note else "")
                    + "DeepSeek OCR output was unstable, so the script fell back to embedded PDF text."
                )
            records.append(record)
        except Exception as exc:  # noqa: BLE001
            records.append(
                InvoiceRecord(
                    file_name=file_path.name,
                    file_path=str(file_path.resolve()),
                    file_type=file_path.suffix.lower().lstrip("."),
                    parse_status="error",
                    parse_note=str(exc),
                )
            )
            print(f"  error: {exc}")

    json_path, csv_path = save_records(records, output_dir)

    ok_count = sum(record.parse_status == "ok" for record in records)
    review_count = sum(record.parse_status == "needs_review" for record in records)
    error_count = sum(record.parse_status == "error" for record in records)

    print()
    print("Done.")
    print(f"JSON: {json_path}")
    print(f"CSV : {csv_path}")
    print(f"OK={ok_count}, NEEDS_REVIEW={review_count}, ERROR={error_count}")


if __name__ == "__main__":
    main()

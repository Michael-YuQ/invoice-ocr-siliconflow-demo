# 鍙戠エ OCR Demo

杩欐槸涓€涓€傚悎璇惧爞婕旂ず鍜屾湰鍦颁綋楠岀殑鍙戠エ OCR 灏忛」鐩紝鍖呭惈涓夐儴鍒嗭細

- `invoice_ocr_demo/run_invoice_ocr.py`
  鎵归噺鎵弿涓€涓枃浠跺す涓殑鍙戠エ PDF / 鍥剧墖锛岃皟鐢ㄧ鍩烘祦鍔?`deepseek-ai/DeepSeek-OCR`
- `invoice_ocr_demo/output/`
  宸茬粡鐢熸垚濂界殑绀轰緥 OCR 缁撴灉锛屾柟渚跨洿鎺ユ紨绀?- `index.html`
  绾潤鎬佹湰鍦扮粨鏋滅湅鏉匡紝鍙屽嚮鍗冲彲鎵撳紑锛屼笉闇€瑕?npm锛屼笉闇€瑕佹湰鍦版湇鍔?
浠撳簱閲岄檮甯︿簡鍑犱唤鐪熷疄鍙戠エ PDF 鏍蜂緥锛屾柟渚垮埆浜烘媺涓嬫潵鐩存帴浣撻獙銆?
## 蹇€熷紑濮?
### 1. 涓嬭浇椤圭洰

```powershell
git clone https://github.com/Michael-YuQ/invoice-ocr-siliconflow-demo.git
cd invoice-ocr-siliconflow-demo
```

鎴栬€呯洿鎺ュ湪 GitHub 椤甸潰鐐瑰嚮 `Code -> Download ZIP`銆?
### 2. 瀹夎 Python 渚濊禆

```powershell
python -m pip install -r invoice_ocr_demo/requirements.txt
```

### 3. 閰嶇疆纭呭熀娴佸姩 API Key

PowerShell:

```powershell
$env:SILICONFLOW_API_KEY=\"浣犵殑纭呭熀娴佸姩 API Key\"
```

涔熷彲浠ョ洿鎺ュ湪鍛戒护琛岄噷浼狅細

```powershell
python invoice_ocr_demo/run_invoice_ocr.py --input-dir . --api-key 浣犵殑Key
```

## 杩愯 OCR

### 澶勭悊褰撳墠鐩綍涓嬬殑鍙戠エ

```powershell
python invoice_ocr_demo/run_invoice_ocr.py --input-dir .
```

### 鍙鐞嗚鍗曞彂绁ㄦ牱渚?
```powershell
python invoice_ocr_demo/run_invoice_ocr.py --input-dir . --match 璁㈠崟
```

### 閫掑綊澶勭悊瀛愮洰褰?
```powershell
python invoice_ocr_demo/run_invoice_ocr.py --input-dir . --recursive
```

OCR 杈撳嚭浼氬啓鍒帮細

- `invoice_ocr_demo/output/invoice_results.json`
- `invoice_ocr_demo/output/invoice_results.csv`
- `invoice_ocr_demo/output/raw_ocr/*.txt`

## 鏈湴鏌ョ湅缁撴灉

鐩存帴鍙屽嚮锛?
- `index.html`

杩欎釜椤甸潰鏄函闈欐€侀〉闈細

- 涓嶉渶瑕?npm
- 涓嶉渶瑕佸惎鍔ㄦ湇鍔?- 涓嶉渶瑕佸畨瑁呭墠绔緷璧?
鎵撳紑鍚庝細鍏堟樉绀轰粨搴撻噷鑷甫鐨?OCR 绀轰緥缁撴灉銆?
濡傛灉浣犻噸鏂拌窇浜嗕竴閬?OCR锛屽彲浠ュ湪椤甸潰閲岀偣鍑伙細

- `鍔犺浇鏈€鏂?JSON`
- `鍔犺浇鍘熷 TXT`

鐒跺悗閫夋嫨锛?
- `invoice_ocr_demo/output/invoice_results.json`
- `invoice_ocr_demo/output/raw_ocr/*.txt`

椤甸潰灏变細鏇存柊鎴愪綘鍒氱敓鎴愮殑缁撴灉銆?
## 浠撳簱閲屽寘鍚殑鏍蜂緥

鍏紑鏍蜂緥涓昏鍖呮嫭锛?
- `璁㈠崟1128145044857135-鐢靛瓙鏅€氬彂绁?pdf`
- `璁㈠崟1128145044857135-鐢靛瓙鏅€氬彂绁?淇濋櫓.pdf`
- `璁㈠崟1128145144721583-鐢靛瓙鏅€氬彂绁?pdf`
- `璁㈠崟1128145144721583-鐢靛瓙鏅€氬彂绁?淇濋櫓.pdf`

浠ュ強瀵瑰簲鐨?OCR 缁撴灉鏂囦欢銆?
## 璇存槑

- 杩欎釜椤圭洰涓嶄細涓婁紶浣犵殑纭呭熀娴佸姩 API Key
- 杩愯鏃堕渶瑕佷綘鑷繁閰嶇疆 `SILICONFLOW_API_KEY`
- 褰撳墠鑴氭湰浼樺厛璧?DeepSeek OCR锛涘鏋?PDF 鐨?OCR 杈撳嚭寮傚父锛屼細鍥為€€鍒?PDF 鍐呭祵鏂囨湰鎶藉彇锛屼互淇濊瘉璇惧爞婕旂ず鏇寸ǔ瀹?


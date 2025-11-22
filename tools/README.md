# Tools

**(Tiếng Việt bên dưới)**

Extraction and repacking tools for game localization files.

## Tools

### 1. `extract_language_files.py`

Extract texts from game language binary files. Automatically handles `_diff` files if present (merges into main texts).

**Usage:**
```bash
conda activate wwm_localization
python tools/extract_language_files.py
```

**Output:**
- Individual language JSON files (e.g., `translation/en.json`, `translation/cn.json`)
- `translation/translation_template.json` - Combined template with all extracted languages plus `Target` column

**Options:**
- `--source-dir`: Directory containing source language files (default: `language/source`)
- `--mod-dir`: Directory containing edited mod language files (default: `language/mod`)
- `--output-dir`: Output directory (default: `translation`)
- `--languages`: Languages to extract, space-separated (default: `en cn ko ja`)

**Notes:**
- Tool automatically finds and merges `_diff` files (e.g., `translate_words_map_en_diff`) into main files
- Most languages follow standard pattern: `translate_words_map_{lang_code}`
- Special cases: `cn` → `translate_words_map_zh_cn`, `tw` → `translate_words_map_zh_tw`
- Field names in template are automatically mapped (e.g., `en` → `English`, `cn` → `Chinese`)

### 2. `repack_translations.py`

Repack translations from JSON template back to binary format.
**IMPORTANT**: Tool automatically creates `_diff` file (required) for game compatibility.

**Usage:**
```bash
conda activate wwm_localization
python tools/repack_translations.py \
  --template translation/translation_template.json \
  --source-binary language/source/translate_words_map_zh_cn \
  --output-binary language/mod/translate_words_map_target \
  --official-binary language/source/translate_words_map_zh_cn
```

**Options:**
- `--template`: Translation template JSON file (default: `translation/translation_template.json`)
- `--source-binary`: Source binary file used as template (default: `language/source/translate_words_map_zh_cn`)
- `--official-binary`: Official binary file for diff comparison (default: `language/source/translate_words_map_zh_cn`)
- `--output-binary`: Output binary file (default: `language/mod/translate_words_map_target`)
- `--output-diff`: Output diff binary file (default: `output_binary` + `_diff`)
- `--temp-dir`: Temporary directory (default: `temp_repack`)
- `--mode`: Translation mode (default: `autofill`)
  - `target`: Use only target column (skip entries if empty)
  - `autofill`: Use target column, fallback to autofill column for empty entries
- `--target-column`: Column name to use as primary translation source (default: `Target`)
- `--autofill-column`: Column name to use for autofill when target is empty (default: `English`)

**Output:**
- `language/mod/translate_words_map_target` - Modded binary file (full)
- `language/mod/translate_words_map_target_diff` - Diff file (required by game engine)

**Game Compatibility:**
- The `_diff` file is required by the game engine for version synchronization
- Tool automatically copies official `_diff` file for verification
- If official diff doesn't exist, tool creates a minimal diff file
- Game engine automatically merges `_diff` into main file when loading

## Workflow

1. **Extract**: Run `extract_language_files.py` to create template
2. **Translate**: Use UI to edit `translation/translation_template.json`, fill in `Target` field
3. **Repack**: Run `repack_translations.py` to create modded binary
4. **Install**: Copy binary files to game directory

---

## Tiếng Việt

# Công cụ

Công cụ trích xuất và đóng gói lại file dịch thuật của game.

## Công cụ

### 1. `extract_language_files.py`

Trích xuất văn bản từ file binary ngôn ngữ của game. Tự động xử lý file `_diff` nếu có (gộp vào văn bản chính).

**Cách sử dụng:**
```bash
conda activate wwm_localization
python tools/extract_language_files.py
```

**Kết quả:**
- Các file JSON ngôn ngữ riêng lẻ (ví dụ: `translation/en.json`, `translation/cn.json`)
- `translation/translation_template.json` - Template kết hợp với tất cả ngôn ngữ đã trích xuất cộng cột `Target`

**Tùy chọn:**
- `--source-dir`: Thư mục chứa file ngôn ngữ nguồn (mặc định: `language/source`)
- `--mod-dir`: Thư mục chứa file mod đã chỉnh sửa (mặc định: `language/mod`)
- `--output-dir`: Thư mục output (mặc định: `translation`)
- `--languages`: Ngôn ngữ cần trích xuất, cách nhau bằng khoảng trắng (mặc định: `en cn ko ja`)

**Lưu ý:**
- Công cụ tự động tìm và gộp file `_diff` (ví dụ: `translate_words_map_en_diff`) vào file chính
- Hầu hết ngôn ngữ theo pattern chuẩn: `translate_words_map_{mã_ngôn_ngữ}`
- Trường hợp đặc biệt: `cn` → `translate_words_map_zh_cn`, `tw` → `translate_words_map_zh_tw`
- Tên field trong template được map tự động (ví dụ: `en` → `English`, `cn` → `Chinese`)

### 2. `repack_translations.py`

Đóng gói lại bản dịch từ template JSON về định dạng binary.
**QUAN TRỌNG**: Công cụ tự động tạo file `_diff` (bắt buộc) để tương thích với game.

**Cách sử dụng:**
```bash
conda activate wwm_localization
python tools/repack_translations.py \
  --template translation/translation_template.json \
  --source-binary language/source/translate_words_map_zh_cn \
  --output-binary language/mod/translate_words_map_target \
  --official-binary language/source/translate_words_map_zh_cn
```

**Tùy chọn:**
- `--template`: File template JSON dịch thuật (mặc định: `translation/translation_template.json`)
- `--source-binary`: File binary nguồn dùng làm template (mặc định: `language/source/translate_words_map_zh_cn`)
- `--official-binary`: File binary chính thức để so sánh diff (mặc định: `language/source/translate_words_map_zh_cn`)
- `--output-binary`: File binary output (mặc định: `language/mod/translate_words_map_target`)
- `--output-diff`: File binary diff output (mặc định: `output_binary` + `_diff`)
- `--temp-dir`: Thư mục tạm (mặc định: `temp_repack`)
- `--mode`: Chế độ dịch thuật (mặc định: `autofill`)
  - `target`: Chỉ sử dụng cột target (bỏ qua mục nếu trống)
  - `autofill`: Sử dụng cột target, fallback sang cột autofill nếu target trống
- `--target-column`: Tên cột dùng làm nguồn dịch chính (mặc định: `Target`)
- `--autofill-column`: Tên cột dùng để autofill khi target trống (mặc định: `English`)

**Kết quả:**
- `language/mod/translate_words_map_target` - File binary mod (đầy đủ)
- `language/mod/translate_words_map_target_diff` - File diff (bắt buộc bởi game engine)

**Tương thích Game:**
- File `_diff` bắt buộc bởi game engine để đồng bộ phiên bản
- Công cụ tự động sao chép file `_diff` chính thức để xác minh
- Nếu diff chính thức không tồn tại, công cụ tạo file diff tối thiểu
- Game engine tự động gộp `_diff` vào file chính khi load

## Quy trình làm việc

1. **Extract**: Chạy `extract_language_files.py` để tạo template
2. **Translate**: Dùng UI để chỉnh sửa `translation/translation_template.json`, điền vào field `Target`
3. **Repack**: Chạy `repack_translations.py` để tạo binary mod
4. **Install**: Sao chép file binary vào thư mục game

# Where Winds Meet - Localization Tools

**(Tiếng Việt bên dưới)**

Tools to extract and repack language files for **Where Winds Meet** game for localization.

## Setup

### Conda Environment

```bash
conda env create -f environment.yml
conda activate wwm_localization
```

## Quick Start

### 1. Extract

Extract texts from game language files:

```bash
# Extract default languages (en, cn, ko, ja)
python tools/extract_language_files.py

# Extract custom languages
python tools/extract_language_files.py --languages en cn ko ja de fr
```

**Output:**
- Individual language JSON files in `translation/` directory
- `translation/translation_template.json` - Combined template with all languages

**Snippet of output structure:**
```json
[
  {
    "ID": "867e8190fa194d0f",
    "English": "You want to know? Then why don't... I hand over the duties of Huaixin Station to you?",
    "Chinese": "你想知道？那不如……怀信驿的任务，也交给你来做？",
    "Korean": "알고 싶어요? 그럼... 회신역 임무도 당신이 맡는 게 어때요?",
    "Japanese": "知りたい？ だったら…懐信の宿場の任務も任せていい？",
    "French": "Vous voulez savoir ? Alors pourquoi ne pas... vous confier les responsabilités de la Station Huaixin ?",
    "Target": ""
  },
  {
    "ID": "867e88904131715a",
    "English": "Sky Lantern Ambience",
    "Chinese": "绘影寄情氛围",
    "Korean": "다정한 그림 분위기",
    "Japanese": "春節の夢",
    "French": "Ambiance des Lanternes Célestes",
    "Target": ""
  }
]
```

### 2. Repack

Repack translations back to binary format:

```bash
# Repack with autofill from a specific column
python tools/repack_translations.py --mode autofill --autofill-column English --target-column Target

# Repack using only target column
python tools/repack_translations.py --mode target --target-column Target
```

**Output:**
- `language/mod/translate_words_map_target` - Main binary file
- `language/mod/translate_words_map_target_diff` - Diff file (required by game)

### 3. Rename and Install

1. **Rename the output files** to a language code that you don't use in the game (recommended):
   - `translate_words_map_target` → `translate_words_map_<unused_lang_code>`
   - `translate_words_map_target_diff` → `translate_words_map_<unused_lang_code>_diff`
   
   **Example:** If you don't use German:
   - `translate_words_map_target` → `translate_words_map_de`
   - `translate_words_map_target_diff` → `translate_words_map_de_diff`
   
2. **Copy both files** to the game's language directory:
   
   **For Client:**
   ```
   \wwm\wwm_standard\LocalData\Patch\HD\oversea\locale\
   ```
   
   **For Steam:**
   ```
   \SteamLib\steamapps\common\Where Winds Meet\
   ```
   (Navigate to the `locale` subdirectory within the game folder)

3. **In-game:** Switch the game language to the language code you renamed the files to (e.g., if you renamed to `de`, switch to German in game settings)

## Disclaimer

**⚠️ IMPORTANT:** Modifying game files may:
- Violate the game's Terms of Service
- Trigger anti-cheat systems
- Cause game instability or crashes
- Result in account penalties or bans

**Use at your own risk.** Always:
- Backup original game files before replacing them
- Test modded files in a safe environment first
- Be aware that game updates may break compatibility
- Understand that you are responsible for any consequences

This tool is provided for educational and localization purposes. The authors are not responsible for any issues arising from the use of modified game files.

## Translation Template

The `translation_template.json` file contains:
- `ID`: Unique identifier for each text entry
- Language columns: `English`, `Chinese`, `Korean`, `Japanese`, etc. (based on extracted languages)
- `Target`: Column for your translations (fill this with your translated text)

## Project Structure

```
.
├── language/
│   ├── source/            # Source language files from game
│   └── mod/               # Repacked translation files (output)
├── translation/           # Extracted JSON translation files
│   └── translation_template.json # (heavy file, please run the code locally)
├── tools/                 # Extraction and repacking tools
└── requirements.txt       # Python dependencies
```

## Notes

- The `_diff` file is automatically created and required by the game engine
- Tools automatically handle `_diff` files when extracting (merge into main texts)
- Default autofill column is `English`

---

## Tiếng Việt

# Where Winds Meet - Công cụ Dịch thuật

Công cụ extract và repack file ngôn ngữ để Việt Hóa cho game **Where Winds Meet**.

## Thiết lập

### Conda Environment

```bash
conda env create -f environment.yml
conda activate wwm_localization
```

## Hướng dẫn nhanh

### 1. Extract

Trích xuất văn bản từ file ngôn ngữ của game:

```bash
# Trích xuất ngôn ngữ mặc định (en, cn, ko, ja)
python tools/extract_language_files.py

# Trích xuất ngôn ngữ tùy chỉnh
python tools/extract_language_files.py --languages en cn ko ja de fr
```

**Kết quả:**
- Các file JSON ngôn ngữ riêng lẻ trong thư mục `translation/`
- `translation/translation_template.json` - Template kết hợp với tất cả ngôn ngữ

**Ví dụ cấu trúc output:**
```json
[
  {
    "ID": "867e8190fa194d0f",
    "English": "You want to know? Then why don't... I hand over the duties of Huaixin Station to you?",
    "Chinese": "你想知道？那不如……怀信驿的任务，也交给你来做？",
    "Korean": "알고 싶어요? 그럼... 회신역 임무도 당신이 맡는 게 어때요?",
    "Japanese": "知りたい？ だったら…懐信の宿場の任務も任せていい？",
    "French": "Vous voulez savoir ? Alors pourquoi ne pas... vous confier les responsabilités de la Station Huaixin ?",
    "Target": ""
  },
  {
    "ID": "867e88904131715a",
    "English": "Sky Lantern Ambience",
    "Chinese": "绘影寄情氛围",
    "Korean": "다정한 그림 분위기",
    "Japanese": "春節の夢",
    "French": "Ambiance des Lanternes Célestes",
    "Target": ""
  }
]
```

### 2. Repack

Đóng gói lại bản dịch về định dạng binary:

```bash
# Repack với autofill từ một cột cụ thể
python tools/repack_translations.py --mode autofill --autofill-column English --target-column Target

# Repack chỉ sử dụng cột target
python tools/repack_translations.py --mode target --target-column Target
```

**Kết quả:**
- `language/mod/translate_words_map_target` - File binary chính
- `language/mod/translate_words_map_target_diff` - File diff (bắt buộc bởi game)

### 3. Đổi tên và Cài đặt

1. **Đổi tên file output** thành mã ngôn ngữ mà bạn không đang sử dụng trong game:
   - `translate_words_map_target` → `translate_words_map_<mã_ngôn_ngữ_không_dùng>`
   - `translate_words_map_target_diff` → `translate_words_map_<mã_ngôn_ngữ_không_dùng>_diff`
   
   **Ví dụ:** Nếu bạn không dùng tiếng Đức:
   - `translate_words_map_target` → `translate_words_map_de`
   - `translate_words_map_target_diff` → `translate_words_map_de_diff`

2. **Sao chép cả hai file** vào thư mục ngôn ngữ của game:
   
   **Đối với phiên bản Client:**
   ```
   \wwm\wwm_standard\LocalData\Patch\HD\oversea\locale\
   ```
   
   **Đối với phiên bản Steam:**
   ```
   \SteamLib\steamapps\common\Where Winds Meet\
   ```
   (Điều hướng đến thư mục con `locale` trong thư mục game)

3. **Trong game:** Chuyển ngôn ngữ game sang mã ngôn ngữ mà bạn đã đổi tên file (ví dụ: nếu đổi tên thành `de`, chuyển sang tiếng Đức trong cài đặt game)

## Lưu ý Quan trọng

**⚠️ QUAN TRỌNG:** Việc chỉnh sửa file game có thể:
- Vi phạm Điều khoản Dịch vụ của game
- Kích hoạt hệ thống chống gian lận
- Gây mất ổn định hoặc crash game
- Dẫn đến phạt tài khoản hoặc ban

**Sử dụng có rủi ro.** Luôn luôn:
- Sao lưu file game gốc trước khi thay thế
- Test file mod trong môi trường an toàn trước
- Lưu ý rằng cập nhật game có thể làm mất tương thích
- Hiểu rằng bạn chịu trách nhiệm cho mọi hậu quả

Công cụ này được cung cấp cho mục đích giáo dục và dịch thuật. Tác giả không chịu trách nhiệm cho bất kỳ vấn đề nào phát sinh từ việc sử dụng file game đã chỉnh sửa.

## Template Dịch thuật

File `translation_template.json` chứa:
- `ID`: Mã định danh duy nhất cho mỗi mục văn bản
- Các cột ngôn ngữ: `English`, `Chinese`, `Korean`, `Japanese`, v.v. (dựa trên ngôn ngữ đã trích xuất)
- `Target`: Cột cho bản dịch của bạn (điền bản dịch vào đây)

## Cấu trúc Dự án

```
.
├── language/
│   ├── source/            # File ngôn ngữ nguồn từ game
│   └── mod/               # File dịch đã đóng gói (output)
├── translation/           # File JSON dịch đã trích xuất
│   └── translation_template.json # (File nặng, vui lòng chạy code locally)
├── tools/                 # Công cụ trích xuất và đóng gói
└── requirements.txt       # Python dependencies
```

## Lưu ý

- File `_diff` được tạo tự động và bắt buộc bởi game engine
- Công cụ tự động xử lý file `_diff` khi trích xuất (gộp vào văn bản chính)
- Cột autofill mặc định là `English` (ngôn ngữ phổ quát)

#!/usr/bin/env python3
"""
Extract texts from game language files.
Outputs JSON files for each language and a combined translation template.
"""

import os
import sys
import struct
import json
import pyzstd

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def extract_file_to_dat(input_file, output_dir):
    """Extract binary file to .dat files."""
    try:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        os.makedirs(output_dir, exist_ok=True)

        with open(input_file, 'rb') as f:
            if f.read(4) != b'\xEF\xBE\xAD\xDE':
                return False

            f.read(4)  # Version
            offset_count_bytes = f.read(4)
            offset_count = struct.unpack('<I', offset_count_bytes)[0] + 1

            if offset_count == 1:
                comp_block_len = struct.unpack('<I', f.read(4))[0]
                comp_block = f.read(comp_block_len)

                if len(comp_block) < comp_block_len:
                    return False

                header = comp_block[:9]
                comp_data_part = comp_block[9:]

                if len(header) < 9:
                    return False
                    
                comp_type, comp_size, decomp_size = struct.unpack('<BII', header)

                if comp_type == 0x04:
                    try:
                        decomp_data = pyzstd.decompress(comp_data_part)
                        output_path = os.path.join(output_dir, f"{base_name}_0.dat")
                        with open(output_path, 'wb') as out_f:
                            out_f.write(decomp_data)
                        return True
                    except Exception:
                        return False
            else:
                offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(offset_count)]
                data_start = f.tell()
                
                extracted = 0
                for i in range(offset_count):
                    current_offset = offsets[i]
                    if i == (offset_count - 1):
                        continue
                    else:
                        next_offset = offsets[i + 1]
                    
                    block_len = next_offset - current_offset
                    f.seek(data_start + current_offset)
                    comp_block = f.read(block_len)

                    if len(comp_block) < block_len or len(comp_block) < 9:
                        continue

                    header = comp_block[:9]
                    comp_data_part = comp_block[9:]
                    comp_type, comp_size, decomp_size = struct.unpack('<BII', header)
                    
                    if comp_type == 0x04:
                        try:
                            decomp_data = pyzstd.decompress(comp_data_part)
                            output_path = os.path.join(output_dir, f"{base_name}_{i}.dat")
                            with open(output_path, 'wb') as out_f:
                                out_f.write(decomp_data)
                            extracted += 1
                        except Exception:
                            pass

                return extracted > 0

    except Exception:
        return False

def extract_texts_from_dat(dat_dir):
    """Extract texts from .dat files, return dict {id: text}."""
    texts = {}
    
    for filename in os.listdir(dat_dir):
        if filename.endswith('.dat'):
            full_path = os.path.join(dat_dir, filename)
            
            try:
                with open(full_path, 'rb') as f:
                    f.seek(16)
                    
                    if f.read(4) != b'\xDC\x96\x58\x59':
                        continue
                    
                    f.seek(0)
                    count_full = struct.unpack('<I', f.read(4))[0]
                    f.read(4)  # Padding (position 4-7)
                    count_text = struct.unpack('<I', f.read(4))[0]
                    f.read(12)  # Padding (4 bytes) + Marker (4 bytes) + Padding (4 bytes) = 12 bytes total
                    # After reading 12 bytes from position 12, we're at position 24
                    # Code block starts at position 24 (current position)
                    code = f.read(count_full).hex()  # Read code block and convert to hex (from position 24)
                    f.read(17)  # Padding
                    data_start = f.tell()  # Should be 24 + count_full + 17
                    
                    for i in range(count_full):
                        f.seek(data_start + (i * 16))
                        id_hex = f.read(8).hex()
                        # Skip entry with all-zero ID (likely metadata/header entry)
                        if id_hex == '0000000000000000':
                            continue
                        start_text_offset = f.tell()  # Position after reading ID (8 bytes)
                        offset_text = struct.unpack('<I', f.read(4))[0]
                        lenght = struct.unpack('<I', f.read(4))[0]
                        # offset_text is relative to start_text_offset (where offset is stored)
                        # So text position = start_text_offset + offset_text
                        f.seek(start_text_offset + offset_text)
                        text = f.read(lenght).decode('utf-8', errors='ignore')
                        # Remove NULL bytes and DEL character
                        text = text.replace('\x00', '').replace('\x7f', '')
                        # Remove other control characters (keep only printable chars, newline, carriage return, tab)
                        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
                        # Skip if only control characters remain
                        if not text.strip():
                            # Keep empty entries but mark as empty (needed for template)
                            if id_hex not in texts:
                                texts[id_hex] = ''
                        else:
                            # No need to escape for JSON - JSON handles special characters automatically
                            if id_hex not in texts or not texts[id_hex]:
                                texts[id_hex] = text
            except Exception:
                continue
    
    return texts

def extract_language_file(input_file, language_code, output_dir, diff_file=None):
    """Extract a single language file from binary format.
    
    Args:
        input_file: Main binary file path
        language_code: Language code for naming
        output_dir: Output directory
        diff_file: Optional diff file path to merge
    """
    temp_dir = os.path.join(output_dir, f"temp_{language_code}")
    os.makedirs(temp_dir, exist_ok=True)
    
    print(f"   Extracting {language_code}...")
    if not extract_file_to_dat(input_file, temp_dir):
        print(f"   ❌ Failed to extract {language_code}")
        return None
    
    print(f"   Extracting texts from {language_code}...")
    texts = extract_texts_from_dat(temp_dir)
    print(f"   ✅ Found {len(texts)} texts")
    
    # Extract and merge diff file if provided
    if diff_file and os.path.exists(diff_file):
        # Check if file is not empty (more than just header)
        file_size = os.path.getsize(diff_file)
        if file_size > 16:  # More than just magic + version + offset_count + comp_block_len
            print(f"   Extracting {language_code} diff...")
            diff_temp_dir = os.path.join(output_dir, f"temp_{language_code}_diff")
            os.makedirs(diff_temp_dir, exist_ok=True)
            if extract_file_to_dat(diff_file, diff_temp_dir):
                diff_texts = extract_texts_from_dat(diff_temp_dir)
                if diff_texts:
                    print(f"   ✅ Found {len(diff_texts)} diff texts")
                    # Merge diff texts into main texts (diff overrides main)
                    texts.update(diff_texts)
                    print(f"   ✅ Merged: {len(texts)} total texts")
                else:
                    # Diff file may be a placeholder (copied from official for verification)
                    # This is common in modding to pass game file verification
                    print(f"   ℹ️  Diff file exists but contains no texts (may be verification placeholder)")
                import shutil
                shutil.rmtree(diff_temp_dir, ignore_errors=True)
            else:
                # Diff file may have non-ZSTD blocks (e.g., comp_type 0) used for verification
                # This is normal for modded diff files copied from official
                print(f"   ℹ️  Diff file cannot be extracted (likely verification placeholder from official)")
        else:
            print(f"   ℹ️  Diff file exists but is empty (no changes from official)")
    
    # Cleanup temp directory
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    return texts

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract texts from game language files')
    parser.add_argument('--source-dir', default='language/source',
                       help='Directory containing source language files')
    parser.add_argument('--mod-dir', default='language/mod',
                       help='Directory containing edited mod language files')
    parser.add_argument('--output-dir', default='translation',
                       help='Output directory for JSON files')
    parser.add_argument('--languages', nargs='+', default=['en', 'cn', 'ko', 'ja'],
                       help='Languages to extract (default: en cn ko ja)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Extract Language Files")
    print("=" * 60)
    print()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Language code to filename mapping (special cases that don't follow standard pattern)
    # Most languages follow: translate_words_map_{lang_code}
    # Special cases:
    lang_map_special = {
        'cn': 'translate_words_map_zh_cn',  # Chinese simplified
        'tw': 'translate_words_map_zh_tw',  # Chinese traditional
    }
    
    # Extract all requested languages
    extracted_texts = {}
    for lang_code in args.languages:
        # Use special mapping if exists, otherwise use standard pattern
        if lang_code in lang_map_special:
            filename = lang_map_special[lang_code]
        else:
            # Standard pattern: translate_words_map_{lang_code}
            filename = f'translate_words_map_{lang_code}'
        main_file = os.path.join(args.source_dir, filename)
        diff_file = os.path.join(args.source_dir, f"{filename}_diff")
        
        if os.path.exists(main_file):
            lang_key = lang_code
            texts = extract_language_file(
                main_file, lang_code, args.output_dir,
                diff_file=diff_file if os.path.exists(diff_file) else None
            )
            if texts:
                extracted_texts[lang_key] = texts
                # Save individual language file
                output_filename = f"{lang_key}.json"
                output_file = os.path.join(args.output_dir, output_filename)
                data = [{"ID": id_hex, "Text": text} for id_hex, text in sorted(texts.items())]
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"   💾 Saved: {output_file}\n")
        else:
            print(f"   ⚠️  {lang_code} file not found: {main_file}\n")
    
    # Create combined template
    print("📝 Creating translation template...")
    # Collect all IDs from extracted languages
    all_ids = set()
    for texts in extracted_texts.values():
        all_ids.update(texts.keys())
    
    # Build template with all languages
    # Field name mapping (default to capitalized lang_code if not specified)
    field_names = {
        'en': 'English',
        'cn': 'Chinese',
        'ko': 'Korean',
        'ja': 'Japanese',
        'vi': 'Vietnamese',
        'de': 'German',
        'fr': 'French',
        'es': 'Spanish',
        'tw': 'Chinese_Traditional'
    }
    
    template_file = os.path.join(args.output_dir, "translation_template.json")
    data = []
    for id_hex in sorted(all_ids):
        entry = {"ID": id_hex}
        
        # Add all extracted languages
        for lang_key, texts in extracted_texts.items():
            # Use mapped name if exists, otherwise capitalize the lang_key
            field_name = field_names.get(lang_key, lang_key.title())
            entry[field_name] = texts.get(id_hex, '')
        
        # Add Target column (empty by default, to be filled by translators)
        entry["Target"] = ''
        
        data.append(entry)
    
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 Saved: {template_file}")
    print(f"   ✅ Total entries: {len(all_ids):,}")
    print()

if __name__ == "__main__":
    main()

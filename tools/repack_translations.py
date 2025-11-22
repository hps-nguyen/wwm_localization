#!/usr/bin/env python3
"""
Repack translations from JSON back to binary file.
Reads translation_template.json and creates modded binary file.
"""

import os
import sys
import struct
import csv
import json
import pyzstd
import re
import shutil

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
                header = comp_block[:9]
                comp_data_part = comp_block[9:]
                comp_type, comp_size, decomp_size = struct.unpack('<BII', header)

                if comp_type == 0x04:
                    decomp_data = pyzstd.decompress(comp_data_part)
                    output_path = os.path.join(output_dir, f"{base_name}_0.dat")
                    with open(output_path, 'wb') as out_f:
                        out_f.write(decomp_data)
                    return True
            else:
                offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(offset_count)]
                data_start = f.tell()
                
                extracted = 0
                for i in range(offset_count):
                    current_offset = offsets[i]
                    if i == (offset_count - 1):
                        continue
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

def extract_official_texts(official_dat_dir):
    """Extract original texts from official .dat files."""
    official_texts = {}
    
    for filename in os.listdir(official_dat_dir):
        if not filename.endswith('.dat'):
            continue
        
        input_path = os.path.join(official_dat_dir, filename)
        try:
            with open(input_path, 'rb') as f:
                f.seek(16)
                if f.read(4) != b'\xDC\x96\x58\x59':
                    continue
                
                f.seek(0)
                count_full = struct.unpack('<I', f.read(4))[0]
                f.read(4)
                count_text = struct.unpack('<I', f.read(4))[0]
                f.read(12)
                f.read(count_full)  # Code block
                f.read(17)
                data_start = f.tell()
                
                for i in range(count_full):
                    f.seek(data_start + (i * 16))
                    id_hex = f.read(8).hex()
                    start_text_offset = f.tell()
                    offset_text = struct.unpack('<I', f.read(4))[0]
                    lenght = struct.unpack('<I', f.read(4))[0]
                    f.seek(start_text_offset + offset_text)
                    text = f.read(lenght).decode('utf-8', errors='ignore')
                    
                    if id_hex not in official_texts:
                        official_texts[id_hex] = text
        except Exception:
            continue
    
    return official_texts

def pack_text_to_dat(json_file, source_dat_dir, output_dat_dir, mode='autofill', target_column='Target', autofill_column='English', official_dat_dir=None, diff_output_dir=None):
    """Pack text from JSON to .dat files.
    
    Args:
        mode: 'target' or 'autofill'
            - 'target': Use only target_column (skip if empty)
            - 'autofill': Use target_column, fallback to autofill_column if empty
        target_column: Column name to use as primary translation source (default: 'Target')
        autofill_column: Column name to use for autofill when target is empty (default: 'English')
        official_dat_dir: Directory containing official .dat files (for diff comparison)
        diff_output_dir: Output directory for diff .dat files (only changed entries)
    """
    # Read translations from JSON
    translations = {}
    target_count = 0
    autofill_count = 0
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for row in data:
            id_hex = (row.get('ID') or '').strip()
            if not id_hex:
                continue
            target_text = (row.get(target_column) or '').strip()
            autofill_text = (row.get(autofill_column) or '').strip()
            
            if mode == 'target':
                # Use only target column (skip if empty)
                if target_text:
                    translations[id_hex] = target_text
                    target_count += 1
            else:  # autofill
                # Use target if available, otherwise use autofill
                if target_text:
                    translations[id_hex] = target_text
                    target_count += 1
                elif autofill_text:
                    translations[id_hex] = autofill_text
                    autofill_count += 1
    
    print(f"📝 Loaded {len(translations)} translations")
    if mode == 'autofill':
        print(f"   - Target ({target_column}): {target_count}")
        print(f"   - Autofill ({autofill_column}): {autofill_count}")
    else:
        print(f"   - Target ({target_column}) only: {target_count}")
    
    if not translations:
        print("⚠️  No translations found!")
        return False
    
    # Extract official texts for diff comparison
    official_texts = {}
    if official_dat_dir and os.path.exists(official_dat_dir):
        print("📋 Extracting official texts for diff comparison...")
        official_texts = extract_official_texts(official_dat_dir)
        print(f"   ✅ Found {len(official_texts)} official texts")
    
    # Calculate diff (only entries that differ from official)
    diff_translations = {}
    if official_texts and diff_output_dir:
        for id_hex, translated_text in translations.items():
            official_text = official_texts.get(id_hex, '')
            # Only include if different from official
            if translated_text != official_text:
                diff_translations[id_hex] = translated_text
        print(f"📊 Diff: {len(diff_translations)} entries differ from official")
    
    # Process each .dat file
    os.makedirs(output_dat_dir, exist_ok=True)
    if diff_output_dir:
        os.makedirs(diff_output_dir, exist_ok=True)
    
    for filename in os.listdir(source_dat_dir):
        if not filename.endswith('.dat'):
            continue
        
        input_path = os.path.join(source_dat_dir, filename)
        output_path = os.path.join(output_dat_dir, filename)
        
        try:
            with open(input_path, 'rb') as f:
                # Check for marker first
                f.seek(16)
                if f.read(4) != b'\xDC\x96\x58\x59':
                    f.seek(0)
                    with open(output_path, 'wb') as out_f:
                        out_f.write(f.read())
                    continue
                
                # Read structure (matching Russian code exactly)
                f.seek(0)
                count_full = struct.unpack('<I', f.read(4))[0]
                f.read(4)
                count_text = struct.unpack('<I', f.read(4))[0]
                f.read(12)  # padding + marker + padding (12 bytes total, brings us to position 24)
                code = f.read(count_full).hex()  # Read code block from position 24
                f.read(17)  # Padding
                data_start = f.tell()
                
                entries = []
                for i in range(count_full):
                    f.seek(data_start + (i * 16))
                    id_hex = f.read(8).hex()
                    start_text_offset = f.tell()
                    offset_text = struct.unpack('<I', f.read(4))[0]
                    lenght = struct.unpack('<I', f.read(4))[0]
                    f.seek(start_text_offset + offset_text)
                    original_text = f.read(lenght).decode('utf-8', errors='ignore')
                    entries.append({
                        'id': id_hex,
                        'offset': offset_text,
                        'length': lenght,
                        'text': original_text
                    })
                
                # Build new file (following Russian code logic)
                # Structure:
                # 0-3: count_full (4 bytes)
                # 4-7: padding (4 bytes) = 0
                # 8-11: count_text (4 bytes)
                # 12-15: padding (4 bytes) = 0
                # 16-19: marker (4 bytes) = \xDC\x96\x58\x59
                # 20-23: padding (4 bytes) = 0
                # 24-24+count_full-1: code block (count_full bytes)
                # 24+count_full: 17 bytes padding
                # data_start = 24 + count_full + 17
                
                all_blocks = struct.pack('<II', count_full, 0)  # 8 bytes: count_full + padding
                work_blocks = struct.pack('<II', count_text, 0)  # 8 bytes: count_text + padding
                file_bytes = b'\xDC\x96\x58\x59\x00\x00\x00\x00'  # 8 bytes: marker + 4 bytes padding
                
                filled_bytes_unk = b''
                filled_bytes_id = b''
                filled_bytes_text = b''
                
                # Calculate positions (matching Russian code)
                start_unk = len(all_blocks) + len(work_blocks) + len(file_bytes)  # 8 + 8 + 8 = 24
                start_id = start_unk + count_full + 17  # Data starts after code + padding
                curr_text = start_id + count_full * 16
                
                # Track current position in ID section (like Russian code does)
                current_start_id = start_id
                
                for i, entry in enumerate(entries):
                    id_hex = entry['id']
                    
                    if id_hex in translations:
                        # JSON already has unescaped text, no need to unescape
                        text = translations[id_hex]
                    else:
                        text = entry['text']
                    
                    text_bytes = text.encode('utf-8')
                    
                    unk_byte = bytes.fromhex(code[i*2:(i+1)*2])
                    filled_bytes_unk += unk_byte
                    
                    id_bytes = bytes.fromhex(id_hex)
                    filled_bytes_id += id_bytes
                    current_start_id += 8  # After writing ID (8 bytes)
                    
                    # Offset is relative to current_start_id (where offset field is stored)
                    # This matches Russian code: offset = curr_text - start_id (where start_id is updated)
                    offset_len = struct.pack('<II', (curr_text - current_start_id), len(text_bytes))
                    filled_bytes_id += offset_len
                    current_start_id += 8  # After writing offset+length (8 bytes)
                    
                    filled_bytes_text += text_bytes
                    curr_text += len(text_bytes)
                
                # Pad code block to exactly count_full bytes
                if len(filled_bytes_unk) < count_full:
                    filled_bytes_unk += b'\x00' * (count_full - len(filled_bytes_unk))
                
                # Add 17 bytes padding after code block (matching Russian code)
                # Russian code adds: \xFF + (first 16 bytes of code or code + padding)
                # Add padding directly to filled_bytes_unk to match Russian code structure
                if len(filled_bytes_unk) >= 16:
                    filled_bytes_unk += b'\xFF' + filled_bytes_unk[:16]
                else:
                    filled_bytes_unk += b'\xFF' + filled_bytes_unk + b'\x80' * (16 - len(filled_bytes_unk))
                
                with open(output_path, 'wb') as out_f:
                    out_f.write(all_blocks)  # 8 bytes: count_full + padding
                    out_f.write(work_blocks)  # 8 bytes: count_text + padding
                    out_f.write(file_bytes)  # 8 bytes: marker + 4 bytes padding
                    out_f.write(filled_bytes_unk)  # Code block (count_full bytes) + 17 bytes padding
                    out_f.write(filled_bytes_id)  # IDs + offsets + lengths
                    out_f.write(filled_bytes_text)  # Text data
                
                # Create diff .dat file (only changed entries)
                if diff_output_dir and diff_translations:
                    diff_entries = []
                    diff_ids = set()
                    for entry in entries:
                        id_hex = entry['id']
                        if id_hex in diff_translations:
                            diff_entries.append({
                                'id': id_hex,
                                'text': diff_translations[id_hex]  # JSON already has unescaped text
                            })
                            diff_ids.add(id_hex)
                    
                    if diff_entries:
                        # Build diff file (only changed entries)
                        diff_count = len(diff_entries)
                        diff_all_blocks = struct.pack('<II', diff_count, 0)
                        diff_work_blocks = struct.pack('<II', diff_count, 0)
                        diff_file_bytes = b'\xDC\x96\x58\x59\x00\x00\x00\x00'
                        
                        diff_filled_bytes_unk = b''
                        diff_filled_bytes_id = b''
                        diff_filled_bytes_text = b''
                        
                        diff_start_unk = len(diff_all_blocks) + len(diff_work_blocks) + len(diff_file_bytes)
                        diff_start_id = diff_start_unk + diff_count + 17
                        diff_curr_text = diff_start_id + diff_count * 16
                        
                        # Track current position in ID section (like main packing logic)
                        diff_current_start_id = diff_start_id
                        
                        for i, entry in enumerate(diff_entries):
                            id_hex = entry['id']
                            text = entry['text']
                            text_bytes = text.encode('utf-8')
                            
                            # Find original code byte
                            orig_idx = next((j for j, e in enumerate(entries) if e['id'] == id_hex), 0)
                            unk_byte = bytes.fromhex(code[orig_idx*2:(orig_idx+1)*2])
                            diff_filled_bytes_unk += unk_byte
                            
                            id_bytes = bytes.fromhex(id_hex)
                            diff_filled_bytes_id += id_bytes
                            diff_current_start_id += 8  # After writing ID (8 bytes)
                            
                            # Offset is relative to diff_current_start_id (where offset field is stored)
                            offset_len = struct.pack('<II', (diff_curr_text - diff_current_start_id), len(text_bytes))
                            diff_filled_bytes_id += offset_len
                            diff_current_start_id += 8  # After writing offset+length (8 bytes)
                            
                            diff_filled_bytes_text += text_bytes
                            diff_curr_text += len(text_bytes)
                        
                        if len(diff_filled_bytes_unk) < diff_count:
                            diff_filled_bytes_unk += b'\x00' * (diff_count - len(diff_filled_bytes_unk))
                        
                        if len(diff_filled_bytes_unk) >= 16:
                            diff_filled_bytes_unk += b'\xFF' + diff_filled_bytes_unk[:16]
                        else:
                            diff_filled_bytes_unk += b'\xFF' + diff_filled_bytes_unk + b'\x80' * (16 - len(diff_filled_bytes_unk))
                        
                        diff_output_path = os.path.join(diff_output_dir, filename)
                        with open(diff_output_path, 'wb') as diff_out_f:
                            diff_out_f.write(diff_all_blocks)
                            diff_out_f.write(diff_work_blocks)
                            diff_out_f.write(diff_file_bytes)
                            diff_out_f.write(diff_filled_bytes_unk)
                            diff_out_f.write(diff_filled_bytes_id)
                            diff_out_f.write(diff_filled_bytes_text)
        
        except Exception as e:
            print(f"⚠️  Error processing {filename}: {e}")
            continue
    
    return True

def pack_dat_to_binary(dat_dir, output_file):
    """Pack .dat files back to binary."""
    files = [f for f in os.listdir(dat_dir) if f.endswith('.dat')]
    
    def extract_number(filename):
        match = re.search(r'(\d+)\.dat$', filename)
        return int(match.group(1)) if match else float('inf')
    
    files.sort(key=extract_number)
    
    with open(output_file, 'wb') as outfile:
        outfile.write(b'\xEF\xBE\xAD\xDE\x01\x00\x00\x00')
        count_files = struct.pack('<I', len(files))
        outfile.write(count_files)
        archive = b''
        
        for filename in files:
            file_path = os.path.join(dat_dir, filename)
            file_size = os.path.getsize(file_path)
            
            with open(file_path, 'rb') as infile:
                comp_data = pyzstd.compress(infile.read())
                header = struct.pack('<BII', 4, len(comp_data), file_size)
                len_arch = struct.pack('<I', len(archive))
                outfile.write(len_arch)
                archive += header + comp_data
        
        len_arch = struct.pack('<I', len(archive))
        outfile.write(len_arch)
        outfile.write(archive)

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Repack translations to binary')
    parser.add_argument('--template', default='translation/translation_template.json',
                       help='Translation template JSON file')
    parser.add_argument('--source-binary', default='language/source/translate_words_map_zh_cn',
                       help='Source binary file (default: Chinese, used as template)')
    parser.add_argument('--official-binary', default='language/source/translate_words_map_zh_cn',
                       help='Official binary file for diff comparison (default: Chinese)')
    parser.add_argument('--output-binary', default='language/mod/translate_words_map_vi',
                       help='Output binary file')
    parser.add_argument('--output-diff', default=None,
                       help='Output diff binary file (default: output_binary + _diff)')
    parser.add_argument('--temp-dir', default='temp_repack',
                       help='Temporary directory for .dat files')
    parser.add_argument('--mode', choices=['target', 'autofill'], default='autofill',
                       help='Translation mode: target (use target column only), autofill (use target, fallback to autofill column)')
    parser.add_argument('--target-column', default='Target',
                       help='Column name to use as primary translation source (default: Target)')
    parser.add_argument('--autofill-column', default='English',
                       help='Column name to use for autofill when target is empty (default: English)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Repack Translations")
    print("=" * 60)
    print()
    print("⚠️  Note: Diff file will be created automatically for game compatibility")
    print()
    
    os.makedirs(os.path.dirname(args.output_binary), exist_ok=True)
    
    # Always create diff file (required for game compatibility)
    if args.output_diff:
        diff_output_binary = args.output_diff
    else:
        # Auto-generate diff filename
        base_path = os.path.splitext(args.output_binary)[0]
        diff_output_binary = base_path + '_diff'
    os.makedirs(os.path.dirname(diff_output_binary), exist_ok=True)
    
    # Step 1: Extract source to .dat
    print("📦 Step 1: Extracting source binary...")
    source_dat_dir = os.path.join(args.temp_dir, "source_dat")
    if not extract_file_to_dat(args.source_binary, source_dat_dir):
        print("❌ Failed to extract source binary")
        return
    
    # Step 1b: Extract official to .dat (for diff) - REQUIRED
    print("\n📦 Step 1b: Extracting official binary for diff (required)...")
    official_dat_dir = os.path.join(args.temp_dir, "official_dat")
    if not extract_file_to_dat(args.official_binary, official_dat_dir):
        print("❌ Failed to extract official binary! Diff file is required for game compatibility.")
        print("   Please ensure the official binary file exists and is valid.")
        return
    else:
        print("   ✅ Official binary extracted")
    
    # Step 2: Pack text to .dat
    print(f"\n📝 Step 2: Packing translations to .dat (mode: {args.mode})...")
    output_dat_dir = os.path.join(args.temp_dir, "output_dat")
    diff_output_dat_dir = os.path.join(args.temp_dir, "diff_dat")  # Always create diff
    if not pack_text_to_dat(args.template, source_dat_dir, output_dat_dir, 
                           mode=args.mode,
                           target_column=args.target_column,
                           autofill_column=args.autofill_column,
                           official_dat_dir=official_dat_dir,
                           diff_output_dir=diff_output_dat_dir):
        print("❌ Failed to pack translations")
        return
    
    # Step 3: Pack .dat to binary
    print("\n📦 Step 3: Packing .dat to binary...")
    pack_dat_to_binary(output_dat_dir, args.output_binary)
    
    # Step 3b: Create diff file (REQUIRED)
    # Strategy: Copy official diff file to pass game verification
    # If official diff doesn't exist or is empty, create minimal diff
    print("\n📦 Step 3b: Creating diff file (required for game verification)...")
    
    official_diff_file = args.official_binary + '_diff'
    if os.path.exists(official_diff_file) and os.path.getsize(official_diff_file) > 16:
        # Copy official diff file (common modding technique to pass verification)
        print(f"   📋 Copying official diff file for verification...")
        shutil.copy2(official_diff_file, diff_output_binary)
        print(f"   ✅ Diff file copied from official: {diff_output_binary}")
        print(f"   ℹ️  Using official diff to pass game file verification")
    elif diff_output_dat_dir and os.path.exists(diff_output_dat_dir):
        # Create diff from extracted .dat files (if we have changes)
        files = [f for f in os.listdir(diff_output_dat_dir) if f.endswith('.dat')]
        if files:
            pack_dat_to_binary(diff_output_dat_dir, diff_output_binary)
            print(f"   ✅ Diff file created from changes: {diff_output_binary}")
        else:
            # Create minimal empty diff file (16 bytes header only)
            print(f"   ⚠️  No changes detected, creating minimal diff file...")
            with open(diff_output_binary, 'wb') as f:
                f.write(b'\xEF\xBE\xAD\xDE\x01\x00\x00\x00')  # Magic + version
                f.write(struct.pack('<I', 0))  # offset_count = 0
                f.write(struct.pack('<I', 0))  # comp_block_len = 0
            print(f"   ✅ Minimal diff file created: {diff_output_binary}")
    else:
        # Fallback: create minimal empty diff
        print(f"   ⚠️  Creating minimal diff file (fallback)...")
        with open(diff_output_binary, 'wb') as f:
            f.write(b'\xEF\xBE\xAD\xDE\x01\x00\x00\x00')  # Magic + version
            f.write(struct.pack('<I', 0))  # offset_count = 0
            f.write(struct.pack('<I', 0))  # comp_block_len = 0
        print(f"   ✅ Minimal diff file created: {diff_output_binary}")
    
    # Cleanup
    shutil.rmtree(args.temp_dir, ignore_errors=True)
    
    print(f"\n✅ Complete! Output files:")
    print(f"   - Main: {args.output_binary}")
    print(f"   - Diff: {diff_output_binary} (REQUIRED for game)")

if __name__ == "__main__":
    main()

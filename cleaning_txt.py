import os
import re

# ==========================================
# 設定
# ==========================================
EJDICT_FILE = "ejdict-hand-utf8.txt"  # ejdictのテキストファイルのパス
INPUT_FILES = ["prefix2.txt", "root2.txt", "suffix2.txt"] # 処理する入力ファイル群

# 丸数字（①〜⑳）のリスト
CIRCLED_NUMBERS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"

def load_ejdict(filepath):
    """
    ejdict-hand-utf8.txtを読み込み、見出し語のセットを作成する
    """
    ejdict_words = set()
    if not os.path.exists(filepath):
        print(f"【警告】{filepath} が見つかりません。辞書チェックをスキップします。")
        return ejdict_words

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if '\t' in line:
                word = line.split('\t')[0].strip().lower()
                ejdict_words.add(word)
    
    print(f"ejdictから {len(ejdict_words)} 語を読み込みました。")
    return ejdict_words

def check_in_dict(stem_raw, ejdict_words):
    """
    語幹が辞書に存在するか確認する
    """
    if not ejdict_words:
        return True 

    stems = [s.strip(" -,") for s in stem_raw.split(",")]
    for s in stems:
        if s in ejdict_words or f"{s}-" in ejdict_words or f"-{s}" in ejdict_words:
            return True
    return False

def replace_circled_numbers(text):
    """
    丸数字（①、②...）を角括弧の数字（[1]、[2]...）に変換する
    """
    for i, char in enumerate(CIRCLED_NUMBERS, start=1):
        text = text.replace(char, f"[{i}]")
    return text

def clean_meaning(meaning):
    """
    意味の欄から英単語を削除し、丸数字を変換する
    """
    cleaned = re.sub(r'[a-zA-Zａ-ｚＡ-Ｚ]', '', meaning)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'^[/／、・]+|[/／、・]+$', '', cleaned) 
    cleaned = replace_circled_numbers(cleaned)
    return cleaned if cleaned else "意味なし"

def clean_stem_str(s):
    """
    あらゆる種類のダッシュやハイフンを除去して比較用文字列を作る
    """
    return re.sub(r'[-–—−－]', '', s)

def process_file(input_file, ejdict_words):
    if not os.path.exists(input_file):
        print(f"【スキップ】{input_file} が見つかりません。")
        return

    # 統合用リスト: [ [元の語幹セット, 比較用のハイフン無し語幹セット, 意味のリスト], ... ]
    merged_data = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or '\t' not in line:
                continue

            parts = line.split('\t', 1)
            if len(parts) != 2:
                continue

            stem_raw, meaning_raw = parts[0].strip(), parts[1].strip()

            if not check_in_dict(stem_raw, ejdict_words):
                continue

            cleaned_meaning = clean_meaning(meaning_raw)

            # カンマで分割してセット化
            raw_stems = set(s.strip() for s in stem_raw.split(","))
            # ハイフンを除外した比較用のセット
            clean_stems = set(clean_stem_str(s) for s in raw_stems)

            # 既存のグループと一致するものがあるか全検索
            matching_indices = []
            for i, entry in enumerate(merged_data):
                existing_clean_stems = entry[1]
                # ハイフン無しの状態で一致する要素が1つでもあればインデックスを記録
                if clean_stems & existing_clean_stems:
                    matching_indices.append(i)
            
            if not matching_indices:
                # どのグループにも属さなければ新規追加
                merged_data.append([raw_stems, clean_stems, [cleaned_meaning]])
            else:
                # 複数のグループにまたがって一致した場合、最初のグループに全てを吸収・統合する
                first_idx = matching_indices[0]
                merged_data[first_idx][0].update(raw_stems)
                merged_data[first_idx][1].update(clean_stems)
                if cleaned_meaning not in merged_data[first_idx][2]:
                    merged_data[first_idx][2].append(cleaned_meaning)
                
                # 吸収された残りのグループはデータを移したあとに削除する（後ろから削除）
                for idx in reversed(matching_indices[1:]):
                    merged_data[first_idx][0].update(merged_data[idx][0])
                    merged_data[first_idx][1].update(merged_data[idx][1])
                    for m in merged_data[idx][2]:
                        if m not in merged_data[first_idx][2]:
                            merged_data[first_idx][2].append(m)
                    merged_data.pop(idx)

    output_file = input_file.replace(".txt", "_cleaned.txt")

    with open(output_file, 'w', encoding='utf-8') as f:
        for raw_stems, _, meanings in merged_data:
            stems_list = list(raw_stems)
            final_stems = []
            
            # ダッシュあり・なしの重複表示を解消する処理
            for s in stems_list:
                if "-" not in s:
                    # ダッシュ付き（接頭辞 or 接尾辞）が存在していれば、ダッシュ無しの方は表示から除外
                    if (s + "-") in stems_list or ("-" + s) in stems_list:
                        continue
                final_stems.append(s)
                
            # アルファベット順にソートして出力
            stem_str = ", ".join(sorted(final_stems))
            merged_meaning = " / ".join(meanings)
            
            f.write(f"{stem_str}\t{merged_meaning}\n")
            
    print(f"完了: {input_file} -> {output_file} に保存しました（{len(merged_data)} 項目に圧縮）。")

# ==========================================
# 実行部
# ==========================================
if __name__ == "__main__":
    print("処理を開始します...")
    dict_words = load_ejdict(EJDICT_FILE)
    
    for filename in INPUT_FILES:
        process_file(filename, dict_words)
        
    print("すべての処理が完了しました。")
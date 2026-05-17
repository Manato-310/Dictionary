import json
import requests
import time
import os
import sys
import csv

def load_csv_master(filename):
    if not os.path.exists(filename):
        print(f"⚠️ マスターファイル '{filename}' が見つかりません。スキップします。")
        return []
        
    data = []
    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    print(f"📁 {filename} を読み込みました（{len(data)}件）")
    return data

def load_ejdict():
    ejdict_file = "ejdict-hand-utf8.txt"
    if not os.path.exists(ejdict_file):
        print(f"❌ エラー: 辞書ファイル '{ejdict_file}' が見つかりません。")
        sys.exit(1)
            
    print("📚 辞書データを読み込み中...")
    dictionary = {}
    with open(ejdict_file, "r", encoding="utf-8") as f:
        for line in f:
            if "\t" in line:
                word, meaning = line.strip().split("\t", 1)
                dictionary[word.lower()] = meaning
    return dictionary

def fetch_wiktionary_words(category_name, limit=None): 
    """Wiktionary APIを使って特定のカテゴリに属する英単語を取得する"""
    url = "https://en.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category_name}",
        "cmnamespace": 0, 
        "cmlimit": 500,
        "format": "json"
    }
    
    headers = {"User-Agent": "EtymologyLearningApp/1.3 (Educational purpose)"}
    
    print(f"[{category_name}] をWiktionaryで検索中", end="", flush=True)
    words = []
    
    while True:
        try:
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 429:
                print(" ⏳制限に達しました。10秒待機して再試行します...", end="", flush=True)
                time.sleep(10)
                continue
                
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"\nAPIエラー: {e}")
            break
        
        if "query" in data and "categorymembers" in data["query"]:
            for member in data["query"]["categorymembers"]:
                title = member["title"]
                if " " not in title and "-" not in title:
                    words.append(title)
                
                if limit and len(words) >= limit:
                    break
        
        if limit and len(words) >= limit:
            break
            
        if "continue" in data and "cmcontinue" in data["continue"]:
            params["cmcontinue"] = data["continue"]["cmcontinue"]
            print(".", end="", flush=True)
            time.sleep(2)
        else:
            break
            
    print(f" -> {len(words)}件 取得完了")
    if limit:
        words = words[:limit]
    return words

def analyze_suffix(word, suffix_master):
    if not suffix_master:
        return "-"
    sorted_suffixes = sorted(suffix_master, key=lambda x: len(x['suffix']), reverse=True)
    for suf_info in sorted_suffixes:
        if word.endswith(suf_info['suffix']):
            return f"-{suf_info['suffix']} ({suf_info['role']})"
    return "-"

def load_existing_data(filename="etymology_data.json"):
    """既存のJSONデータを読み込み、差分更新を行えるようにする"""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                print(f"📦 既存データ '{filename}' を読み込みました。")
                return data
            except json.JSONDecodeError:
                print(f"⚠️ '{filename}' の形式が不正です。新規作成として扱います。")
    return {"etymologies": [], "word_families": [], "words": []}

def generate_real_data():
    print("=== データ生成プロセス開始 (Wiktionary API 高精度版) ===")
    start_time = time.time()
    
    # 1. マスターデータの読み込み
    prefix_master = load_csv_master("prefix_master.csv")
    root_master = load_csv_master("root_master.csv")
    etymology_master = prefix_master + root_master
    
    if not etymology_master:
        print("❌ マスターデータが1件もありません。処理を終了します。")
        sys.exit(1)

    suffix_master = load_csv_master("suffix_master.csv")
    ejdict = load_ejdict()
    existing_data = load_existing_data()
    
    etymologies = existing_data["etymologies"]
    word_families = existing_data["word_families"]
    words_data = existing_data["words"]

    # 既に処理済みの語源IDをセットとして取得（スキップ判定用）
    processed_ety_ids = {ety["id"] for ety in etymologies}

    # IDカウンターの復元
    max_family_id = 0
    for f in word_families:
        num = int(f["id"].replace("f", ""))
        if num > max_family_id: max_family_id = num
    family_id_counter = max_family_id + 1

    max_word_id = 0
    for w in words_data:
        num = int(w["id"].replace("w", ""))
        if num > max_word_id: max_word_id = num
    word_id_counter = max_word_id + 1

    has_new_data = False

    # 2. マスターデータの各語源ごとに処理ループ
    for ety in etymology_master:
        # スキップ判定
        if ety["id"] in processed_ety_ids:
            print(f"⏭️ [{ety['spelling']}] は既に取得済みのためスキップします。")
            continue

        fetched_words = fetch_wiktionary_words(ety["category"], limit=None)
        time.sleep(3) 

        # 辞書フィルタリング & 語根の厳格フィルタリング
        valid_words = []
        target_spelling = ety["spelling"].lower().replace('-', '')
        
        for w in fetched_words:
            w_lower = w.lower()
            if w_lower in ejdict:
                # 語根(root)の場合、指定した綴りが含まれていない単語は除外する
                if ety["type"] == "root" and target_spelling not in w_lower:
                    continue
                valid_words.append(w)
                
        print(f"  -> 辞書フィルタリング後: {len(valid_words)}件の単語が残りました")

        if len(valid_words) == 0:
            print(f"⚠️ 有効な単語が0件だったため、[{ety['spelling']}] は保存しません（次回再試行します）。")
            continue

        has_new_data = True
        etymologies.append({
            "id": ety["id"],
            "type": ety["type"],
            "spelling": ety["spelling"],
            "meaning": ety["meaning"]
        })

        # 語幹・語根でグループ化
        groups = {}
        for w in valid_words:
            w_lower = w.lower()
            if ety["type"] == "prefix":
                prefix_clean = ety['spelling'].replace('-', '')
                base_part = w[len(prefix_clean):] if w_lower.startswith(prefix_clean) else w
                stem_key = base_part[:4] if len(base_part) >= 4 else base_part
            else:
                idx = w_lower.find(target_spelling)
                if idx > 0:
                    prefix_part = w[:idx]
                    stem_key = f"{prefix_part} + {target_spelling}"
                else:
                    stem_key = f"{target_spelling} (先頭)"
                
            if stem_key not in groups:
                groups[stem_key] = []
            groups[stem_key].append(w)

        # データ構造への格納
        for stem_key, words_in_group in groups.items():
            family_id = f"f{family_id_counter}"
            base_word = words_in_group[0] 
            
            # === Explanation の動的生成 ===
            if ety["type"] == "prefix":
                prefix_clean = ety['spelling'].replace('-', '')
                base_part = base_word[len(prefix_clean):] if base_word.lower().startswith(prefix_clean) else base_word
                
                found_root_spell = base_part
                found_root_meaning = "?" 
                for r in root_master:
                    if r['spelling'] in base_part:
                        found_root_spell = r['spelling']
                        found_root_meaning = r['meaning']
                        break
                
                explanation = f"{prefix_clean}({ety['meaning']}) + {found_root_spell}({found_root_meaning})"
                
            else:
                idx = base_word.lower().find(target_spelling)
                if idx > 0:
                    prefix_part = base_word[:idx] 
                    found_pref_spell = prefix_part
                    found_pref_meaning = "?"
                    
                    for p in prefix_master:
                        p_clean = p['spelling'].replace('-', '')
                        if p_clean in prefix_part or prefix_part in p_clean:
                            found_pref_spell = prefix_part
                            found_pref_meaning = p['meaning']
                            break
                            
                    explanation = f"{found_pref_spell}({found_pref_meaning}) + {target_spelling}({ety['meaning']})"
                else:
                    explanation = f"{target_spelling}({ety['meaning']}) から派生"
            
            word_families.append({
                "id": family_id,
                "etymology_id": ety["id"],
                "base_word": base_word,
                "explanation": explanation
            })
            family_id_counter += 1

            for w in words_in_group:
                meaning_text = ejdict[w.lower()]
                pos = "不明"
                if "(v" in meaning_text or "する" in meaning_text: pos = "動詞"
                elif "(n" in meaning_text or "こと" in meaning_text: pos = "名詞"
                elif "(a" in meaning_text or "な" in meaning_text: pos = "形容詞"
                elif "(ad" in meaning_text or "に" in meaning_text: pos = "副詞"
                
                short_meaning = meaning_text.replace('/', ', ').split(';')[0]
                
                words_data.append({
                    "id": f"w{word_id_counter}",
                    "family_id": family_id,
                    "spelling": w,
                    "part_of_speech": pos,
                    "meaning": short_meaning,
                    "suffix": analyze_suffix(w, suffix_master)
                })
                word_id_counter += 1

    # 4. JSONへ差分保存
    if has_new_data:
        final_data = {
            "etymologies": etymologies,
            "word_families": word_families,
            "words": words_data
        }
        with open('etymology_data.json', 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        end_time = time.time()
        print(f"✨ すべての処理が完了し、etymology_data.json を更新しました！ (所要時間: {end_time - start_time:.1f}秒)")
    else:
        end_time = time.time()
        print(f"✅ 新しく追加するデータはありませんでした。(所要時間: {end_time - start_time:.1f}秒)")

if __name__ == "__main__":
    generate_real_data()
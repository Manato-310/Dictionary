import json
import requests
import time
import os
import sys
import csv

# ==========================================
# 🛑 ブラックリスト
# ==========================================
# 偶然の一致で間違ったグループに入ってしまうのを防ぐ
EXCLUDE_LIST = {
    "of": ["office", "officer", "official", "officiate"],
}

# ==========================================
# 💎 カスタム語源辞書
# ==========================================
# 激しく文字が変形(ope -> of)しており、システムが自動判定できない単語の
# 「正しいパーツと意味」を強制的に上書き指定します。
CUSTOM_ETYMOLOGY = {
    "office": {"prefix": "ope", "prefix_meaning": "仕事・富"},
    "officer": {"prefix": "ope", "prefix_meaning": "仕事・富"},
    "official": {"prefix": "ope", "prefix_meaning": "仕事・富"},
    "officiate": {"prefix": "ope", "prefix_meaning": "仕事・富"},
}

def load_csv_master(filename):
    if not os.path.exists(filename):
        print(f"⚠️ マスターファイル '{filename}' が見つかりません。スキップします。")
        return []
        
    data = []
    with open(filename, "r", encoding="utf-8-sig") as f:
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
    url = "https://en.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category_name}",
        "cmnamespace": 0, 
        "cmlimit": 500,
        "format": "json"
    }
    
    headers = {"User-Agent": "EtymologyLearningApp/1.9 (Educational purpose)"}
    
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

def is_compound(word, ejdict):
    if len(word) < 6:
        return False
    for i in range(3, len(word) - 2):
        p1 = word[:i]
        p2 = word[i:]
        if p1 in ejdict and p2 in ejdict:
            return True
    return False

def analyze_suffix(word, suffix_master):
    if not suffix_master:
        return {"display": "-", "pos": "-"}
        
    sorted_suffixes = sorted(suffix_master, key=lambda x: len(x['suffix']), reverse=True)
    vowels = {'a', 'e', 'i', 'o', 'u'}
    
    for suf_info in sorted_suffixes:
        suf = suf_info['suffix']
        if word.endswith(suf):
            base_part = word[:-len(suf)] if len(suf) > 0 else word
            
            if len(base_part) <= 2:
                continue
                
            if suf == "y" and len(base_part) > 0 and base_part[-1] in vowels:
                continue
                
            pos = suf_info.get('pos', '-')
            return {
                "display": f"-{suf_info['suffix']} ({suf_info['role']})",
                "pos": pos
            }
            
    return {"display": "-", "pos": "-"}

def load_existing_data(filename="etymology_data.json"):
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
    print("=== データ生成プロセス開始 ===")
    start_time = time.time()
    
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

    processed_ety_ids = {ety["id"] for ety in etymologies}

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

    common_prefixes = [
        "a", "ab", "abs", "ad", "ac", "af", "ag", "al", "an", "ap", "ar", "as", "at", 
        "con", "com", "col", "cor", "co", "de", "dis", "dif", "di", "en", "em",
        "ex", "e", "ef", "im", "in", "il", "ir", "inter", "intro", "ob", "oc", "of", "op",
        "per", "pre", "pro", "re", "retro", "sub", "suc", "suf", "sug", "sup", "sur", "sus", 
        "trans", "tra", "un", "non", "over", "out", "auto", "anti", "bi", "mono", "poly", "under"
    ]
    
    all_starting_parts = set(common_prefixes)
    for p in prefix_master:
        all_starting_parts.add(p['spelling'].replace('-', ''))
    for r in root_master:
        all_starting_parts.add(r['spelling'].replace('-', ''))

    for ety in etymology_master:
        if not ety.get("category"):
            print(f"⚠️ [{ety['spelling']}] は category が設定されていないためスキップします。")
            continue
            
        if ety["id"] in processed_ety_ids:
            print(f"⏭️ [{ety['spelling']}] は既に取得済みのためスキップします。")
            continue

        fetched_words = fetch_wiktionary_words(ety["category"], limit=None)
        time.sleep(3) 

        valid_words = []
        target_spelling = ety["spelling"].lower().replace('-', '')
        
        for w in fetched_words:
            w_lower = w.lower()
            
            if target_spelling in EXCLUDE_LIST and w_lower in EXCLUDE_LIST[target_spelling]:
                continue
                
            if w_lower in ejdict:
                if ety["type"] == "root" and target_spelling not in w_lower:
                    continue
                if w_lower not in valid_words:
                    valid_words.append(w_lower)
                
        print(f"  -> Wiktionaryからの抽出: {len(valid_words)}件の単語が残りました")

        print(f"  -> 辞書全体から [{target_spelling}] に関連する単語を補完検索します...")
        rescued_count = 0
        
        can_rescue_root = (ety["type"] == "root" and len(target_spelling) >= 3)
        can_rescue_prefix = (ety["type"] == "prefix")

        for dict_word in ejdict.keys():
            if dict_word not in valid_words:
                
                if target_spelling in EXCLUDE_LIST and dict_word in EXCLUDE_LIST[target_spelling]:
                    continue
                
                if can_rescue_root and target_spelling in dict_word:
                    idx = dict_word.find(target_spelling)
                    if idx == 0:
                        valid_words.append(dict_word)
                        rescued_count += 1
                    elif idx > 0:
                        prefix_part = dict_word[:idx]
                        is_valid_prefix = prefix_part in common_prefixes
                        if not is_valid_prefix:
                            for p in prefix_master:
                                if p['spelling'].replace('-', '') == prefix_part:
                                    is_valid_prefix = True
                                    break
                        if is_valid_prefix:
                            valid_words.append(dict_word)
                            rescued_count += 1
                            
                elif can_rescue_prefix and dict_word.startswith(target_spelling):
                    
                    is_overridden = False
                    for other_part in all_starting_parts:
                        if len(other_part) > len(target_spelling) and dict_word.startswith(other_part):
                            is_overridden = True
                            break
                    
                    if is_overridden:
                        continue
                        
                    base_part = dict_word[len(target_spelling):]
                    if len(base_part) >= 3:
                        is_valid_base = False
                        
                        if base_part in ejdict:
                            is_valid_base = True
                        else:
                            for r in root_master:
                                r_spell = r['spelling']
                                if len(r_spell) >= 3 and base_part.startswith(r_spell):
                                    is_valid_base = True
                                    break
                                    
                        if is_valid_base:
                            valid_words.append(dict_word)
                            rescued_count += 1
                            
        print(f"  -> 補完完了: {rescued_count}件の一般的な単語を救済しました！")
        print(f"  -> 最終的な単語数: {len(valid_words)}件")

        if len(valid_words) == 0:
            print(f"⚠️ 有効な単語が0件だったため、[{ety['spelling']}] は保存しません。")
            continue

        has_new_data = True
        etymologies.append({
            "id": ety["id"],
            "type": ety["type"],
            "spelling": ety["spelling"],
            "meaning": ety["meaning"]
        })

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
                    prefix_part = w_lower[:idx]
                    stem_key = f"{prefix_part} + {target_spelling}"
                else:
                    stem_key = f"{target_spelling} (先頭)"
                
            if stem_key not in groups:
                groups[stem_key] = []
            groups[stem_key].append(w_lower)

        for stem_key, words_in_group in groups.items():
            family_id = f"f{family_id_counter}"
            base_word = words_in_group[0] 
            
            # ==========================================
            # 🌟 説明文（explanation）とUI用パーツ（explanation_parts）の生成ロジック
            # ==========================================
            explanation_parts = []

            if ety["type"] == "prefix":
                prefix_clean = ety['spelling'].replace('-', '')
                base_part = base_word[len(prefix_clean):] if base_word.startswith(prefix_clean) else base_word
                found_root_spell = base_part
                found_root_meaning = "?" 
                for r in root_master:
                    if r['spelling'] in base_part:
                        found_root_spell = r['spelling']
                        found_root_meaning = r['meaning']
                        break
                explanation = f"{prefix_clean}({ety['meaning']}) + {found_root_spell}({found_root_meaning})"
                
                # UI用バッジパーツの構築
                explanation_parts.append({"type": "prefix", "text": prefix_clean, "meaning": ety['meaning']})
                explanation_parts.append({"type": "root", "text": found_root_spell, "meaning": found_root_meaning})

            else:
                # 💎 カスタム辞書に登録されていれば、強制上書きする！
                if base_word in CUSTOM_ETYMOLOGY:
                    found_pref_spell = CUSTOM_ETYMOLOGY[base_word]["prefix"]
                    found_pref_meaning = CUSTOM_ETYMOLOGY[base_word]["prefix_meaning"]
                    explanation = f"{found_pref_spell}({found_pref_meaning}) + {target_spelling}({ety['meaning']})"
                    
                    explanation_parts.append({"type": "prefix", "text": found_pref_spell, "meaning": found_pref_meaning})
                    explanation_parts.append({"type": "root", "text": target_spelling, "meaning": ety['meaning']})
                else:
                    idx = base_word.find(target_spelling)
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
                        
                        explanation_parts.append({"type": "prefix", "text": found_pref_spell, "meaning": found_pref_meaning})
                        explanation_parts.append({"type": "root", "text": target_spelling, "meaning": ety['meaning']})
                    else:
                        explanation = f"{target_spelling}({ety['meaning']}) から派生"
                        
                        explanation_parts.append({"type": "root", "text": target_spelling, "meaning": ety['meaning']})
                        explanation_parts.append({"type": "other", "text": "から派生", "meaning": ""})
            
            word_families.append({
                "id": family_id,
                "etymology_id": ety["id"],
                "base_word": base_word,
                "explanation": explanation,
                "explanation_parts": explanation_parts  # UI用の構造化データを追加
            })
            family_id_counter += 1

            for w in words_in_group:
                if is_compound(w, ejdict):
                    suffix_data = {"display": "-", "pos": "-"}
                else:
                    suffix_data = analyze_suffix(w, suffix_master)
                    
                meaning_text = ejdict[w]
                pos = "不明"
                
                first_meaning = meaning_text.split('/')[0].split(',')[0].split(';')[0].strip()
                
                if "(v" in first_meaning: pos = "動詞"
                elif "(n" in first_meaning or "(pron" in first_meaning: pos = "名詞"
                elif "(a" in first_meaning: pos = "形容詞"
                elif "(ad" in first_meaning: pos = "副詞"
                elif "(prep" in first_meaning: pos = "前置詞"
                elif "(conj" in first_meaning: pos = "接続詞"
                
                if pos == "不明":
                    if first_meaning.endswith("する"): pos = "動詞"
                    elif first_meaning.endswith("な") or first_meaning.endswith("の") or first_meaning.endswith("的"): pos = "形容詞"
                    elif first_meaning.endswith("に") or first_meaning.endswith("く"): pos = "副詞"
                    elif first_meaning.endswith("こと") or first_meaning.endswith("もの") or first_meaning.endswith("人"): pos = "名詞"
                
                if pos == "不明" and suffix_data["pos"] != "-":
                    pos = suffix_data["pos"]
                    
                if pos == "不明":
                    pos = "名詞"
                
                short_meaning = meaning_text.replace('/', ', ').split(';')[0]
                
                words_data.append({
                    "id": f"w{word_id_counter}",
                    "family_id": family_id,
                    "spelling": w,
                    "part_of_speech": pos,
                    "meaning": short_meaning,
                    "suffix": suffix_data["display"]
                })
                word_id_counter += 1

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
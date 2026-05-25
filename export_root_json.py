import json
import os
import sys
import time
from utils import WORD_EXCEPTIONS, load_csv_master, load_ejdict, analyze_suffix

# ==========================================
# 設定
# ==========================================
INPUT_ALLOCATIONS_FILE = "root_allocations.json"
OUTPUT_JSON_FILE = "root_data.json"

def export_root_json():
    print("=== 語根データJSON構築(軽い処理) 開始 ===")
    start_time = time.time()
    
    etymology_master = load_csv_master("root_master.csv")
    prefix_master = load_csv_master("prefix_master.csv")
    suffix_master = load_csv_master("suffix_master.csv")
    ejdict = load_ejdict()
    
    if not os.path.exists(INPUT_ALLOCATIONS_FILE):
        print(f"❌ エラー: 割り当てファイル '{INPUT_ALLOCATIONS_FILE}' が見つかりません。")
        print("先に build_root_allocations.py を実行してください。")
        sys.exit(1)
        
    with open(INPUT_ALLOCATIONS_FILE, 'r', encoding='utf-8') as f:
        allocations = json.load(f)
    print(f"📦 割り当てデータを読み込みました。")

    etymologies = []
    word_families = []
    words_data = []

    family_id_counter = 1
    word_id_counter = 1
    
    for ety in etymology_master:
        valid_words = allocations.get(ety["id"], [])
        target_spelling = ety["spelling"].lower().replace('-', '')
        
        if len(valid_words) == 0:
            continue

        etymologies.append({
            "id": ety["id"],
            "type": ety["type"],
            "spelling": ety["spelling"],
            "meaning": ety["meaning"]
        })

        groups = {}
        for w in valid_words:
            w_lower = w.lower()
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
            family_id = f"rf{family_id_counter}" # 語根用ID
            
            words_in_group.sort(key=len)
            base_word = words_in_group[0] 
            
            explanation_parts = []

            if base_word in WORD_EXCEPTIONS and "custom_prefix" in WORD_EXCEPTIONS[base_word]:
                found_pref_spell = WORD_EXCEPTIONS[base_word]["custom_prefix"]
                found_pref_meaning = WORD_EXCEPTIONS[base_word]["custom_prefix_meaning"]
                explanation = f"{found_pref_spell}({found_pref_meaning}) + {target_spelling}({ety['meaning']})"
                
                explanation_parts.append({"type": "prefix", "text": found_pref_spell, "meaning": found_pref_meaning})
                explanation_parts.append({"type": "root", "text": target_spelling, "meaning": ety['meaning']})
            else:
                idx = base_word.find(target_spelling)
                if idx > 0:
                    prefix_part = base_word[:idx] 
                    found_pref_spell = prefix_part
                    found_pref_meaning = "?"
                    
                    sorted_prefs_for_desc = sorted([p for p in prefix_master], key=lambda x: len(x['spelling'].replace('-', '')), reverse=True)
                    for p in sorted_prefs_for_desc:
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
                "explanation_parts": explanation_parts
            })
            family_id_counter += 1

            for w in words_in_group:
                suffix_data = analyze_suffix(w, suffix_master, ejdict)
                    
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
                
                short_meaning = meaning_text.replace('/', ', ').split(';')[0]
                
                words_data.append({
                    "id": f"rw{word_id_counter}",
                    "family_id": family_id,
                    "spelling": w,
                    "part_of_speech": pos,
                    "meaning": short_meaning,
                    "suffix": suffix_data["display"]
                })
                word_id_counter += 1

    final_data = {
        "etymologies": etymologies,
        "word_families": word_families,
        "words": words_data
    }
    with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    end_time = time.time()
    print(f"✨ JSONの構築が完了し、{OUTPUT_JSON_FILE} を生成しました！ (所要時間: {end_time - start_time:.2f}秒)")

if __name__ == "__main__":
    export_root_json()
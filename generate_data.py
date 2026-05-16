import json
import requests
import time
import os
import sys

TARGET_PREFIXES = [
    {"id": "e1", "spelling": "pre-", "meaning": "前に、あらかじめ", "category": "English_terms_prefixed_with_pre-"},
    {"id": "e2", "spelling": "re-", "meaning": "再び、後ろに", "category": "English_terms_prefixed_with_re-"},
    {"id": "e3", "spelling": "sub-", "meaning": "下に、副次的な", "category": "English_terms_prefixed_with_sub-"}
]

def load_ejdict():
    """ejdict-handのデータをローカルファイルからメモリに読み込む"""
    ejdict_file = "ejdict-hand-utf8.txt"
    
    if not os.path.exists(ejdict_file):
        print(f"❌ エラー: 辞書ファイル '{ejdict_file}' が見つかりません。")
        print("このスクリプトと同じフォルダに辞書ファイルを配置してください。")
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
    """Wiktionary APIを使って特定のカテゴリに属する英単語を全件取得する"""
    url = "https://en.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category_name}",
        "cmnamespace": 0, 
        "cmlimit": 500, # 1回のリクエストで取得できる最大数
        "format": "json"
    }
    
    # Wikimedia APIのポリシーに沿って、連絡先(GitHubのアカウント名など)を記載しておくと制限されにくくなります
    headers = {"User-Agent": "EtymologyLearningApp/1.0 (Educational purpose; GitHub: Manato-310)"}
    
    print(f"[{category_name}] をWiktionaryで検索中", end="", flush=True)
    words = []
    
    while True:
        try:
            response = requests.get(url, params=params, headers=headers)
            
            # 429 Too Many Requests エラーの場合は待機してリトライ
            if response.status_code == 429:
                print(" ⏳制限に達しました。10秒待機して再試行します...", end="", flush=True)
                time.sleep(10) # 5秒から10秒に延長してより安全に
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
                
                # 上限が設定されていて、それに達した場合は終了
                if limit and len(words) >= limit:
                    break
        
        if limit and len(words) >= limit:
            break
            
        # 次のページ（続きのデータ）があるかチェック
        if "continue" in data and "cmcontinue" in data["continue"]:
            params["cmcontinue"] = data["continue"]["cmcontinue"]
            print(".", end="", flush=True) # 継続中であることを示すドットを表示
            time.sleep(2) # サーバーへの負荷軽減（1秒から2秒に延長）
        else:
            break # 全件取得完了
            
    print(f" -> {len(words)}件 取得完了")
    
    if limit:
        words = words[:limit]
    return words

def analyze_suffix(word):
    """単語の末尾から接尾辞を推測する"""
    suffixes = {
        'tion': '名詞化', 'sion': '名詞化', 'ment': '名詞化', 'ness': '名詞化', 'ity': '名詞化',
        'able': '形容詞化 (可能)', 'ible': '形容詞化 (可能)', 'ive': '形容詞化 (性質)', 'al': '形容詞化', 'ful': '形容詞化',
        'ly': '副詞化', 'ate': '動詞化', 'ify': '動詞化', 'ize': '動詞化',
        'er': '人・物', 'or': '人・物', 'ist': '人'
    }
    for suf, role in suffixes.items():
        if word.endswith(suf):
            return f"-{suf} ({role})"
    return "-"

def generate_real_data():
    print("=== データ生成プロセス開始 ===")
    
    # 1. 英和辞書(ejdict)を読み込む
    ejdict = load_ejdict()
    
    etymologies = []
    word_families = []
    words_data = []

    family_id_counter = 1
    word_id_counter = 1

    for prefix in TARGET_PREFIXES:
        etymologies.append({
            "id": prefix["id"],
            "type": "prefix",
            "spelling": prefix["spelling"],
            "meaning": prefix["meaning"]
        })

        # 2. Wiktionaryから単語リスト（接頭辞の確証があるもの）を全件取得
        # limit=None を指定することで無制限に取得します
        fetched_words = fetch_wiktionary_words(prefix["category"], limit=None)
        time.sleep(5) # カテゴリ間の待機時間も2秒から5秒に延長して優しく

        # 3. ejdictに載っている一般的な単語だけを残す（フィルタリング）
        valid_words = []
        for w in fetched_words:
            if w.lower() in ejdict:
                valid_words.append(w)
                
        print(f"  -> 辞書フィルタリング後: {len(valid_words)}件の一般的な単語が残りました！")

        # 4. 語幹でグループ化
        groups = {}
        prefix_clean = prefix['spelling'].replace('-', '')
        
        for w in valid_words:
            base_part = w[len(prefix_clean):] if w.startswith(prefix_clean) else w
            stem_key = base_part[:4] if len(base_part) >= 4 else base_part
            
            if stem_key not in groups:
                groups[stem_key] = []
            groups[stem_key].append(w)

        # 5. データ構造への格納
        for stem_key, words_in_group in groups.items():
            family_id = f"f{family_id_counter}"
            base_word = words_in_group[0] 
            
            word_families.append({
                "id": family_id,
                "etymology_id": prefix["id"],
                "base_word": base_word,
                "explanation": f"「{prefix['spelling']}」と「{stem_key}...」から成る単語"
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
                    "suffix": analyze_suffix(w)
                })
                word_id_counter += 1

    final_data = {
        "etymologies": etymologies,
        "word_families": word_families,
        "words": words_data
    }

    with open('etymology_data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print("✨ すべての処理が完了し、etymology_data.json を更新しました！")

if __name__ == "__main__":
    generate_real_data()
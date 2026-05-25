import json
import requests
import time
import os
import sys
import csv

# ==========================================
# 単語ごとの例外・カスタム設定（統合版）
# ==========================================
WORD_EXCEPTIONS = {
    "office": {
        "exclude_from": ["of"], 
        "custom_prefix": "ope",
        "custom_prefix_meaning": "仕事・富"
    },
    "gooey": {
        "custom_suffix": "y",
        "custom_suffix_role": "のような、満ちた",
        "custom_pos": "形容詞"
    },
    "clayey": {
        "custom_suffix": "y",
        "custom_suffix_role": "のような、満ちた",
        "custom_pos": "形容詞"
    }
}

def load_csv_master(filename):
    """CSVマスターデータを読み込む共通関数"""
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
    """英和辞典（ejdict）を読み込む共通関数"""
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

def load_cache(cache_file):
    """キャッシュを読み込む共通関数"""
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            try:
                print(f"📦 キャッシュファイル '{cache_file}' を読み込みました。")
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return {}

def save_cache(cache, cache_file):
    """キャッシュを保存する共通関数"""
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def fetch_wiktionary_words(category_name, cache, cache_file, limit=None): 
    """Wiktionary APIから単語を取得する共通関数"""
    if category_name in cache:
        print(f"⚡ [{category_name}] キャッシュから即時読み込み", end="", flush=True)
        words = cache[category_name]
        print(f" -> {len(words)}件")
        if limit:
            return words[:limit]
        return words

    url = "https://en.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category_name}",
        "cmnamespace": 0, 
        "cmlimit": 500,
        "format": "json"
    }
    
    headers = {"User-Agent": "EtymologyLearningApp/2.2 (Educational purpose)"}
    
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
    
    cache[category_name] = words
    save_cache(cache, cache_file)

    if limit:
        words = words[:limit]
    return words

def analyze_suffix(word, suffix_master, ejdict):
    """接尾辞の解析・品詞判定を行う共通関数"""
    if not suffix_master:
        return {"display": "-", "pos": "-"}
    
    if word in WORD_EXCEPTIONS and "custom_suffix" in WORD_EXCEPTIONS[word]:
        exc = WORD_EXCEPTIONS[word]
        return {
            "display": f"-{exc['custom_suffix']} ({exc['custom_suffix_role']})",
            "pos": exc.get("custom_pos", "形容詞")
        }
        
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
import json
import time
import sys
from utils import WORD_EXCEPTIONS, load_csv_master, load_ejdict, load_cache, fetch_wiktionary_words

# ==========================================
# 設定
# ==========================================
CACHE_FILE = "wiktionary_cache_root.json"
OUTPUT_ALLOCATIONS_FILE = "root_allocations.json"

def build_root_allocations():
    print("=== 語根データ割り当てプロセス(重い処理) 開始 ===")
    start_time = time.time()
    
    etymology_master = load_csv_master("root_master.csv")
    prefix_master = load_csv_master("prefix_master.csv")
    
    if not etymology_master:
        print("❌ 語根マスターデータが1件もありません。処理を終了します。")
        sys.exit(1)

    ejdict = load_ejdict()
    wiktionary_cache = load_cache(CACHE_FILE)

    common_prefixes = [
        "a", "ab", "abs", "ad", "ac", "af", "ag", "al", "an", "ap", "ar", "as", "at", 
        "con", "com", "col", "cor", "co", "de", "dis", "dif", "di", "en", "em",
        "ex", "e", "ef", "im", "in", "il", "ir", "inter", "intro", "ob", "oc", "of", "op",
        "per", "pre", "pro", "re", "retro", "sub", "suc", "suf", "sug", "sup", "sur", "sus", 
        "trans", "tra", "un", "non", "over", "out", "auto", "anti", "bi", "mono", "poly", "under"
    ]

    # =========================================================================
    # フェーズ 1: Wiktionary API による抽出
    # =========================================================================
    print("\n[フェーズ1] Wiktionary カテゴリからの語根単語抽出を実行します...")
    
    wiktionary_allocations = { ety["id"]: set() for ety in etymology_master }
    assigned_words = set()

    for ety in etymology_master:
        if not ety.get("category"):
            print(f"⚠️ [{ety['spelling']}] は category が設定されていないためスキップします。")
            continue

        raw_category_str = str(ety["category"])
        categories = [c.strip() for c in raw_category_str.split('|') if c.strip()]
        
        fetched_words = []
        is_all_cached = True
        
        for cat in categories:
            if cat not in wiktionary_cache:
                is_all_cached = False
            words_for_cat = fetch_wiktionary_words(cat, wiktionary_cache, CACHE_FILE, limit=None)
            fetched_words.extend(words_for_cat)
            
        fetched_words = list(dict.fromkeys(fetched_words))
        
        if not is_all_cached:
            time.sleep(3) 

        target_spelling = ety["spelling"].lower().replace('-', '')
        
        valid_words_count = 0
        for w in fetched_words:
            w_lower = w.lower()
            
            if w_lower in WORD_EXCEPTIONS and target_spelling in WORD_EXCEPTIONS[w_lower].get("exclude_from", []):
                continue
                
            if w_lower in ejdict:
                if target_spelling not in w_lower:
                    continue
                wiktionary_allocations[ety["id"]].add(w_lower)
                assigned_words.add(w_lower)
                valid_words_count += 1
                
        print(f"  -> {valid_words_count} 件の単語を確定割り当てしました")

    # =========================================================================
    # フェーズ 2: 未割り当て単語の語根補完処理 (最長一致)
    # =========================================================================
    remaining_count = len(ejdict) - len(assigned_words)
    print(f"\n[フェーズ2] 辞書内の未割り当て単語({remaining_count}件)に対する最長一致補完処理を開始します...")
    
    sorted_roots = sorted([r for r in etymology_master], key=lambda x: len(x['spelling'].replace('-', '')), reverse=True)
    sorted_prefixes = sorted([p for p in prefix_master], key=lambda x: len(x['spelling'].replace('-', '')), reverse=True)
    
    rescued_allocations = { ety["id"]: set() for ety in etymology_master }
    
    for dict_word in ejdict.keys():
        if dict_word in assigned_words:
            continue
            
        best_root_id = None
        
        for r in sorted_roots:
            r_spell = r['spelling'].replace('-', '')
            if len(r_spell) < 3: 
                continue
            if dict_word in WORD_EXCEPTIONS and r_spell in WORD_EXCEPTIONS[dict_word].get("exclude_from", []):
                continue
                
            idx = dict_word.find(r_spell)
            if idx == 0:
                best_root_id = r['id']
                break 
            elif idx > 0:
                prefix_part = dict_word[:idx]
                is_valid_prefix = prefix_part in common_prefixes
                if not is_valid_prefix:
                    for p in sorted_prefixes:
                        if p['spelling'].replace('-', '') == prefix_part:
                            is_valid_prefix = True
                            break
                if is_valid_prefix:
                    best_root_id = r['id']
                    break
                    
        if best_root_id:
            rescued_allocations[best_root_id].add(dict_word)

    print("✅ 補完処理が完了しました！")
    
    # 割り当て結果の統合と保存
    final_allocations = {}
    for ety in etymology_master:
        words = list(wiktionary_allocations[ety["id"]] | rescued_allocations[ety["id"]])
        final_allocations[ety["id"]] = words
        
    with open(OUTPUT_ALLOCATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_allocations, f, ensure_ascii=False, indent=2)

    end_time = time.time()
    print(f"\n✨ すべての割り当て処理が完了し、{OUTPUT_ALLOCATIONS_FILE} を生成しました！ (所要時間: {end_time - start_time:.1f}秒)")

if __name__ == "__main__":
    build_root_allocations()
import requests
import pandas as pd
import time
import os

INPUT_CSV = "root_master.csv"
OUTPUT_CSV = "root_master.csv"

def get_pie_root_categories(word):
    """
    Wiktionary API (prop=categories) を使用して、
    指定した単語ページに紐づく PIE root (印欧祖語) のカテゴリ一覧を取得する
    """
    url = "https://en.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "prop": "categories",
        "titles": word,
        "cllimit": 500, # 最大500件のカテゴリを取得
        "format": "json"
    }
    
    headers = {"User-Agent": "EtymologyLearningApp/1.1 (Category Filler)"}
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            # 🌟 429 Too Many Requests エラー対策（リトライロジック）
            if response.status_code == 429:
                print(" ⏳制限到達(10秒待機)... ", end="", flush=True)
                time.sleep(10)
                continue
                
            response.raise_for_status()
            data = response.json()
            break # 成功したらリトライループを抜ける
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"\n[ERROR] APIリクエスト失敗 {word}: {e}")
                return []
            print(" ⏳エラー(5秒待機)... ", end="", flush=True)
            time.sleep(5)
        
    found_categories = []
    pages = data.get("query", {}).get("pages", {})
    
    for page_id, page_info in pages.items():
        # ページが存在しない場合（page_idが負の値）はスキップ
        if "categories" in page_info:
            for cat in page_info["categories"]:
                title = cat["title"]
                
                # 印欧祖語の語根カテゴリを探す（"Middle English"などを除外し、現代英語に限定する）
                if title.startswith("Category:English terms derived from the Proto-Indo-European root"):
                    # "Category:" という接頭辞を外し、スペースをアンダースコアに置換（アプリの仕様に合わせる）
                    clean_title = title.replace("Category:", "").replace(" ", "_")
                    found_categories.append(clean_title)
                    
    return found_categories

def fill_categories():
    if not os.path.exists(INPUT_CSV):
        print(f"⚠️ {INPUT_CSV} が見つかりません。")
        return

    print(f"📁 {INPUT_CSV} を読み込み中...")
    df = pd.read_csv(INPUT_CSV)
    
    # 型推論エラーを防ぐ
    if "category" not in df.columns:
        df["category"] = None
    df["category"] = df["category"].astype(object)
    
    updated_count = 0

    # iterrows() ではなく、インデックスでループする（動的な更新を即座に反映させるため）
    for idx in df.index:
        current_category = df.at[idx, "category"]
        
        # すでにカテゴリが入力されている場合はスキップ
        if pd.notna(current_category) and str(current_category).strip() != "":
            continue

        word = str(df.at[idx, "spelling"])
        meaning = str(df.at[idx, "meaning"])
        print(f"🔍 検索中: {word} ... ", end="", flush=True)

        categories = get_pie_root_categories(word)

        if categories:
            # 複数のカテゴリが見つかった場合（多義語など）は、' | ' で繋いで保存する
            joined_cats = " | ".join(categories)
            
            # 🌟 【重要】同じ意味(meaning)を持つ「他の空欄の行」も一気に埋める横展開ロジック
            mask = (df["meaning"] == meaning) & (df["category"].isnull() | (df["category"] == ""))
            update_count_for_meaning = mask.sum()
            
            # 条件に合致する行を一括更新
            df.loc[mask, "category"] = joined_cats
            
            if update_count_for_meaning > 1:
                print(f"✅ 発見({len(categories)}件) ➔ 仲間の語根 {update_count_for_meaning} 件に一括適用しました！")
            else:
                print(f"✅ 見つかりました ({len(categories)}件)")
                
            updated_count += update_count_for_meaning
        else:
            print("❌ 見つかりませんでした")
            
        # APIの負荷軽減のためのウェイト
        time.sleep(1.5)

    # 保存
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n✨ 処理完了！ {updated_count} 件のカテゴリを補完し、{OUTPUT_CSV} に保存しました。")

if __name__ == "__main__":
    print("=== Wiktionary 語根カテゴリ自動補完プロセス開始 ===")
    fill_categories()
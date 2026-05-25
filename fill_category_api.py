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
    data = None  # 🌟 初期値を設定してUnboundLocalErrorを防ぐ
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            # 🌟 429 Too Many Requests エラー対策
            if response.status_code == 429:
                wait_time = 10 * (attempt + 1)  # 10秒, 20秒, 30秒と待機を延ばす
                print(f" ⏳制限到達({wait_time}秒待機)... ", end="", flush=True)
                time.sleep(wait_time)
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
            
    # 🌟 リトライ回数を使い切っても取得できなかった場合はスキップ
    if data is None:
        print(" ❌リトライ上限到達... ", end="", flush=True)
        return []
        
    found_categories = []
    pages = data.get("query", {}).get("pages", {})
    
    for page_id, page_info in pages.items():
        if "categories" in page_info:
            for cat in page_info["categories"]:
                title = cat["title"]
                if title.startswith("Category:English terms derived from the Proto-Indo-European root"):
                    clean_title = title.replace("Category:", "").replace(" ", "_")
                    found_categories.append(clean_title)
                    
    return found_categories

def fill_categories():
    if not os.path.exists(INPUT_CSV):
        print(f"⚠️ {INPUT_CSV} が見つかりません。")
        return

    print(f"📁 {INPUT_CSV} を読み込み中...")
    df = pd.read_csv(INPUT_CSV)
    
    if "category" not in df.columns:
        df["category"] = None
    df["category"] = df["category"].astype(object)
    
    # 処理開始前の空欄の数をカウント
    initial_empty_mask = df["category"].isnull() | (df["category"] == "")
    initial_empty_count = initial_empty_mask.sum()
    
    print("🌐 全ての空欄の単語に対して個別にAPIリクエストを実行します...")

    for idx in df.index:
        current_category = df.at[idx, "category"]
        
        # すでにカテゴリが入力されている場合はスキップ
        if pd.notna(current_category) and str(current_category).strip() != "":
            continue

        word = str(df.at[idx, "spelling"])
        
        print(f"🔍 検索中: {word} ... ", end="", flush=True)

        categories = get_pie_root_categories(word)

        if categories:
            joined_cats = " | ".join(categories)
            # その単語単体にカテゴリを保存
            df.at[idx, "category"] = joined_cats
            print(f"✅ 見つかりました ({len(categories)}件)")
        else:
            print("❌ 見つかりませんでした")
            
        # APIの負荷軽減のためのウェイト
        time.sleep(2.0)

    print("\n🔄 取得できなかった単語に対し、同じ意味を持つ仲間の語根からカテゴリを補完しています...")
    
    # 全件検索終了後、カテゴリが取得できているデータをベースに辞書を作成
    valid_categories = df[df["category"].notna() & (df["category"] != "")]
    # 同じ意味で複数の異なるカテゴリが存在する場合は、最初に見つかったものを採用する
    category_map = valid_categories.drop_duplicates(subset=["meaning"]).set_index("meaning")["category"].to_dict()
    
    # カテゴリが空のままの行に対して、マッピング辞書から補完を試みる
    empty_mask = df["category"].isnull() | (df["category"] == "")
    mapped_categories = df.loc[empty_mask, "meaning"].map(category_map)
    
    # マップから値が取得できた（補完できた）行のみを更新
    update_mask = empty_mask & mapped_categories.notna()
    df.loc[update_mask, "category"] = mapped_categories[update_mask]
    
    complemented_count = update_mask.sum()
    if complemented_count > 0:
        print(f"💡 {complemented_count} 件の単語を仲間の語根から補完しました！")
    else:
        print("💡 補完対象の単語はありませんでした。")

    # 処理完了後の空欄の数をカウントし、更新された総件数を算出
    final_empty_mask = df["category"].isnull() | (df["category"] == "")
    final_empty_count = final_empty_mask.sum()
    updated_count = initial_empty_count - final_empty_count

    # 保存
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n✨ 処理完了！ 合計 {updated_count} 件のカテゴリを新たに取得・補完し、{OUTPUT_CSV} に保存しました。")

if __name__ == "__main__":
    print("=== Wiktionary 語根カテゴリ自動補完プロセス開始 ===")
    fill_categories()
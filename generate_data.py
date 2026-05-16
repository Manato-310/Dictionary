import json
import requests
import time

# 取得したい語源（今回は接頭辞の例）を定義
TARGET_PREFIXES = [
    {"id": "e1", "spelling": "pre-", "meaning": "前に、あらかじめ", "category": "English_words_prefixed_with_pre-"},
    {"id": "e2", "spelling": "re-", "meaning": "再び、後ろに", "category": "English_words_prefixed_with_re-"},
    {"id": "e3", "spelling": "sub-", "meaning": "下に、副次的な", "category": "English_words_prefixed_with_sub-"}
]

def fetch_wiktionary_words(category_name, limit=15):
    """Wiktionary APIを使って特定のカテゴリに属する英単語を取得する"""
    url = "https://en.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category_name}",
        "cmnamespace": 0, # 通常の単語ページのみ
        "cmlimit": limit,
        "format": "json"
    }
    
    # Wikimedia APIの要件に従い、User-Agentヘッダーを追加
    headers = {
        "User-Agent": "EtymologyLearningApp/1.0 (Educational purpose)"
    }
    
    print(f"[{category_name}] の単語をWiktionaryから取得中...")
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status() # HTTPステータスコードが200以外ならエラーを投げる
        data = response.json()
    except Exception as e:
        print(f"APIリクエストエラー: {e}")
        print(f"レスポンス内容: {response.text[:200]}") # エラー原因を見やすくする
        return []
    
    words = []
    if "query" in data and "categorymembers" in data["query"]:
        for member in data["query"]["categorymembers"]:
            words.append(member["title"])
    return words

def generate_real_data():
    etymologies = []
    word_families = []
    words_data = []

    family_id_counter = 1
    word_id_counter = 1

    for prefix in TARGET_PREFIXES:
        # 1. etymologies の作成
        etymologies.append({
            "id": prefix["id"],
            "type": "prefix",
            "spelling": prefix["spelling"],
            "meaning": prefix["meaning"]
        })

        # 2. APIでWiktionaryから単語リストを取得
        fetched_words = fetch_wiktionary_words(prefix["category"])
        time.sleep(1) # サーバーに負荷をかけないよう1秒待機

        # 今回は簡易的に、取得した単語を1つの family にまとめる
        family_id = f"f{family_id_counter}"
        word_families.append({
            "id": family_id,
            "etymology_id": prefix["id"],
            "base_word": f"{prefix['spelling']} words",
            "explanation": f"Wiktionaryから取得した {prefix['spelling']} を含む単語群"
        })
        family_id_counter += 1

        # 3. words の作成
        for w in fetched_words:
            # 実際のAPIから品詞や日本語訳を取得するのは非常に処理が重いため、今回はダミーを入れます
            words_data.append({
                "id": f"w{word_id_counter}",
                "family_id": family_id,
                "spelling": w,
                "part_of_speech": "調査中",
                "meaning": "(Wiktionary連携済)", 
                "suffix": "-"
            })
            word_id_counter += 1

    # 最終的なJSON構造にまとめる
    final_data = {
        "etymologies": etymologies,
        "word_families": word_families,
        "words": words_data
    }

    # ファイルに保存
    with open('etymology_data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print("✨ Wiktionaryからのデータ取得と etymology_data.json の更新が完了しました！")

if __name__ == "__main__":
    generate_real_data()
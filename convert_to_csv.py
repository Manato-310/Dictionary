import csv
import os

def convert_prefix_root(input_file, output_file, ety_type):
    if not os.path.exists(input_file):
        print(f"⚠️ {input_file} が見つかりません。")
        return

    data = []
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    id_counter = 1
    for line in lines:
        parts = line.strip().split("\t")
        # 修正: 2列のデータを処理するように変更
        if len(parts) >= 2:
            spellings = parts[0]
            meaning = parts[1]

            # カンマで分割して独立行として登録
            for sp in spellings.split(","):
                sp_clean = sp.strip()
                
                id_prefix = "e" if ety_type == "prefix" else "r"
                category = f"English_terms_prefixed_with_{sp_clean}" if ety_type == "prefix" else ""

                data.append({
                    "id": f"{id_prefix}{id_counter}",
                    "type": ety_type,
                    "spelling": sp_clean,
                    "meaning": meaning,
                    "category": category
                })
                id_counter += 1

    # 🌟 utf-8-sig で保存し、最初からBOM問題を回避する
    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "type", "spelling", "meaning", "category"])
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ {output_file} を生成しました（{len(data)}件）。")


def get_pos_from_role(suffix, role):
    """接尾辞のつづりと日本語の役割テキストから、品詞を高精度で推測する"""
    poses = set()
    
    # 1. テキスト内の明示的なキーワードで判定（最優先）
    if "名詞化" in role or "抽象名詞" in role:
        poses.add("名詞")
    if "形容詞化" in role:
        poses.add("形容詞")
    if "動詞化" in role:
        poses.add("動詞")
    if "副詞化" in role:
        poses.add("副詞")

    # 2. 日本語の意味（役割）からの推測
    # 動詞的な表現
    if "～させる" in role or "～にする" in role or "～を生じる" in role or role == "する":
        poses.add("動詞")

    # 形容詞的な表現
    adj_keywords = [
        "のような", "できる", "しうる", "され得る", "満ちた", "無い", "のない", 
        "ふさわしい", "～の性質", "～に関連した", "～に適した", "特有", "固有", 
        "～らしい", "～重", "～倍", "の傾向がある", "～関連の", "～系の"
    ]
    if any(k in role for k in adj_keywords) or role.endswith("の") or "～の、" in role:
        poses.add("形容詞")

    # 副詞的な表現
    if "のように" in role or "方向" in role:
        poses.add("副詞")

    # 名詞的な表現 (明確に名詞を示すキーワードを多数追加)
    noun_keywords = [
        "こと", "もの", "人", "学", "主義", "主張", "場所", "状態", "病気", "物質", 
        "政治", "法", "規則", "地位", "恐怖症", "面体", "行為", "結果", 
        "資格", "役職", "器械", "鏡", "症", "語", "スキャンダル", "職人", 
        "尺度", "粉末", "細胞", "生物", "植物", "動物", "岩", "微生物", "皮膚", 
        "形状", "地震", "振動", "信仰", "藍色", "嚢", "用語", "言葉", "君主", "星", 
        "層", "肉", "度", "術", "土地", "部分", "球", "音", "作品", "工芸品", "足"
    ]
    if any(k in role for k in noun_keywords):
        poses.add("名詞")

    # 3. テキストから判定できなかった場合、つづりから推測 (フォールバック)
    if not poses:
        if suffix in ["ate", "ize", "ise", "ify", "en", "le", "fy"]: 
            poses.add("動詞")
        elif suffix in ["ly", "ward", "wards", "fold", "wise"]: 
            poses.add("副詞")
        elif suffix in ["ic", "ous", "ar", "fic", "ish", "al", "able", "ible", "ble", "tic", "se", "related", "specific", "lingual", "proof", "biotic", "long", "worthy", "plastic", "clastic", "clinic", "metric"]: 
            poses.add("形容詞")
        else:
            poses.add("名詞") # 最終的なデフォルト

    # 複数の品詞が見つかった場合、決まった順序で結合して返す
    order = {"名詞": 1, "動詞": 2, "形容詞": 3, "副詞": 4}
    sorted_poses = sorted(list(poses), key=lambda x: order.get(x, 99))
    
    # "名詞・形容詞" のように「・」で繋いで返す
    return "・".join(sorted_poses)


def convert_suffix(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"⚠️ {input_file} が見つかりません。")
        return

    data = []
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        parts = line.strip().split("\t")
        # 修正: 2列のデータを処理するように変更
        if len(parts) >= 2:
            spellings = parts[0]
            role = parts[1]

            for sp in spellings.split(","):
                sp_clean = sp.strip().replace("-", "") 
                pos = get_pos_from_role(sp_clean, role)

                data.append({
                    "suffix": sp_clean,
                    "role": role,
                    "pos": pos
                })

    # 🌟 utf-8-sig で保存
    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["suffix", "role", "pos"])
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ {output_file} を生成しました（{len(data)}件）。")


if __name__ == "__main__":
    print("=== マスターデータCSV変換プロセス開始 (utf-8-sig版) ===")
    convert_prefix_root("prefix.txt", "prefix_master.csv", "prefix")
    convert_prefix_root("root.txt", "root_master.csv", "root")
    convert_suffix("suffix.txt", "suffix_master.csv")
    print("✨ すべての変換が完了しました！")
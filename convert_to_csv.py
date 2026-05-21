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
    if suffix in ["ate", "ize", "ise", "ify", "en", "le"]: return "動詞"
    if suffix in ["ly", "ward", "fold"]: return "副詞"
    if suffix in ["ic", "ous", "ar", "fic", "ish"]: return "形容詞"
        
    if "のように" in role: return "副詞"
    if "のような" in role or "できる" in role or "しうる" in role or "満ちた" in role or "無い" in role: return "形容詞"
    if role == "する" or role.startswith("する、"): return "動詞"
        
    noun_keywords = ["こと", "もの", "人", "学問", "主義", "主張", "場所", "状態", "病気", "物質", "政治", "法", "規則", "関係", "地位", "恐怖症", "面体"]
    if any(k in role for k in noun_keywords): return "名詞"
        
    return "名詞"


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
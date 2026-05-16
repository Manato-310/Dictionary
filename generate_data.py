import json
import os

def generate_dummy_data():
    """
    Wiktionaryのデータを模した、語源学習用の3階層ダミーデータを生成します。
    実際のアプリ運用時は、この部分をWiktionary APIやダンプ解析ロジックに置き換えます。
    """
    data = {
        "etymologies": [
            {
                "id": "e1",
                "type": "prefix",
                "spelling": "pre-",
                "meaning": "前に、あらかじめ (before, in advance)"
            },
            {
                "id": "e2",
                "type": "root",
                "spelling": "spect",
                "meaning": "見る (look, see)"
            },
            {
                "id": "e3",
                "type": "prefix",
                "spelling": "pro-",
                "meaning": "前に、賛成して (forward, in favor of)"
            },
            {
                "id": "e4",
                "type": "root",
                "spelling": "dict",
                "meaning": "言う (say, speak)"
            }
        ],
        "word_families": [
            {
                "id": "f1",
                "etymology_id": "e1",
                "base_word": "predict",
                "explanation": "pre(前に) + dict(言う) = 前もって言う、予測する"
            },
            {
                "id": "f2",
                "etymology_id": "e1",
                "base_word": "prepare",
                "explanation": "pre(前に) + pare(整える) = 前もって整える、準備する"
            },
            {
                "id": "f3",
                "etymology_id": "e2",
                "base_word": "inspect",
                "explanation": "in(中に) + spect(見る) = 中を詳しく見る、検査する"
            },
            {
                "id": "f4",
                "etymology_id": "e2",
                "base_word": "respect",
                "explanation": "re(再び) + spect(見る) = 何度も振り返って見る、尊敬する"
            },
            {
                "id": "f5",
                "etymology_id": "e4",
                "base_word": "predict", # etymology e1 (pre) にも属するが、ここでは root (dict) の例として
                "explanation": "pre(前に) + dict(言う) = 前もって言う、予測する"
            },
            {
                "id": "f6",
                "etymology_id": "e4",
                "base_word": "dictate",
                "explanation": "dict(言う) + ate(動詞化) = 言いつける、書き取りをさせる"
            }
        ],
        "words": [
            # Family f1 (predict) の派生語
            {"id": "w1", "family_id": "f1", "spelling": "predict", "part_of_speech": "動詞", "meaning": "予測する、予言する", "suffix": "-"},
            {"id": "w2", "family_id": "f1", "spelling": "prediction", "part_of_speech": "名詞", "meaning": "予測、予言", "suffix": "-tion (名詞化)"},
            {"id": "w3", "family_id": "f1", "spelling": "predictable", "part_of_speech": "形容詞", "meaning": "予測可能な、当たり前の", "suffix": "-able (可能)"},
            
            # Family f2 (prepare) の派生語
            {"id": "w4", "family_id": "f2", "spelling": "prepare", "part_of_speech": "動詞", "meaning": "準備する", "suffix": "-"},
            {"id": "w5", "family_id": "f2", "spelling": "preparation", "part_of_speech": "名詞", "meaning": "準備、用意", "suffix": "-ation (名詞化)"},
            {"id": "w6", "family_id": "f2", "spelling": "preparatory", "part_of_speech": "形容詞", "meaning": "準備の、予備の", "suffix": "-ory (形容詞化)"},
            
            # Family f3 (inspect) の派生語
            {"id": "w7", "family_id": "f3", "spelling": "inspect", "part_of_speech": "動詞", "meaning": "検査する、視察する", "suffix": "-"},
            {"id": "w8", "family_id": "f3", "spelling": "inspection", "part_of_speech": "名詞", "meaning": "検査、視察", "suffix": "-tion (名詞化)"},
            {"id": "w9", "family_id": "f3", "spelling": "inspector", "part_of_speech": "名詞", "meaning": "検査官、警部", "suffix": "-or (人)"},
            
            # Family f4 (respect) の派生語
            {"id": "w10", "family_id": "f4", "spelling": "respect", "part_of_speech": "動詞/名詞", "meaning": "尊敬する / 尊敬", "suffix": "-"},
            {"id": "w11", "family_id": "f4", "spelling": "respectable", "part_of_speech": "形容詞", "meaning": "ちゃんとした、立派な（尊敬できる）", "suffix": "-able (可能)"},
            {"id": "w12", "family_id": "f4", "spelling": "respectful", "part_of_speech": "形容詞", "meaning": "敬意に満ちた、礼儀正しい", "suffix": "-ful (満ちた)"},
            {"id": "w13", "family_id": "f4", "spelling": "respective", "part_of_speech": "形容詞", "meaning": "それぞれの、各自の", "suffix": "-ive (性質)"},

            # Family f5, f6 (dict 関連 - 一部重複するが、idは分ける)
            {"id": "w14", "family_id": "f5", "spelling": "predict", "part_of_speech": "動詞", "meaning": "予測する", "suffix": "-"},
            {"id": "w15", "family_id": "f6", "spelling": "dictate", "part_of_speech": "動詞", "meaning": "書き取らせる、命令する", "suffix": "-ate (動詞化)"},
            {"id": "w16", "family_id": "f6", "spelling": "dictator", "part_of_speech": "名詞", "meaning": "独裁者", "suffix": "-or (人)"},
            {"id": "w17", "family_id": "f6", "spelling": "dictation", "part_of_speech": "名詞", "meaning": "書き取り、口述", "suffix": "-tion (名詞化)"}
        ]
    }
    return data

def main():
    print("ダミーデータの生成を開始します...")
    data = generate_dummy_data()
    
    output_filename = "etymology_data.json"
    
    # データをJSONファイルとして保存
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"データの生成が完了しました: {os.path.abspath(output_filename)}")
    print(f"etymologies: {len(data['etymologies'])}件")
    print(f"word_families: {len(data['word_families'])}件")
    print(f"words: {len(data['words'])}件")

if __name__ == "__main__":
    main()
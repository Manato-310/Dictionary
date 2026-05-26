import streamlit as st
import json
import pandas as pd

# ページの基本設定
st.set_page_config(page_title="語源で学ぶ英単語帳", page_icon="📚", layout="wide")

# カスタムCSS（Gogengo風のカードとバッジデザイン）
st.markdown("""
<style>
    /* カード全体のスタイル */
    .word-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .word-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.12);
    }
    .base-word-title {
        font-size: 1.8em;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .ety-parent-info {
        font-size: 0.85em;
        color: #7f8c8d;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid #f0f0f0;
    }
    
    /* 語源パーツ（バッジ）のスタイル */
    .ety-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.95em;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .badge-prefix { background-color: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }
    .badge-root { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
    .badge-suffix { background-color: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb; }
    .badge-other { background-color: #f5f5f5; color: #616161; border: 1px solid #e0e0e0; }

    /* 派生語リストのスタイル */
    .derivative-container {
        background-color: #fafafa; 
        padding: 15px; 
        border-radius: 8px; 
        margin-top: 15px; 
        border: 1px solid #eee;
    }
    .derivative-item {
        border-bottom: 1px dashed #e0e0e0;
        padding: 10px 0;
        display: flex;
        align-items: baseline;
        flex-wrap: wrap;
    }
    .derivative-item:last-child {
        border-bottom: none;
    }
    .derivative-spelling {
        font-size: 1.25em;
        font-weight: bold;
        color: #1a73e8;
        min-width: 150px;
    }
    .derivative-pos {
        font-size: 0.8em;
        background-color: #eceff1;
        color: #546e7a;
        padding: 3px 8px;
        border-radius: 12px;
        margin-right: 12px;
        font-weight: bold;
    }
    .derivative-suffix {
        font-size: 0.85em; 
        color: #888;
        margin-right: 15px;
    }
    .derivative-meaning {
        color: #424242;
        flex-grow: 1;
        font-size: 1.05em;
    }
    
    /* ヘッダーリボン */
    .ety-header {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 24px;
        border-radius: 12px;
        border-left: 6px solid #4a90e2;
        margin-bottom: 30px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """prefix_data.json と root_data.json を読み込んで結合する"""
    merged_data = {
        "etymologies": [],
        "word_families": [],
        "words": []
    }
    
    files_loaded = 0

    # 接頭辞データの読み込み
    try:
        with open('prefix_data.json', 'r', encoding='utf-8') as f:
            prefix_data = json.load(f)
            merged_data["etymologies"].extend(prefix_data.get("etymologies", []))
            merged_data["word_families"].extend(prefix_data.get("word_families", []))
            merged_data["words"].extend(prefix_data.get("words", []))
            files_loaded += 1
    except FileNotFoundError:
        pass

    # 語根データの読み込み
    try:
        with open('root_data.json', 'r', encoding='utf-8') as f:
            root_data = json.load(f)
            merged_data["etymologies"].extend(root_data.get("etymologies", []))
            merged_data["word_families"].extend(root_data.get("word_families", []))
            merged_data["words"].extend(root_data.get("words", []))
            files_loaded += 1
    except FileNotFoundError:
        pass

    if files_loaded == 0:
        st.error("データファイル (`prefix_data.json`, `root_data.json`) が見つかりません。先にエクスポートスクリプトを実行してください。")
        return None

    return merged_data

def render_word_family_card(family, related_words, parent_ety=None):
    """1つの単語グループ(family)をカード形式で描画するコンポーネント"""
    card_html = f"<div class='word-card'>"
    
    # タイトル
    card_html += f"<div class='base-word-title'>🌳 {family['base_word']}</div>"
    
    # 検索画面用：親の語源情報を表示
    if parent_ety:
        ety_type_str = "接頭辞" if parent_ety['type'] == 'prefix' else "語根"
        card_html += f"<div class='ety-parent-info'>💡 属する語源: <b>{parent_ety['spelling']}</b> ({ety_type_str} / {parent_ety['meaning']})</div>"
    
    # 構造化データ(explanation_parts)によるバッジ表示
    if 'explanation_parts' in family and family['explanation_parts']:
        badges_html = "<div style='margin-bottom: 10px;'>"
        for part in family['explanation_parts']:
            ptype = part.get('type', 'other')
            badge_class = f"badge-{ptype}"
            text = part.get('text', '')
            meaning = part.get('meaning', '')
            display_text = f"{text} ({meaning})" if meaning and meaning != "?" else text
            badges_html += f"<span class='ety-badge {badge_class}'>{display_text}</span>"
        badges_html += "</div>"
        card_html += badges_html
    else:
        # フォールバック
        card_html += f"<div style='margin-bottom: 10px; color: #555;'>📖 <b>成り立ち:</b> {family.get('explanation', '')}</div>"

    # 派生語リスト
    if related_words:
        card_html += "<div class='derivative-container'>"
        for w in related_words:
            spelling = w['spelling']
            pos = w.get('part_of_speech', '')
            meaning = w.get('meaning', '')
            suffix_info = w.get('suffix', '-')
            
            suffix_display = f"<span class='derivative-suffix'>[接尾辞: {suffix_info}]</span>" if suffix_info != "-" else ""
            
            # StreamlitのMarkdownパーサーによるHTMLエスケープを防ぐため、改行を含めずに1行で連結します
            card_html += f"<div class='derivative-item'><span class='derivative-spelling'>{spelling}</span><span class='derivative-pos'>{pos}</span>{suffix_display}<span class='derivative-meaning'>{meaning}</span></div>"
            
        card_html += "</div>"
    else:
        card_html += "<div style='color: #888; font-size: 0.9em; margin-top: 10px;'>派生語は登録されていません。</div>"

    card_html += "</div>"
    st.markdown(card_html, unsafe_allow_html=True)


def render_browse_mode(data):
    """語源から探すモードの描画"""
    etymologies = data.get('etymologies', [])
    word_families = data.get('word_families', [])
    words = data.get('words', [])

    ety_type_jp = st.sidebar.radio("カテゴリを選択", ["接頭辞 (Prefix)", "語根 (Root)"])
    ety_type_en = "prefix" if "Prefix" in ety_type_jp else "root"

    group_by_meaning = st.sidebar.checkbox("同じ意味の語源をまとめる", value=False)

    filtered_etymologies = [e for e in etymologies if e['type'] == ety_type_en]
    
    if not filtered_etymologies:
        st.sidebar.warning(f"現在、{ety_type_jp}のデータがありません。")
        return

    if group_by_meaning:
        # 意味でグループ化する処理
        grouped_ety = {}
        for e in filtered_etymologies:
            meaning = e['meaning']
            if meaning not in grouped_ety:
                grouped_ety[meaning] = {'spellings': [], 'ids': [], 'meaning': meaning}
            grouped_ety[meaning]['spellings'].append(e['spelling'])
            grouped_ety[meaning]['ids'].append(e['id'])
        
        display_etymologies = []
        for meaning, grp_data in grouped_ety.items():
            # 重複を省きアルファベット順にしてカンマ区切りで結合
            sorted_spellings = sorted(list(set(grp_data['spellings'])), key=lambda s: s.lower())
            combined_spelling = ", ".join(sorted_spellings)
            display_etymologies.append({
                'display_name': combined_spelling,
                'meaning': meaning,
                'ids': grp_data['ids']
            })
        
        # 結合後の綴りでアルファベット順にソート
        display_etymologies = sorted(display_etymologies, key=lambda x: x['display_name'].lower())
        
        selected_ety = st.sidebar.selectbox(
            "語源を選択してください", 
            display_etymologies,
            format_func=lambda x: x['display_name']
        )
        selected_ids = selected_ety['ids']
        header_spelling = selected_ety['display_name']
        header_meaning = selected_ety['meaning']

    else:
        # アルファベット順（綴り）、次に意味の順でソート（同じ綴り・意味のものを連続させる）
        filtered_etymologies = sorted(filtered_etymologies, key=lambda x: (x['spelling'].lower(), x['meaning']))
    
        selected_ety = st.sidebar.selectbox(
            "語源を選択してください", 
            filtered_etymologies,
            format_func=lambda x: x['spelling']
        )
        selected_ids = [selected_ety['id']]
        header_spelling = selected_ety['spelling']
        header_meaning = selected_ety['meaning']

    # リッチなヘッダー表示
    st.markdown(f"""
    <div class="ety-header">
        <h2 style="margin-top: 0; color: #2c3e50; font-size: 2.2em;">🔍 {header_spelling}</h2>
        <p style="font-size: 1.2em; margin-bottom: 0; color: #424242;">
            <strong>コアとなる意味:</strong> {header_meaning}
        </p>
    </div>
    """, unsafe_allow_html=True)

    related_families = [f for f in word_families if f['etymology_id'] in selected_ids]

    if not related_families:
        st.info("関連する単語が登録されていません。")
        return

    # 該当するfamilyをカードで表示
    for family in related_families:
        related_words = [w for w in words if w['family_id'] == family['id']]
        render_word_family_card(family, related_words)


def render_search_mode(data):
    """単語・意味から探すモードの描画"""
    st.title("🔎 単語・意味から検索")
    st.markdown("英単語の綴りや、日本語の意味から単語とその語源グループを検索できます。")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("検索キーワード (例: struct, 構築, 会社)", "")
    
    with col2:
        # 存在する品詞のリストを動的に取得
        all_pos_raw = set(w.get('part_of_speech', '不明') for w in data.get('words', []))
        all_pos = sorted(list(all_pos_raw))
        selected_pos = st.selectbox("品詞で絞り込み", ["すべて"] + all_pos)

    if search_query:
        query = search_query.lower().strip()
        words = data.get('words', [])
        
        # フィルタリング処理
        matched_words = []
        for w in words:
            match_spell = query in w.get('spelling', '').lower()
            match_meaning = query in w.get('meaning', '')
            match_pos = (selected_pos == "すべて") or (w.get('part_of_speech') == selected_pos)
            
            if (match_spell or match_meaning) and match_pos:
                matched_words.append(w)
                
        if not matched_words:
            st.warning(f"「{search_query}」に一致する単語は見つかりませんでした。")
            return
            
        st.success(f"{len(matched_words)} 件の単語がヒットしました！")
        
        # ヒットした単語を family (語源グループ) ごとにまとめる
        hit_family_ids = set(w['family_id'] for w in matched_words)
        hit_families = [f for f in data.get('word_families', []) if f['id'] in hit_family_ids]
        
        for family in hit_families:
            # 親の語源情報を取得
            parent_ety = next((e for e in data.get('etymologies', []) if e['id'] == family['etymology_id']), None)
            
            # このfamilyの中で、検索にヒットした単語のみを抽出して表示する
            family_hit_words = [w for w in matched_words if w['family_id'] == family['id']]
            
            render_word_family_card(family, family_hit_words, parent_ety)
    else:
        st.info("👆 キーワードを入力すると、ここに結果のカードが表示されます。")


def main():
    data = load_data()
    if not data:
        return

    st.sidebar.title("📚 語源で学ぶ英単語")
    st.sidebar.markdown("---")
    
    app_mode = st.sidebar.radio("🧭 モード選択", ["📖 語源から探す", "🔎 単語・意味から探す"])
    st.sidebar.markdown("---")

    if "語源から探す" in app_mode:
        render_browse_mode(data)
    else:
        render_search_mode(data)

if __name__ == "__main__":
    main()
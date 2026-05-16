import streamlit as st
import json
import pandas as pd

# ページの基本設定
st.set_page_config(page_title="語源で学ぶ英単語帳", page_icon="📚", layout="wide")

# データの読み込み
@st.cache_data
def load_data():
    try:
        with open('etymology_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("データファイル (etymology_data.json) が見つかりません。先にデータを準備してください。")
        return None

def main():
    data = load_data()
    if not data:
        return

    etymologies = data['etymologies']
    word_families = data['word_families']
    words = data['words']

    # --- サイドバーのUI構築 ---
    st.sidebar.title("📚 語源で学ぶ英単語帳")
    st.sidebar.markdown("---")
    
    # 語源のタイプ（接頭辞/語根）を選択
    ety_type_jp = st.sidebar.radio("検索カテゴリ", ["接頭辞 (Prefix)", "語根 (Root)"])
    ety_type_en = "prefix" if "Prefix" in ety_type_jp else "root"

    # 選択されたタイプの語源リストを作成
    filtered_etymologies = [e for e in etymologies if e['type'] == ety_type_en]
    
    if not filtered_etymologies:
        st.sidebar.warning(f"現在、{ety_type_jp}のデータがありません。")
        return

    # 語源を選択するプルダウン
    ety_options = {f"{e['spelling']} ({e['meaning']})": e for e in filtered_etymologies}
    selected_ety_label = st.sidebar.selectbox("語源を選択してください", list(ety_options.keys()))
    selected_ety = ety_options[selected_ety_label]

    st.sidebar.markdown("---")
    st.sidebar.info("💡 **学習のヒント**\n\n語源を理解することで、初めて見る単語の意味も推測しやすくなります。")

    # --- メインエリアのUI構築 ---
    # 1. 選択された語源のハイライト表示
    st.title(f"🔍 {selected_ety['spelling']}")
    st.info(f"**コアとなる意味:** {selected_ety['meaning']}")

    st.markdown("### 関連する単語グループ")

    # 2. 該当する word_families を抽出
    related_families = [f for f in word_families if f['etymology_id'] == selected_ety['id']]

    if not related_families:
        st.write("関連する単語が登録されていません。")
        return

    # 3. 各単語グループ(family)をループで表示
    for family in related_families:
        with st.container():
            st.markdown(f"#### 🌳 {family['base_word']}")
            st.write(f"📖 **成り立ち:** {family['explanation']}")
            
            # その family に属する words (派生語) を抽出してテーブル表示
            related_words = [w for w in words if w['family_id'] == family['id']]
            
            if related_words:
                # pandas DataFrameを使って見やすいテーブルを作成
                df = pd.DataFrame(related_words)
                df_display = df[['spelling', 'part_of_speech', 'meaning', 'suffix']]
                df_display.columns = ['単語', '品詞', '意味', '接尾辞・特徴']
                
                # インデックスを非表示にしてテーブルを表示
                st.table(df_display)
            else:
                st.write("派生語は登録されていません。")
            
            st.markdown("---")

if __name__ == "__main__":
    main()
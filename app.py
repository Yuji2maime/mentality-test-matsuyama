import streamlit as st
from supabase import create_client
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go

# 1. ページ基本設定（当日用）
st.set_page_config(
    page_title="思考・表現力セッション（当日用）",
    page_icon="🔴",
    layout="wide"
)

# カスタムCSS（当日用：赤系デザイン）
st.markdown("""
<style>
    .day-banner {
        background-color: #800000;
        color: #FFFFFF !important;
        padding: 16px 18px;
        border-radius: 6px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #800000;
        color: white;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: #A52A2A;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Supabase接続情報
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Gemini API設定
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# ----------------------------------------------------
# 補助関数・分析ロジック
# ----------------------------------------------------
def analyze_text_simple(text):
    """Gemini APIを用いて記述テキストを分析し、5項目のスコアと診断レポートを生成する"""
    prompt = """以下の応募者の記述テキストを分析し、5つの指標（各20点満点、合計100点満点）で評価し、それぞれの評価理由、総合的な思考・認知特性のレポート、深掘り質問案を作成してください。

【評価項目】
1. 構造化思考力 (Logical Structure): 筋立てて分かりやすく論理的に構成されているか
2. 主体的姿勢・当事者意識 (Proactive & Ownership): 他者任せにせず、当事者として主体的に取り組んでいるか
3. 課題発見・分析力 (Problem Solving & Analysis): 本質的な課題を見極め、多角的に分析できているか
4. 協調性・共感力 (Collaboration & Empathy): 周囲との調和を重んじ、共感的なコミュニケーションが取れるか
5. 改善・成長意欲 (Growth Mindset): 経験から学び、前向きに改善・成長しようとする姿勢があるか

【応募者テキスト】
{text}

以下のJSON形式、およびテキスト形式で正確に出力してください。
JSONのキー名やフォーマットは崩さないでください。

```json
{
    "score_logical": 15,
    "score_proactive": 15,
    "score_analysis": 14,
    "score_empathy": 15,
    "score_growth": 16,
    "score_total": 75,
    "ai_report": "ここに総合的な思考・認知特性の分析レポートを詳しく記述してください。",
    "interview_questions": "ここに面接官が当日深掘りすべき質問案を記述してください。",
    "recommended_role": "ここに適性配置（部署）の推奨や、採用後の労務管理・育成アプローチを記述してください。"
}
```"""
    
    prompt = prompt.format(text=text)
    # ----------------------------------------------------
# アプリケーション本体
# ----------------------------------------------------
st.sidebar.title("メニュー")
app_mode = st.sidebar.radio("モード選択", ["応募者入力画面", "管理者ログイン (当日用)"])

if app_mode == "応募者入力画面":
    st.markdown("<div class='day-banner'>選考当日 思考・表現力セッション 応募者入力フォーム<br><span style='font-size: 0.9em; font-weight: normal;'>以下のフォームに必要事項をご入力の上、「提出する」ボタンを押してください。</span></div>", unsafe_allow_html=True)

    with st.form("applicant_form"):
        name = st.text_input("お名前 (フルネーム)")
        email = st.text_input("メールアドレス")
        content = st.text_area("記述テキスト（自由記述：これまでの経験や仕事への取り組み方などをご記入ください）", height=200, placeholder="ここにテキストを入力してください...")
        
        submitted = st.form_submit_button("提出する")
        
        if submitted:
            if not name or not content:
                st.warning("お名前と記述テキストを入力してください。")
            else:
                with st.spinner("AIが思考・認知特性を分析中です...少々お待ちください。"):
                    analysis_result = analyze_text_simple(content)
                    
                    if analysis_result:
                        insert_data = {
                            "name": name,
                            "email": email,
                            "content": content,
                            "score_logical": analysis_result["score_logical"],
                            "score_proactive": analysis_result["score_proactive"],
                            "score_analysis": analysis_result["score_analysis"],
                            "score_empathy": analysis_result["score_empathy"],
                            "score_growth": analysis_result["score_growth"],
                            "total_score": analysis_result["total_score"],
                            "ai_report": analysis_result["ai_report"],
                            "interview_questions": analysis_result["interview_questions"],
                            "recommended_role": analysis_result["recommended_role"]
                        }
                        
                        try:
                            supabase.table("mentality_applicants_matsuyama").insert(insert_data).execute()
                            st.success("ご提出ありがとうございました！データが正常に保存されました。")
                        except Exception as e:
                            st.error(f"データベース保存エラー: {e}")

# 2. 管理者ログイン画面
elif app_mode == "管理者ログイン (当日用)":
    st.markdown("<div class='day-banner'>管理者ログイン (当日・面接官用)</div>", unsafe_allow_html=True)
    
    password_input = st.text_input("管理者パスワードを入力してください", type="password")
    
    # 松山様用パスワード
    ADMIN_PASSWORD = "ｍTsN1018"
    
    if password_input == ADMIN_PASSWORD:
        st.success("認証に成功しました。")
        
        st.markdown("### 応募者一覧・評価レポート管理")
        
        try:
            response = supabase.table("mentality_applicants_matsuyama").select("*").execute()
            applicants = response.data
            
            if not applicants:
                st.info("現在、登録されている応募者データはありません。")
            else:
                applicant_names = [f"{app['name']} (ID: {app['id']})" for app in applicants]
                selected_applicant_str = st.selectbox("確認・編集する応募者を選択してください", applicant_names)
                
                selected_index = applicant_names.index(selected_applicant_str)
                selected_app = applicants[selected_index]
                
                st.markdown("---")
                st.subheader(f"👤 応募者: {selected_app['name']} さんの評価結果")
                st.write(f"**総合スコア:** {selected_app.get('total_score', 0)} / 100点")
                
                categories, scores = calculate_scores(selected_app)
                fig = go.Figure(data=go.Scatterpolar(
                    r=scores,
                    theta=categories,
                    fill='toself',
                    marker_color='#800000'
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 20])),
                    showlegend=False,
                    height=400,
                    margin=dict(t=20, b=20, l=20, r=20)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("📝 応募者の記述テキストを確認"):
                    st.write(selected_app['content'])
                
                st.markdown("### 📋 AI分析レポート・面接メモ（編集可能）")
                edited_report = st.text_area("AIレポート・面接評価メモ", value=selected_app.get('ai_report', ''), height=250)
                edited_questions = st.text_area("深掘り質問案", value=selected_app.get('interview_questions', ''), height=150)
                edited_role = st.text_area("適性配置・労務管理アプローチ", value=selected_app.get('recommended_role', ''), height=150)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 変更を保存する"):
                        try:
                            supabase.table("mentality_applicants_matsuyama").update({
                                "ai_report": edited_report,
                                "interview_questions": edited_questions,
                                "recommended_role": edited_role
                            }).eq("id", selected_app['id']).execute()
                            st.success("変更内容を保存しました！")
                        except Exception as e:
                            st.error(f"削除エラー: {e}")
                            
        except Exception as e:
            st.error(f"データ取得エラー: {e}")
            
    elif password_input != "":
        st.error("パスワードが違います。")

# フッター
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 0.85em;'>事業者・採用担当者様向け運用資料 | 思考・表現力セッション AI選考アプリ</div>", unsafe_allow_html=True)

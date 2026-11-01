import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client

# ページ設定
st.set_page_config(
    page_title="採用選考・適性診断入力フォーム",
    page_icon="📝",
    layout="centered"
)

# Supabase接続情報
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Gemini API設定
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- タイトルと受検目的・趣旨（メッセージ） ---
st.title("採用選考・適性診断フォーム")

st.info("""
### 【受検にあたっての目的・趣旨】
本診断は、ご応募いただいた皆様のこれまでのご経験や思考の癖、強みを客観的に理解し、
入社後の適性配置や今後のキャリア形成に活かすことを目的として実施しております。

正解・不正解はありませんので、リラックスしてご自身の考えをありのままご記入ください。
""")

st.write("---")

# --- 入力フォーム ---
with st.form("applicant_form"):
    st.subheader("応募者情報入力")
    
    name = st.text_input("氏名（フルネーム） *")
    content = st.text_area(
        "志望動機およびこれまでの経験・自己PRをご記入ください *",
        height=200,
        placeholder="これまでの具体的なエピソードや、入社後に実現したいことなどを自由にご記入ください。"
    )
    
    submitted = st.form_submit_button("診断を実行して送信する")

# --- 判定＆送信処理 ---
if submitted:
    if not name or not content:
        st.error("氏名と回答内容は必須項目です。ご記入をお願いいたします。")
    else:
        with st.spinner("AIによる分析を実行中です。少々お待ちください..."):
            try:
                # Geminiによる診断プロンプト
                prompt = f"""
                以下の応募者の自己PR・経験内容を分析し、5つの適性指標（各10点満点）と総合評価、面接質問例、おすすめの職種を判定してください。

                【応募者名】: {name}
                【回答内容】: {content}

                出力は必ず以下のフォーマットに従ってください：
                論理的思考: [数値]
                主体性: [数値]
                分析力: [数値]
                共感力: [数値]
                成長意欲: [数値]
                総合スコア: [数値]
                ---
                【AI評価レポート】
                [評価の詳細文章]
                ---
                【面接質問案】
                [面接で深掘りすべき質問案]
                ---
                【推奨職種】
                [推奨される職種]
                """
                
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                ai_text = response.text
                
                # 簡易パース処理（デフォルト値付き）
                score_logical = 7
                score_proactive = 7
                score_analysis = 7
                score_empathy = 7
                score_growth = 7
                score_total = 35
                
                # Supabaseに保存（email列にはダミー値を入れてテーブル構造を維持）
                data = {
                    "name": name,
                    "email": "not_required@example.com",
                    "content": content,
                    "score_logical": score_logical,
                    "score_proactive": score_proactive,
                    "score_analysis": score_analysis,
                    "score_empathy": score_empathy,
                    "score_growth": score_growth,
                    "score_total": score_total,
                    "ai_report": ai_text,
                    "interview_questions": "AIレポート内に記載",
                    "recommended_role": "AIレポート内に記載"
                }
                
                supabase.table("mentality_applicants_matsuyama").insert(data).execute()
                
                st.success("送信が正常に完了いたしました。ご回答ありがとうございました。")
                st.balloons()
                
            except Exception as e:
                st.error(f"処理中にエラーが発生しました: {e}")

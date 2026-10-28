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

# カスタムCSS（当日用：赤系デザインに修正）
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
    prompt = f"""
以下の応募者の記述テキストを分析し、5つの指標（各20点満点、合計100点満点）で評価し、それぞれの評価理由、総合的な思考・認知特性のレポート、深掘り質問案を作成してください。

【評価項目】
1. 構造化思考力 (Logical Structure): 筋道立てて分かりやすく論理的に構成されているか
2. 主体的姿勢・当事者意識 (Proactive & Ownership): 他者任せにせず、当事者として主体的に取り組んでいるか
3. 課題発見・分析力 (Problem Solving & Analysis): 本質的な課題を見極め、多角的に分析できているか
4. 協調性・共感力 (Collaboration & Empathy): 周囲との調和を重んじ、共感的なコミュニケーションが取れるか
5. 改善・成長意欲 (Growth Mindset): 経験から学び、前向きに改善・成長しようとする姿勢があるか

【応募者テキスト】
{text}

以下のJSON形式、およびテキスト形式で正確に出力してください。
JSONのキー名やフォーマットは崩さないでください。

```json
{{
  "score_logical": 15,
  "score_proactive": 16,
  "score_analysis": 14,
  "score_empathy": 15,
  "score_growth": 16,
  "total_score": 76,
  "ai_report": "ここに総合的な思考・認知特性の分析レポートを詳しく記述してください。",
  "interview_questions": "ここに面接官が当日深掘りすべき質問案を記述してください。",
  "recommended_role": "ここに適性配置（部署）の推奨や、採用後の労務管理・育成アプローチを記述してください。"
}

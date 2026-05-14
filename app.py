import os
import re
from typing import Optional

import anthropic
import streamlit as st
from postgrest.exceptions import APIError
from supabase import create_client
from prompts import QUESTION_SYSTEM_PROMPT, FEEDBACK_SYSTEM_PROMPT


# --- Anthropic client ---
def _api_key() -> Optional[str]:
    env = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if env:
        return env
    try:
        return str(st.secrets["ANTHROPIC_API_KEY"]).strip()
    except KeyError:
        return None


_api = _api_key()
if not _api:
    st.error(
        "Missing **ANTHROPIC_API_KEY**. Set it in `.streamlit/secrets.toml` locally, or under "
        "**App settings → Secrets** on Streamlit Cloud (same key name, value in quotes)."
    )
    st.stop()

client = anthropic.Anthropic(api_key=_api)


# --- Supabase client ---
def _supabase_client():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError:
        st.error(
            "Missing **SUPABASE_URL** or **SUPABASE_KEY**. "
            "Add them to `.streamlit/secrets.toml` locally or Streamlit Cloud secrets."
        )
        st.stop()

supabase = _supabase_client()


# --- Helpers ---
CATEGORIES = [
    "Product Design",
    "Metrics & Execution",
    "Strategy",
    "Estimation",
    "Pricing",
    "Technical",
    "Tradeoff",
    "A/B Testing",
    "New Market Entry",
    "Behavioral"
]

def extract_score(feedback_text: str) -> Optional[int]:
    match = re.search(r'\*\*Score:\*\*\s*(\d+)/10', feedback_text)
    return int(match.group(1)) if match else None

def save_session(category: str, score: int) -> bool:
    try:
        supabase.table("sessions").insert({
            "category": category,
            "score": score,
        }).execute()
        return True
    except APIError:
        st.warning(
            "Could not save progress to Supabase. Typical fixes: create a `sessions` table with "
            "`category` (text) and `score` (int), and add RLS policies so your **anon** key can "
            "INSERT and SELECT—or set `SUPABASE_KEY` to the **service_role** key (private apps only). "
            "See `supabase_sessions.sql` in the repo."
        )
        return False


def load_progress():
    try:
        data = supabase.table("sessions").select("*").execute().data
        return data or []
    except APIError:
        st.warning(
            "Could not load progress from Supabase. Check RLS allows SELECT on `sessions` for your key."
        )
        return []


# --- UI ---
st.title("AI PM Interview Coach")
st.caption("Practice. Get feedback. Track progress.")

tab1, tab2 = st.tabs(["Practice", "Progress"])

with tab1:
    category = st.selectbox("Choose a category", CATEGORIES)

    if st.button("Generate Question"):
        with st.spinner("Generating question..."):
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": QUESTION_SYSTEM_PROMPT.format(category=category)
                }]
            )
            st.session_state.question = response.content[0].text
            st.session_state.category = category
            st.session_state.pop("feedback", None)

    if "question" in st.session_state:
        st.subheader("Your Question")
        st.info(st.session_state.question)

        answer = st.text_area("Your answer", height=200,
                              placeholder="Type or dictate your answer here...")

        if st.button("Get Feedback") and answer:
            with st.spinner("Evaluating your answer..."):
                feedback = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1000,
                    system=FEEDBACK_SYSTEM_PROMPT,
                    messages=[{
                        "role": "user",
                        "content": f"Question: {st.session_state.question}\n\nAnswer: {answer}"
                    }]
                )
                st.session_state.feedback = feedback.content[0].text
                score = extract_score(st.session_state.feedback)
                if score is not None:
                    save_session(st.session_state.category, score)

    if "feedback" in st.session_state:
        st.subheader("Feedback")
        st.markdown(st.session_state.feedback)

with tab2:
    st.subheader("Your Progress")
    data = load_progress()

    if not data:
        st.info("No sessions yet. Start practicing to see your progress.")
    else:
        reps = {}
        scores = {}
        for row in data:
            cat = row["category"]
            reps[cat] = reps.get(cat, 0) + 1
            scores.setdefault(cat, []).append(row["score"])

        for cat in CATEGORIES:
            rep_count = reps.get(cat, 0)
            avg = round(sum(scores[cat]) / len(scores[cat]), 1) if cat in scores else "-"
            st.write(f"**{cat}** — {rep_count} reps | Avg score: {avg}/10")
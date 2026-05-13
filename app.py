import os

import anthropic
import streamlit as st
from prompts import QUESTION_SYSTEM_PROMPT, FEEDBACK_SYSTEM_PROMPT

# Local: use ANTHROPIC_API_KEY in the environment. Streamlit Cloud: same key in app secrets.
if not os.environ.get("ANTHROPIC_API_KEY"):
    try:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    except KeyError:
        pass

client = anthropic.Anthropic()

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

st.title("AI PM Interview Coach")
st.caption("Practice. Get feedback. Track progress.")

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
            st.subheader("Feedback")
            st.markdown(feedback.content[0].text)
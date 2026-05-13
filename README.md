# AI PM Interview Coach

Streamlit app that generates PM interview questions (by category) and scores your answers using the Anthropic API.

## Local setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Set your API key (the Anthropic SDK reads this automatically):

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

3. Run the app:

```bash
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. In [Streamlit Community Cloud](https://streamlit.io/cloud), connect the repo and choose **Main file path**: `app.py`.
3. Under **Secrets**, add:

```toml
ANTHROPIC_API_KEY = "your-key-here"
```

Streamlit injects secrets into the environment; the Anthropic client will pick up `ANTHROPIC_API_KEY`.

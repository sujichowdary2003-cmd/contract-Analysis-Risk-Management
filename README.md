# Contract Analysis Multi-Agent System

**AI-powered contract review system** using multiple specialized agents to analyze contracts from different perspectives: Structure, Legal, Negotiation, and Management. The project includes a **Streamlit web dashboard**, a **Telegram bot**, and a **main script** to run the system in VSCode or any IDE.

## Features

- ✅ Multi-agent analysis: Structure, Legal, Negotiation, Management  
- 📄 PDF upload and text extraction  
- 📊 Risk assessment with confidence scores  
- 📈 Interactive visualizations using Plotly  
- 💾 Export results in JSON format  
- 🤖 Telegram bot for remote contract analysis  

## Installation

1. Clone the repository:

```bash
git clone https://github.com/TechSlinger/Contract_Analysis_Multi_Agent_System.git
cd Contract_Analysis_Multi_Agent_System
````

2. Create and activate a virtual environment:

```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### 1. Run with main.py (VSCode or IDE)

```bash
python main.py
```

* Starts the system for local use.
* Interact via the Streamlit dashboard or command-line prompts.

### 2. Streamlit Web App

```bash
streamlit run streamlit_app.py
```

* Upload a PDF contract.
* Extract text and run analysis.
* View metrics, agent findings, and visualizations.
* Export results in JSON.

### 3. Telegram Bot

* Set your Telegram bot token in `telegram_bot.py`.
* Run the bot:

```bash
python telegram_bot.py
```

* Send a PDF to the bot and get analysis results directly.

## Folder Structure

```
├─ contract_analysis_system.py   # Core analysis modules
├─ streamlit_app.py              # Streamlit interface
├─ telegram_bot.py               # Telegram bot interface
├─ main.py                       # Entry point for running the project locally
├─ requirements.txt
└─ README.md
```


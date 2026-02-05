# telegram_bot.py
import logging
from pathlib import Path
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from contract_analysis_system import (
    ContractAnalysisSystem,
    extract_text_from_pdf,
    analyze_contract,
    save_analysis_results,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation
WAITING_FOR_FILE, WAITING_FOR_CONFIRMATION = range(2)

# Dictionary to store user session data
user_sessions = {}

# Helper function to send long messages
async def send_long_message(chat_id, text, context, chunk_size=4000):
    """Send long text in multiple messages to avoid Telegram limits"""
    for i in range(0, len(text), chunk_size):
        await context.bot.send_message(chat_id=chat_id, text=text[i:i+chunk_size])

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Contract Analysis Bot!\n\n"
        "Send me a PDF contract to start analysis."
    )
    return WAITING_FOR_FILE

# Handle PDF file upload
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    if file.mime_type != "application/pdf":
        await update.message.reply_text("❌ Please send a PDF file only.")
        return WAITING_FOR_FILE

    file_path = f"temp_{file.file_name}"

    # Correctly await get_file()
    telegram_file = await file.get_file()
    await telegram_file.download_to_drive(file_path)

    text = extract_text_from_pdf(file_path)
    Path(file_path).unlink(missing_ok=True)

    if not text:
        await update.message.reply_text("❌ Failed to extract text from PDF.")
        return WAITING_FOR_FILE

    user_sessions[update.effective_chat.id] = {
        "contract_text": text,
        "contract_name": file.file_name,
        "analysis_result": None,
    }

    await update.message.reply_text(
        f"✅ Extracted {len(text):,} characters from {file.file_name}\n\n"
        "Send /analyze to start the contract analysis."
    )
    return WAITING_FOR_CONFIRMATION

# Analyze command
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = user_sessions.get(update.effective_chat.id)
    if not session or "contract_text" not in session:
        await update.message.reply_text("⚠️ No contract uploaded. Send a PDF first.")
        return WAITING_FOR_FILE

    await update.message.reply_text("🔍 Analyzing contract, please wait...")

    # Initialize system if not already
    if "system" not in context.application.bot_data:
        context.application.bot_data["system"] = ContractAnalysisSystem()

    result = analyze_contract(
        context.application.bot_data["system"],
        session["contract_text"],
        session["contract_name"],
    )
    session["analysis_result"] = result

    # Summarize results for Telegram
    summary = f"📄 Contract: {session['contract_name']}\n"
    summary += f"Length: {result.contract_info['length']:,} chars\n"
    total_agents = len(result.agent_responses)
    success_agents = sum(1 for resp in result.agent_responses if "error" not in resp.findings)
    summary += f"🤖 Agents Success: {success_agents}/{total_agents}\n"

    # Risk assessment
    risk_levels = [resp.risk_level for resp in result.agent_responses if resp.risk_level != "PENDING"]
    if risk_levels:
        high_risk = sum(1 for r in risk_levels if r == "HIGH")
        overall_risk = "HIGH" if high_risk > 0 else "MEDIUM" if "MEDIUM" in risk_levels else "LOW"
    else:
        overall_risk = "UNKNOWN"
    summary += f"⚠️ Overall Risk Level: {overall_risk}\n"

    # Send summary safely
    await send_long_message(update.effective_chat.id, summary, context)

    # Send individual agent findings
    for resp in result.agent_responses:
        findings_text = (
            resp.findings.get("raw_response", "No detailed findings available")
            if "error" not in resp.findings
            else f"❌ Error: {resp.findings['error']}"
        )
        agent_msg = f"🤖 {resp.agent_name} - {resp.analysis_type.replace('_', ' ').title()}\n{findings_text}"
        await send_long_message(update.effective_chat.id, agent_msg, context)

    # Save results and send JSON
    filepath = save_analysis_results(result)
    if filepath:
        await update.message.reply_document(document=InputFile(filepath))
        Path(filepath).unlink(missing_ok=True)
    else:
        await update.message.reply_text("❌ Failed to save analysis results.")

    return ConversationHandler.END

# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

# Main function
def main():
    TOKEN = "8436806287:AAFaRTS7_qZ99puFdV55sfz6qeCxvwf87HI"
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_FILE: [MessageHandler(filters.Document.ALL, handle_file)],
            WAITING_FOR_CONFIRMATION: [CommandHandler("analyze", analyze)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()

    
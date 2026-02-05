# telegram_bot.py

import logging
import os
from pathlib import Path
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from contract_analysis_system import (
    ContractAnalysisSystem,
    extract_text_from_pdf,
    analyze_contract,
    save_analysis_results,
)

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Conversation states
# --------------------------------------------------
WAITING_FOR_FILE, WAITING_FOR_CONFIRMATION = range(2)

# In-memory session storage
user_sessions = {}

# --------------------------------------------------
# Helper: send long messages safely
# --------------------------------------------------
async def send_long_message(chat_id, text, context, chunk_size=3500):
    for i in range(0, len(text), chunk_size):
        await context.bot.send_message(chat_id=chat_id, text=text[i : i + chunk_size])

# --------------------------------------------------
# /start command
# --------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Contract Analysis Bot!\n\n"
        "📄 Please upload a *PDF contract* to begin analysis."
    )
    return WAITING_FOR_FILE

# --------------------------------------------------
# Handle PDF upload
# --------------------------------------------------
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("❌ Please upload a valid PDF contract.")
        return WAITING_FOR_FILE

    temp_path = f"temp_{document.file_unique_id}.pdf"

    try:
        telegram_file = await document.get_file()
        await telegram_file.download_to_drive(temp_path)

        text = extract_text_from_pdf(temp_path)
        Path(temp_path).unlink(missing_ok=True)

        if not text.strip():
            await update.message.reply_text("❌ Could not extract text from this PDF.")
            return WAITING_FOR_FILE

        user_sessions[update.effective_chat.id] = {
            "contract_text": text,
            "contract_name": document.file_name,
            "analysis_result": None,
        }

        await update.message.reply_text(
            f"✅ Contract received: *{document.file_name}*\n"
            f"📏 Extracted {len(text):,} characters\n\n"
            "Send /analyze to start analysis."
        )

        return WAITING_FOR_CONFIRMATION

    except Exception as e:
        logger.exception("File handling error")
        await update.message.reply_text("❌ Error processing the PDF.")
        return WAITING_FOR_FILE

# --------------------------------------------------
# /analyze command
# --------------------------------------------------
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    session = user_sessions.get(chat_id)

    if not session:
        await update.message.reply_text("⚠️ Please upload a contract first.")
        return WAITING_FOR_FILE

    await update.message.reply_text("🔍 Analyzing contract… Please wait.")

    # Initialize analysis system once
    if "system" not in context.application.bot_data:
        context.application.bot_data["system"] = ContractAnalysisSystem()

    try:
        # Run heavy analysis safely in executor
        result = await context.application.run_in_executor(
            None,
            analyze_contract,
            context.application.bot_data["system"],
            session["contract_text"],
            session["contract_name"],
        )

        session["analysis_result"] = result

        # ---------------- Summary ----------------
        summary = (
            f"📄 *Contract:* {session['contract_name']}\n"
            f"📏 *Length:* {result.contract_info.get('length', 0):,} characters\n"
        )

        agent_responses = result.agent_responses or []
        total_agents = len(agent_responses)
        successful_agents = sum(
            1 for r in agent_responses if isinstance(r.findings, dict) and "error" not in r.findings
        )

        summary += f"🤖 *Agents Successful:* {successful_agents}/{total_agents}\n"

        # Risk aggregation
        risk_levels = [
            r.risk_level
            for r in agent_responses
            if hasattr(r, "risk_level") and r.risk_level
        ]

        if "HIGH" in risk_levels:
            overall_risk = "HIGH"
        elif "MEDIUM" in risk_levels:
            overall_risk = "MEDIUM"
        elif "LOW" in risk_levels:
            overall_risk = "LOW"
        else:
            overall_risk = "UNKNOWN"

        summary += f"⚠️ *Overall Risk Level:* {overall_risk}"

        await send_long_message(chat_id, summary, context)

        # ---------------- Agent details ----------------
        for resp in agent_responses:
            findings = resp.findings or {}
            if "error" in findings:
                details = f"❌ Error: {findings['error']}"
            else:
                details = findings.get("raw_response", "No detailed findings.")

            agent_msg = (
                f"🤖 *{resp.agent_name}*\n"
                f"📌 {resp.analysis_type.replace('_', ' ').title()}\n\n"
                f"{details}"
            )

            await send_long_message(chat_id, agent_msg, context)

        # ---------------- Save JSON ----------------
        json_path = save_analysis_results(result)
        if json_path and Path(json_path).exists():
            await update.message.reply_document(document=InputFile(json_path))
            Path(json_path).unlink(missing_ok=True)

        # Cleanup session
        user_sessions.pop(chat_id, None)

        return ConversationHandler.END

    except Exception as e:
        logger.exception("Analysis failed")
        await update.message.reply_text("❌ Contract analysis failed.")
        return ConversationHandler.END

# --------------------------------------------------
# /cancel command
# --------------------------------------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions.pop(update.effective_chat.id, None)
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

# --------------------------------------------------
# Main entry
# --------------------------------------------------
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable not set")

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_FILE: [
                MessageHandler(filters.Document.PDF & ~filters.COMMAND, handle_file)
            ],
            WAITING_FOR_CONFIRMATION: [
                CommandHandler("analyze", analyze)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()


    

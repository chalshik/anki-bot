import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .. import dictionary
from ..handlers.add_word import handle_add_word

logger = logging.getLogger(__name__)

_KEY = "upload_words" # List of extracted words in context.user_data
_SELECTED = "upload_selected" # Set of indexed words selected

async def handle_upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user to send a photo."""
    await update.message.reply_text(
        "📸 *Photo Upload*\n\nPlease send me a photo of text (from a book, screen, or article). "
        "I will extract advanced English vocabulary (B2+) for you to add to your deck.",
        parse_mode="Markdown"
    )
    # No explicit state needed since we'll just listen for photos globally 
    # or we can check context.user_data if we want to be strict.

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process received photo."""
    photo = update.message.photo[-1] # Get highest resolution
    status_msg = await update.message.reply_text("🔍 *Reading image and analyzing vocabulary...*", parse_mode="Markdown")
    
    try:
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        
        words = await dictionary.extract_words_from_image(bytes(image_bytes))
        
        if not words:
            await status_msg.edit_text("🤷 No advanced (B2+) words found in this image. Try another one!")
            return
            
        context.user_data[_KEY] = words
        context.user_data[_SELECTED] = set() # Store indices of selected words
        
        await status_msg.delete()
        await _send_word_list(update.message.reply_text, context, words)
        
    except Exception as e:
        logger.error("Photo processing failed: %s", e)
        await status_msg.edit_text("❌ Sorry, I failed to process that image. Please try again.")

async def handle_upload_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle word selection and add to deck."""
    query = update.callback_query
    await query.answer()
    
    index = int(query.data.split(":")[1])
    words = context.user_data.get(_KEY, [])
    selected = context.user_data.get(_SELECTED, set())
    
    if not words or index >= len(words):
        return

    word = words[index]
    
    if index in selected:
        # Already added/selected - actually the user might want a way to "un-add" 
        # but for simplicity we'll just keep it as "Added ✅"
        return
    
    # Trigger addition logic
    # We'll call a simplified version of handle_add_word or use a shared helper 
    # To keep it clean, we'll implement a small helper in dictionary or db if needed, 
    # but handle_add_word in its current state works on Updates.
    # Let's use handle_add_word manually by creating a fake 'word' prompt.
    
    selected.add(index)
    
    # We need to simulate the addition. Handlers/add_word.py uses DB.
    # Instead of simulating a full Update, let's just use the logic directly.
    from .. import db
    user_id = update.effective_user.id
    settings = await db.get_user_settings(user_id)
    result = await dictionary.fetch_definition(word)
    if result:
        await db.save_word_and_card(user_id, word, result)
        # Update the UI
        await query.edit_message_reply_markup(reply_markup=_build_markup(words, selected))
    else:
        await query.message.reply_text(f"❌ Failed to get definition for '{word}'.")

async def _send_word_list(send_fn, context, words):
    selected = context.user_data.get(_SELECTED, set())
    text = (
        "✨ *Extracted Vocabulary*\n"
        "Tap a word to add it to your deck. I'll automatically fetch definitions and examples!\n"
    )
    await send_fn(
        text,
        parse_mode="Markdown",
        reply_markup=_build_markup(words, selected)
    )

def _build_markup(words, selected):
    rows = []
    current_row = []
    for i, word in enumerate(words):
        is_selected = i in selected
        label = f"✅ {word}" if is_selected else word
        btn = InlineKeyboardButton(label, callback_data=f"upload_toggle:{i}")
        current_row.append(btn)
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    
    rows.append([InlineKeyboardButton("Done", callback_data="upload_done")])
    return InlineKeyboardMarkup(rows)

async def handle_upload_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data.pop(_KEY, None)
    context.user_data.pop(_SELECTED, None)
    await query.edit_message_text("👍 Word extraction complete. You can see your words using /words!")

# charmbracelet/vhs tape for the cuere README demo GIF (docs/img/demo.gif).
# Regenerate:  vhs examples/demo.tape   (needs vhs + ttyd + ffmpeg on PATH, plus
# `cuere` itself — the `Require cuere` directive below enforces that).
# The hidden `clear` just starts the recording on a clean screen.

Output docs/img/demo.gif

Require cuere

Set Shell bash
Set FontSize 18
Set Width 1000
Set Height 760
Set Padding 24
Set Theme "Dracula"
Set TypingSpeed 60ms

# --- hidden: clear the screen so the recording starts on a clean prompt ---
Hide
Type "clear" Enter
Show

# 1. A first code
Type "cuere 'https://github.com/IvanAnishchuk/cuere'" Sleep 500ms Enter
Sleep 2.5s

# 2. Inverted (light-on-dark)
Type "cuere --invert 'HELLO'" Sleep 500ms Enter
Sleep 2.5s

# 3. A wallet URI, optimized to QR-alphanumeric for a smaller code
Type "cuere --optimize-uri 'bitcoin:bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq'" Sleep 500ms Enter
Sleep 2.5s

# 4. Colored ANSI half-blocks (theme-proof)
Type "cuere --mode ansi 'cuere'" Sleep 500ms Enter
Sleep 3s

import string
import sys
import unicodedata


# Graceful shutdown flag
shutdown_requested = False


# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    """Handle termination signals to allow graceful shutdown."""
    global shutdown_requested
    if shutdown_requested:
        print("\nForce quit.")
        sys.exit(1)
    shutdown_requested = True
    print("\nShutdown requested. Finishing current page...")


def text_normalizer(text: str):
    # Decompose accents
    text = unicodedata.normalize("NFD", text)
    # Remove decomposed part of accents to only keep letter
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Lower case aggressively
    text = text.casefold()

    return text

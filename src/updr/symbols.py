"""Provides text or emoji symbols for CLI display."""

# pylint: disable=invalid-name,too-few-public-methods


class Symbols:
    """CLI display symbols (emojis or plain text)."""

    def __init__(self, no_color: bool = False) -> None:
        if no_color:
            self.ok = "[OK] "
            self.warn = "[WARN] "
            self.err = "[ERR] "
            self.upg = "[UPG] "
            self.pkg = "[PKG] "
            self.info = "[INFO] "
            self.pin = "[PIN] "
        else:
            self.ok = "✅"
            self.warn = "⚠️"
            self.err = "❌"
            self.upg = "⬆️"
            self.pkg = "📦"
            self.info = "ℹ️"
            self.pin = "📌"

    OK: str = property(lambda self: self.ok)
    WARN: str = property(lambda self: self.warn)
    ERR: str = property(lambda self: self.err)
    UPG: str = property(lambda self: self.upg)
    PKG: str = property(lambda self: self.pkg)
    INFO: str = property(lambda self: self.info)
    PIN: str = property(lambda self: self.pin)

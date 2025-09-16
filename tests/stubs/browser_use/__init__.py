class BrowserConfig:
    """Minimal stub mirroring the configuration dataclass used in production."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


__all__ = ["BrowserConfig"]

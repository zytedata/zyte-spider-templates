try:
    from enum_tools.documentation import document_enum
except ImportError:

    def document_enum(func):  # type: ignore[misc]
        return func


__all__ = ["document_enum"]

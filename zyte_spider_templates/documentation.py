try:
    from enum_tools.documentation import document_enum
except ImportError:

    def document_enum(func):
        return func

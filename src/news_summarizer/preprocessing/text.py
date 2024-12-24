import re
import unicodedata


class TextTransformation:
    def apply(self, text: str) -> str:
        raise NotImplementedError


class StripWhitespace(TextTransformation):
    def apply(self, text: str) -> str:
        return text.strip()


class RemoveEmojis(TextTransformation):
    def apply(self, text: str) -> str:
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map symbols
            "\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub(r"", text)


class RemoveNonAsciiExceptAccents(TextTransformation):
    def apply(self, text: str) -> str:
        return "".join(c for c in text if ord(c) < 128 or unicodedata.category(c).startswith("L"))


class ReplaceMultipleSpaces(TextTransformation):
    def apply(self, text: str) -> str:
        return re.sub(r"\s+", " ", text)


class TextPipeline:
    def __init__(self):
        self.transformations = []

    def add_transformation(self, transformation: TextTransformation):
        self.transformations.append(transformation)

    def execute(self, text: str) -> str:
        if text is None:
            return ""
        for transformation in self.transformations:
            text = transformation.apply(text)
        return text


# Example usage
pipeline = TextPipeline()
pipeline.add_transformation(StripWhitespace())
pipeline.add_transformation(RemoveEmojis())
pipeline.add_transformation(RemoveNonAsciiExceptAccents())
pipeline.add_transformation(ReplaceMultipleSpaces())

from dataclasses import dataclass


@dataclass
class RetrieverConfig:
    settings: dict
    KEYS: list = ["fetch_k", "k"]

    def get(self):
        return {key: self.settings[key] for key in self.KEYS}


@dataclass
class RetrieverWithSearchConfig:
    settings: dict
    KEYS: list = [
        "chunk_size",
        "chunk_overlap",
        "search_k",
        "fetch_k",
        "k",
        "search",
        "pdf_parser",
    ]

    def get(self):
        return {key: self.settings[key] for key in self.KEYS}


@dataclass
class LLMConfig:
    settings: dict
    KEYS: list = ["temperature"]

    def get(self):
        return {key: self.settings[key] for key in self.KEYS}

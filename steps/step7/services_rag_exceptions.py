class EmbeddingsMissing(Exception):
    def __init__(self, method, folder):
        super().__init__(f"Embeddings missing for method '{method}' in {folder}")
        self.method = method
        self.folder = folder

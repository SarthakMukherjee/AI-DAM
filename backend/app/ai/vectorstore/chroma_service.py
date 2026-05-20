# Creates a ChromaDB client

import chromadb
from chromadb.config import Settings

CHROMA_DB_PATH = "storage/vector_db"

class ChromaService:

    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = chromadb.PersistentClient(
                path=CHROMA_DB_PATH,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )

            return cls._client
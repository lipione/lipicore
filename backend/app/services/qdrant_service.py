from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from ..core.config import settings

# Initialize Qdrant Client
qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
COLLECTION_NAME = "bank_documents"

def init_qdrant():
    import time
    max_retries = 5
    retry_delay = 2
    
    for i in range(max_retries):
        try:
            print(f"Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT} (Attempt {i+1}/{max_retries})...")
            collections = qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if COLLECTION_NAME not in collection_names:
                print(f"Creating collection: {COLLECTION_NAME}")
                qdrant_client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=settings.EMBEDDING_DIMENSION, distance=Distance.COSINE),
                )
            print("Qdrant initialized successfully.")
            return
        except Exception as e:
            print(f"Error connecting to Qdrant: {e}")
            if i < max_retries - 1:
                time.sleep(retry_delay)
    
    print("Could not connect to Qdrant after several retries.")

def upload_points(points: list[PointStruct]):
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

def delete_points_by_document(document_id: int, bank_id: int):
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    qdrant_client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(key="document_id", match=MatchValue(value=document_id)),
                FieldCondition(key="bank_id", match=MatchValue(value=bank_id)),
            ]
        ),
    )


def update_points_by_document_payload(document_id: int, bank_id: int, payload: dict):
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    qdrant_client.set_payload(
        collection_name=COLLECTION_NAME,
        payload=payload,
        points=Filter(
            must=[
                FieldCondition(key="document_id", match=MatchValue(value=document_id)),
                FieldCondition(key="bank_id", match=MatchValue(value=bank_id)),
            ]
        ),
    )


def search_points(
    query_vector: list[float],
    bank_id: int,
    limit: int = 5,
    document_ids: list[int] | None = None,
    session_id: int | None = None,
    document_scope: str | None = None,
    document_statuses: list[str] | None = None,
    version_states: list[str] | None = None,
    max_access_level: int | None = None,
):
    from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

    must = [FieldCondition(key="bank_id", match=MatchValue(value=bank_id))]
    if document_ids:
        must.append(FieldCondition(key="document_id", match=MatchAny(any=document_ids)))
    if session_id is not None:
        must.append(FieldCondition(key="session_id", match=MatchValue(value=session_id)))
    if document_scope:
        must.append(FieldCondition(key="document_scope", match=MatchValue(value=document_scope)))
    if document_statuses:
        must.append(FieldCondition(key="document_status", match=MatchAny(any=document_statuses)))
    if version_states:
        must.append(FieldCondition(key="version_state", match=MatchAny(any=version_states)))
    if max_access_level is not None:
        from qdrant_client.models import Range
        must.append(FieldCondition(key="access_level", range=Range(lte=max_access_level)))

    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=Filter(must=must),
        limit=limit,
    ).points
    return results

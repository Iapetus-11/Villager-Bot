from pydantic import BaseModel

class ClusterInfo(BaseModel):
    cluster_id: int
    shard_count: int
    shard_ids: list[int]

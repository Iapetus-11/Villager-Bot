import uuid


class ShardIdManager:
    def __init__(self, shard_count: int, cluster_count: int) -> None:
        if shard_count % cluster_count != 0:
            raise ValueError("Shard count must be a multiple of the cluster count")

        self.shards_per_cluster = shard_count // cluster_count

        self._available_shards = list(range(shard_count))
        self._taken_shards = dict[uuid.UUID, list[int]]()

    def take(self, ws_id: uuid.UUID) -> list[int]:
        shard_ids = self._available_shards[: self.shards_per_cluster]

        if not shard_ids:
            raise RuntimeError("No shard ids left to take!")

        self._available_shards = self._available_shards[self.shards_per_cluster :]

        self._taken_shards[ws_id] = shard_ids

        return shard_ids

    def release(self, ws_id: uuid.UUID) -> None:
        self._available_shards.extend(self._taken_shards.pop(ws_id))

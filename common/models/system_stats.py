from common.models.base_model import BaseModel


class SystemStats(BaseModel):
    identifier: str
    cpu_usage_percent: float
    memory_usage_bytes: int
    memory_max_bytes: int
    threads: int
    asyncio_tasks: int

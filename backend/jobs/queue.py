from django_q.tasks import async_task


def enqueue(function: str, *args, cluster: str = "default"):
    if cluster not in {"default", "ai"}:
        raise ValueError("Unknown cluster")
    return async_task(function, *args, cluster=cluster)

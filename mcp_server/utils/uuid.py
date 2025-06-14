from uuid import uuid5, NAMESPACE_URL


def generate_id(name: str) -> str:
    uuid = uuid5(namespace=NAMESPACE_URL, name=name)
    return str(uuid)

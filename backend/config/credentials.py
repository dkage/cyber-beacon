import os
from collections.abc import Mapping
from pathlib import Path


def load_fernet_keys(environ: Mapping[str, str] | None = None) -> list[str]:
    environment = os.environ if environ is None else environ
    credential_path = environment.get("FERNET_KEYS_FILE")
    if not credential_path and environment.get("CREDENTIALS_DIRECTORY"):
        credential_path = str(Path(environment["CREDENTIALS_DIRECTORY"]) / "fernet-keys")

    if credential_path:
        try:
            key_material = Path(credential_path).read_text(encoding="utf-8")
        except OSError as exc:
            raise RuntimeError("Could not read the configured Fernet credential file.") from exc
    else:
        key_material = environment.get("FERNET_KEYS", "")

    return [
        key.strip()
        for part in key_material.replace(",", "\n").splitlines()
        if (key := part.strip())
    ]

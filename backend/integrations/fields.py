import json

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings
from django.db import models


class EncryptedJSONField(models.TextField):
    """Opaque credentials only; do not use lookups or expose through serializers."""

    def cipher(self):
        if not settings.FERNET_KEYS:
            raise RuntimeError("Configure FERNET_KEYS before connecting a Provider.")
        return MultiFernet([Fernet(key) for key in settings.FERNET_KEYS])

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return json.loads(self.cipher().decrypt(value.encode()))

    def to_python(self, value):
        if value is None or isinstance(value, dict):
            return value
        return json.loads(self.cipher().decrypt(value.encode()))

    def get_prep_value(self, value):
        if value is None:
            return None
        return self.cipher().encrypt(json.dumps(value).encode()).decode()

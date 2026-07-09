# from uuid import UUID

# from pydantic import BaseModel, model_serializer

# from core.id_cypher import encrypt_id


# class EncryptedResponseModel(BaseModel):
#     @model_serializer(mode="wrap")
#     def serialize(self, handler):
#         return self._encrypt(handler(self))

#     @classmethod
#     def _encrypt(cls, value):
#         if isinstance(value, UUID):
#             return encrypt_id(value)

#         if isinstance(value, list):
#             return [cls._encrypt(v) for v in value]

#         if isinstance(value, dict):
#             return {k: cls._encrypt(v) for k, v in value.items()}

#         return value
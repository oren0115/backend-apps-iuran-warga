from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class GenerateFeesRequest(BaseModel):
    bulan: str
    # Tarif IPL per tipe rumah; dikirim dari frontend
    tarif_60m2: int
    tarif_72m2: int
    tarif_hook: int


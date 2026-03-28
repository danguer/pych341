def get_formatted_hex(data: bytes) -> str:
    return " ".join([f"{x:02X}" for x in data])

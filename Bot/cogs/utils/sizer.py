def get_size(bytes_1: int, suffix: str = "B") -> str:
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes_1 < factor:
            return f"{bytes_1:.2f}{unit}{suffix}"
        bytes_1 /= factor

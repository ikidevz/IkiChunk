from .codecs import Codec, register_codec
from .compression import archive, compress, decompress, extract

__all__ = ["Codec", "register_codec", "compress",
           "decompress", "archive", "extract"]

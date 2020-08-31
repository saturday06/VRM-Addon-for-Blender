# To avoid circular reference
def version():
    return __import__(".".join(__name__.split(".")[:-1])).bl_info["version"]

from common.models.data import Data


def load_data() -> Data:
    return Data.parse_file("common/data/data.json")

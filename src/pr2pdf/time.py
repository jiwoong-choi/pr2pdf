from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Time:
    """Represents a timestamp, handling UTC to KST conversion."""

    utc_datetime: str

    def to_string(self) -> str:
        """Convert UTC datetime string to KST datetime string.

        Returns:
            KST datetime string in format "YYYY-MM-DD HH:MM:SS"
        """
        utc_time = datetime.strptime(self.utc_datetime, "%Y-%m-%dT%H:%M:%SZ")
        kst_time = utc_time + timedelta(hours=9)  # KST is UTC+9
        return kst_time.strftime("%Y-%m-%d %H:%M:%S")


def convert_to_kst(utc_datetime: str) -> str:
    """Convert UTC datetime string to KST datetime string.

    Args:
        utc_datetime: UTC datetime string in format "YYYY-MM-DDTHH:MM:SSZ"

    Returns:
        KST datetime string in format "YYYY-MM-DD HH:MM:SS"
    """
    utc_time = datetime.strptime(utc_datetime, "%Y-%m-%dT%H:%M:%SZ")
    kst_time = utc_time + timedelta(hours=9)  # KST is UTC+9
    return kst_time.strftime("%Y-%m-%d %H:%M:%S")

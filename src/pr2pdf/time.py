from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Time:
    """Represents a timestamp, handling UTC to KST conversion."""

    utc_datetime: str

    

    def to_kst_str(self) -> str:
        """Convert UTC datetime string to KST datetime string.

        Returns:
            KST datetime string in format "YYYY-MM-DD HH:MM:SS"
        """
        utc_time = datetime.strptime(self.utc_datetime, "%Y-%m-%dT%H:%M:%SZ")
        kst_time = utc_time + timedelta(hours=9)  # KST is UTC+9
        return kst_time.strftime("%Y-%m-%d %H:%M:%S")




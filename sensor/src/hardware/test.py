
# time > last calibration day + x days (config) at 03:00
# day of last calibration was today
from datetime import datetime

today_ts = datetime.utcnow().timestamp()

tomorrow_ts = today_ts + 3600 * 24
yesterday_ts = today_ts - 3600 * 24

if datetime.fromtimestamp(today_ts).date() < datetime.fromtimestamp(tomorrow_ts).date():
    print(1)
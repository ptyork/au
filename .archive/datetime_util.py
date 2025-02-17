from datetime import datetime, timezone, timedelta

def parse_github_datetime(datetime_str: str) -> datetime:
    try:
        return datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except:
        return None

def format_github_datetime(gh_datetime: datetime) -> str:
    return datetime.strftime(gh_datetime, '%Y-%m-%dT%H:%M:%SZ')

def utc_to_local(utc_datetime: datetime) -> datetime:
    return utc_datetime.replace(tzinfo=timezone.utc).astimezone(tz=None)

def get_friendly_local_datetime(utc_datetime: datetime) -> str:
    return utc_to_local(utc_datetime).strftime('%Y-%m-%d %I:%M %p')

def get_friendly_timedelta(delta: timedelta) -> str:
    pd_str = ''
    if delta.days:
        pd_str += f'{delta.days} day + '
    secs = delta.seconds
    hours = secs // 3600
    secs = secs % 3600
    mins = secs // 60
    pd_str += f'{hours}:{mins:02d}'
    return pd_str

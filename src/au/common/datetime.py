from datetime import datetime, timezone, timedelta


def parse_github_datetime(datetime_str: str) -> datetime:
    try:
        return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except:
        return None


def utc_now():
    return datetime.now(timezone.utc)


def local_now():
    return date_to_local(utc_now())


def utc_min():
    return datetime.min.replace(tzinfo=timezone.utc)


def utc_max():
    return datetime.max.replace(tzinfo=timezone.utc)


def format_github_datetime(dt: datetime) -> str:
    return datetime.strftime(dt, "%Y-%m-%dT%H:%M:%SZ")


def date_to_utc(to_convert: datetime) -> datetime:
    return to_convert.astimezone(timezone.utc)


def date_to_local(to_convert: datetime) -> datetime:
    return to_convert.astimezone()


def get_friendly_local_datetime(dt: datetime) -> str:
    try:
        return date_to_local(dt).strftime("%Y-%m-%d %I:%M %p")
    except:
        return "N/A"


def get_friendly_timedelta(delta: timedelta) -> str:
    pd_str = ""
    if delta.days:
        pd_str += f"{delta.days} day + "
    secs = delta.seconds
    hours = secs // 3600
    secs = secs % 3600
    mins = secs // 60
    pd_str += f"{hours}:{mins:02d}"
    return pd_str

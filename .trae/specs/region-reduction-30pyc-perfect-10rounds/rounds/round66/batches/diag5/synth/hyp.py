def f(self, minute_time):
    try:
        try:
            if ':' in minute_time:
                minute_time = minute_time.replace(':', '')
            minute_time = int(minute_time)
        except (ValueError, TypeError):
            hour = 1
            minute = 2
        else:
            hour, minute = divmod(minute_time, 100)
        minute_time = self._day_minutes(hour, minute)
    except (ValueError, TypeError):
        pass
    return minute_time

from time import time
from datetime import datetime, timezone
from datetime import timezone as dt_timezone
import pytz
from datetime import timedelta
from string import Template
from dateutil.parser import parse as dateutil_phase
import pydateinfer

class Timer:

    def __init__(self) -> None:
        
        self.start_time = None

    def start(self) -> float:
        
        self.start_time = time()
        return self.start_time

    def stop(self) -> float:
        
        self.stop_time = time() - self.start_time
        #print("Time: %s sec" % (end_time))
        return self.stop_time

class Time:

    __timezone: str = None
    __format: str = None

    default_format: str = '%Y-%m-%d %H:%M:%S.%f'
    default_timezone: dt_timezone = dt_timezone.utc

    def __init__(self, 
        timezone: str | dt_timezone = None, 
        timeformat: str = None
        ):

        self.timezone = timezone
        self.format = timeformat

    class timer:
        
        def __init__(self) -> None:
            
            self._timer = Timer()
            
            self._start_time = self._timer.start()
            
            self._stop_time = -1
            
            self.__total_sec = -1

        @property
        def total_sec(self) -> float:

            return self.__total_sec

        def stop(self) -> float:

            self._stop_time = time()

            self.__total_sec = self._stop_time - self._start_time

            return self.__total_sec

    @property
    def timezone(self) -> str:

        if self.__timezone is None:
            return self.default_timezone
        else:
            return self.__timezone
        
    @timezone.setter
    def timezone(self, value: str | dt_timezone) -> None:

        if isinstance(value, str) == True:
            self.__timezone = pytz.timezone(value)

        elif isinstance(value, dt_timezone) == True:
            self.__timezone = value

        else:
            self.__timezone = 'UTC'

    @property
    def format(self) -> str:

        if self.__format is None:
            return self.default_format
        
        else:
            return self.__format
        
    @format.setter
    def format(self, value: str) -> None:

        if value is None or value == "" or isinstance(value, str) == False:
            self.__format = self.default_format
            
        else:
            self.__format = value

    def unixTimestampsDiff(self, tstamp1: float, tstamp2: float) -> float:
        
        if tstamp1 > tstamp2:
            td = tstamp1 - tstamp2
            
        else:
            td = tstamp2 - tstamp1
            
        td_sec = int(round(td))
        return td_sec

    def unixTimestampNow(self) -> float:
        return time()

    def strftimeToFormat(self, format: str) -> str:
        return pydateinfer.infer([format])

    def unixTimestampToDatetime(self, timestamp: float, tz: str | dt_timezone = None) -> datetime:
        # return datetime.fromtimestamp(timestamp).astimezone(pytz.timezone(self.timezone)).strftime(self.format)

        if isinstance(tz, str) == True:
            tz = pytz.timezone(tz)

        if tz is None:
            tz = self.timezone

        tz = self.timezone if tz is None else tz

        return datetime.fromtimestamp(timestamp, tz=tz)

    def strftimeToDatetime(self, strftime) -> datetime:
        return dateutil_phase(strftime)

    def datetimeToStrftime(self, dt: datetime, tz: str | dt_timezone = None, format: str = None) -> str:

        format = self.format if format is None else format

        if isinstance(tz, str) == True:
            tz = pytz.timezone(tz)

        if tz is None:
            tz = self.timezone

        return dt.astimezone(tz=tz).strftime(format)

    def strfTime(self, ms: bool = True) -> str:

        #utcnow = datetime.utcnow()
        tznow = self.timeNow()  #utcnow.astimezone(pytz.timezone(self.timezone))

        format = self.format.replace(".%f", "") if ms == False else self.format

        tznowFormated = tznow.strftime(format)

        return tznowFormated
    
    def now(self, tz: str | dt_timezone = None) -> datetime:

        return self.timeNow(
            tz = tz
        )

    def timeNow(self, tz: str | dt_timezone = None) -> datetime:

        if isinstance(tz, str) == True:
            tz = pytz.timezone(tz)

        if tz is None:
            tz = self.timezone

        return datetime.now(tz=tz)

class TimeDiff:

    def __init__(self, 
        date1, 
        date2,
        fmt = '%Y:%m:%d:%H:%M:%S'
        ) -> None:
        
        self.date1 = date1
        
        self.date2 = date2
        
        self.fmt = fmt

    def getDateStringDiff(self):
        
        timeDiff = TimeDiff.TimeData()

        timeDiff.date1 = datetime.strptime(self.date1, self.fmt)
        timeDiff.date2 = datetime.strptime(self.date2, self.fmt)
        timeDiff.totalSeconds = (timeDiff.date2 - timeDiff.date1).total_seconds()
        
        seconds = timeDiff.totalSeconds
        seconds_in_day = 60 * 60 * 24
        seconds_in_hour = 60 * 60
        seconds_in_minute = 60

        timeDiff.days = int(seconds) // seconds_in_day
        timeDiff.hours = int(seconds - (timeDiff.days * seconds_in_day)) // seconds_in_hour
        timeDiff.minutes = int(seconds - (timeDiff.days * seconds_in_day) - (timeDiff.hours * seconds_in_hour)) // seconds_in_minute
        
        timeDiff.seconds = int(seconds - (timeDiff.days * seconds_in_day) - (timeDiff.hours * seconds_in_hour) - (timeDiff.minutes * seconds_in_minute))
        
        timeDiff.timedelta = timedelta(days=timeDiff.days, hours=timeDiff.hours, minutes=timeDiff.minutes, seconds=timeDiff.seconds)

        timeDiff.strfdelta = TimeDiff.strfdelta(timeDiff.timedelta, hideNull = True)
        
        timeDiff.strfdeltaFull = TimeDiff.strfdelta(timeDiff.timedelta, hideNull = False)

        return timeDiff

    def strfdelta(self, 
        td, 
        str_day = "day",
        str_days = "days",
        str_hour = "hour",
        str_hours = "hours",
        str_min = "min",
        str_mins = "mins",
        str_sec = "sec",
        str_secs = "secs",
        hideNull = False
        ):

        # Get the timedelta’s sign and absolute number of seconds.
        sign = "-" if td.days < 0 else "+"
        secs = abs(td).total_seconds()

        # Break the seconds into more readable quantities.
        year = 0
        days, rem = divmod(secs, 86400)  # Seconds per day: 24 * 60 * 60
        hours, rem = divmod(rem, 3600)  # Seconds per hour: 60 * 60
        mins, secs = divmod(rem, 60)
        
        Dtext = str_days if int(days) > 1 else str_day
        DPreFmt = '%D ' + Dtext + " "
        Dfmt = DPreFmt if int(days) > 0 else ("" if hideNull == True else DPreFmt)

        Htext = str_hours if int(hours) > 1 else str_hour
        HPreFmt = '%H ' + Htext + " "
        Hfmt = HPreFmt if int(hours) > 0 else ("" if hideNull == True else HPreFmt)
        
        Mtext = str_mins if int(mins) > 1 else str_min
        MPreFmt = '%M ' + Mtext + " "
        Mfmt = MPreFmt if int(mins) > 0 else ("" if hideNull == True else MPreFmt)

        Stext = str_secs if int(secs) > 1 else str_sec
        SPreFmt = '%S ' + Stext + ""
        Sfmt = SPreFmt if int(secs) > 0 else ("" if hideNull == True else SPreFmt)

        fmt = Dfmt + Hfmt + Mfmt + Sfmt

        # Format (as per above answers) and return the result string.
        t = TimeDiff.DeltaTemplate(fmt)
        
        return t.substitute(
            s = sign,
            D = "{:0d}".format(int(days)),
            H = "{:0d}".format(int(hours)),
            M = "{:0d}".format(int(mins)),
            S = "{:0d}".format(int(secs)),
        )

    class DeltaTemplate(Template):
        delimiter = '%'

    class TimeData:
        days = 0
        hours = 0
        minutes = 0
        seconds = 0
        
        totalSeconds = 0
        
        date1 = None
        date2 = None
        
        timedelta = None
        
        strfdelta = None
        strfdeltaFull = None
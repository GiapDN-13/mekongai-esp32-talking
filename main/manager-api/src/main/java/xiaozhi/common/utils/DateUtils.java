package xiaozhi.common.utils;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.Date;

/**
 * Date/time formatting helpers.
 * Copyright (c) Renren Open Source. All rights reserved.
 * Website: https://www.renren.io
 */
public class DateUtils {
    /** Pattern: yyyy-MM-dd */
    public final static String DATE_PATTERN = "yyyy-MM-dd";
    /** Pattern: yyyy-MM-dd HH:mm:ss */
    public final static String DATE_TIME_PATTERN = "yyyy-MM-dd HH:mm:ss";
    public final static String DATE_TIME_MILLIS_PATTERN = "yyyy-MM-dd HH:mm:ss.SSS";


    /** Format with {@link #DATE_PATTERN}. */
    public static String format(Date date) {
        return format(date, DATE_PATTERN);
    }

    /** Format with the given {@link SimpleDateFormat} pattern. */
    public static String format(Date date, String pattern) {
        if (date != null) {
            SimpleDateFormat df = new SimpleDateFormat(pattern);
            return df.format(date);
        }
        return null;
    }

    /** Parse string to {@link Date}; returns null on failure. */
    public static Date parse(String date, String pattern) {
        try {
            return new SimpleDateFormat(pattern).parse(date);
        } catch (ParseException e) {
            e.printStackTrace();
        }
        return null;
    }


    public static String getDateTimeNow() {
        return getDateTimeNow(DATE_TIME_PATTERN);
    }

    public static String getDateTimeNow(String pattern) {
        return format(new Date(), pattern);
    }

    public static String millsToSecond(long mills) {
        return String.format("%.3f", mills / 1000.0);
    }

    /**
     * Relative English label (e.g. "just now", "5m ago"); falls back to full datetime after one week.
     */
    public static String getShortTime(Date date) {
        if (date == null) {
            return null;
        }
        LocalDateTime localDateTime = date.toInstant()
                .atZone(ZoneId.systemDefault())
                .toLocalDateTime();
        LocalDateTime now = LocalDateTime.now();
        long secondsBetween = ChronoUnit.SECONDS.between(localDateTime, now);

        if (secondsBetween <= 10) {
            return "just now";
        } else if (secondsBetween < 60) {
            return secondsBetween + "s ago";
        } else if (secondsBetween < 60 * 60) {
            return secondsBetween / 60 + "m ago";
        } else if (secondsBetween < 86400) {
            return secondsBetween / 3600 + "h ago";
        } else if (secondsBetween < 604800) {
            return secondsBetween / 86400 + "d ago";
        } else {
            return format(date,DATE_TIME_PATTERN);
        }
    }
}

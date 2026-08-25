export function solve({ cron, from, count }) {
  const [minute, hour, dayOfMonth, month, dayOfWeek] = cron.split(' ');
  const parsedCron = {
    minute: parseCronField(minute),
    hour: parseCronField(hour),
    dayOfMonth: parseCronField(dayOfMonth),
    month: parseCronField(month),
    dayOfWeek: parseCronField(dayOfWeek),
  };

  function parseCronField(field) {
    const parts = field.split(',');
    if (parts.length === 1 && !field.includes('-') && !field.includes('/')) {
      return [Number.parseInt(part, 10)];
    }
    const values = [];
    for (const part of parts) {
      if (part.startsWith('*/')) {
        const step = Number.parseInt(part.substring(2), 10);
        for (let i = 0; i < 60; i += step) {
          values.push(i);
        }
      } else if (part.includes('-')) {
        const [start, end] = part.split('-').map(Number.parseInt);
        for (let i = start; i <= end; i++) {
          values.push(i);
        }
      } else if (part.includes('/')) {
        const [start, step] = part.split('/');
        for (let i = Number.parseInt(start); i < 60; i += Number.parseInt(step)) {
          values.push(i);
        }
      } else {
        values.push(Number.parseInt(part, 10));
      }
    }
    return values;
  }

  function getNextRuns(currentTime, parsedCron) {
    const nextRunTimes = [];
    while (nextRunTimes.length < count) {
      let foundMatch = false;
      for (const minuteVal of parsedCron.minute) {
        if (parsedCron.minute.includes(minuteVal)) {
          for (const hourVal of parsedCron.hour) {
            if (parsedCron.hour.includes(hourVal)) {
              for (const dayOfMonthVal of parsedCron.dayOfMonth) {
                if (parsedCron.dayOfMonth.includes(dayOfMonthVal)) {
                  for (const monthVal of parsedCron.month) {
                    if (parsedCron.month.includes(monthVal)) {
                      for (const dayOfWeekVal of parsedCron.dayOfWeek) {
                        if (
                          (parsedCron.dayOfMonth.includes('*') || dayOfMonthVal === Number.parseInt(dayOfWeekVal, 10))
                          && (parsedCron.dayOfWeek.includes('*') || dayOfWeekVal === Number.parseInt(minuteVal, 10))
                        ) {
                          const nextRun = new Date(currentTime);
                          nextRun.setUTCSeconds(minuteVal * 60 + hourVal * 3600 + dayOfMonthVal * 86400 + monthVal * 2592000 + dayOfWeekVal * 604800);
                          nextRun.setMilliseconds(0);
                          nextRunTimes.push(nextRun.toISOString());
                        }
                      }
                    } else {
                      for (const dayOfWeekVal of parsedCron.dayOfWeek) {
                        if (
                          (parsedCron.dayOfMonth.includes('*') || dayOfMonthVal === Number.parseInt(dayOfWeekVal, 10))
                          && (parsedCron.dayOfWeek.includes('*') || dayOfWeekVal === Number.parseInt(minuteVal, 10))
                        ) {
                          const nextRun = new Date(currentTime);
                          nextRun.setUTCSeconds(minuteVal * 60 + hourVal * 3600 + dayOfMonthVal * 86400 + monthVal * 2592000 + dayOfWeekVal * 604800);
                          nextRun.setMilliseconds(0);
                          nextRunTimes.push(nextRun.toISOString());
                        }
                      }
                    }
                  } else {
                    for (const dayOfWeekVal of parsedCron.dayOfWeek) {
                      if (
                        (parsedCron.dayOfMonth.includes('*') || dayOfMonthVal === Number.parseInt(dayOfWeekVal, 10))
                        && (parsedCron.dayOfWeek.includes('*') || dayOfWeekVal === Number.parseInt(minuteVal, 10))
                      ) {
                        const nextRun = new Date(currentTime);
                        nextRun.setUTCSeconds(minuteVal * 60 + hourVal * 3600 + dayOfMonthVal * 86400 + monthVal * 2592000 + dayOfWeekVal * 604800);
                        nextRun.setMilliseconds(0);
                        nextRunTimes.push(nextRun.toISOString());
                      }
                    }
                  }
                } else {
                  for (const dayOfWeekVal of parsedCron.dayOfWeek) {
                    if (
                      (parsedCron.dayOfMonth.includes('*') || dayOfMonthVal === Number.parseInt(dayOfWeekVal, 10))
                      && (parsedCron.dayOfWeek.includes('*') || dayOfWeekVal === Number.parseInt(minuteVal, 10))
                    ) {
                      const nextRun = new Date(currentTime);
                      nextRun.setUTCSeconds(minuteVal * 60 + hourVal * 3600 + dayOfMonthVal * 86400 + monthVal * 2592000 + dayOfWeekVal * 604800);
                      nextRun.setMilliseconds(0);
                      nextRunTimes.push(nextRun.toISOString());
                    }
                  }
                }
              } else {
                for (const dayOfWeekVal of parsedCron.dayOfWeek) {
                  if (
                    (parsedCron.dayOfMonth.includes('*') || dayOfMonthVal === Number.parseInt(dayOfWeekVal, 10))
                    && (parsedCron.dayOfWeek.includes('*') || dayOfWeekVal === Number.parseInt(minuteVal, 10))
                  ) {
                    const nextRun = new Date(currentTime);
                    nextRun.setUTCSeconds(minuteVal * 60 + hourVal * 3600 + dayOfMonthVal * 86400 + monthVal * 2592000 + dayOfWeekVal * 604800);
                    nextRun.setMilliseconds(0);
                    nextRunTimes.push(nextRun.toISOString());
                  }
                }
              }
            } else {
              for (const dayOfMonthVal of parsedCron.dayOfMonth) {
                if (
                  (parsedCron.dayOfMonth.includes('*') || dayOfMonthVal === Number.parseInt(dayOfWeekVal, 10))
                  && (parsedCron.dayOfWeek.includes('*') || dayOfWeekVal === Number.parseInt(minuteVal, 10))
                ) {
                  const nextRun = new Date(currentTime);
                  nextRun.setUTCSeconds(minuteVal * 60 + hourVal * 3600 + dayOfMonthVal * 86400 + monthVal * 2592000 + dayOfWeekVal * 604800);
                  nextRun.setMilliseconds(0);
                  nextRunTimes.push(nextRun.toISOString());
                }
              }
            }
          } else {
            for (const monthVal of parsedCron.month) {
              if (
                (parsedCron.dayOfMonth.includes('*') || dayOfMonthVal === Number.parseInt(dayOfWeekVal, 10))
                && (parsedCron.dayOfWeek.includes('*') || dayOfWeekVal === Number.parseInt(minuteVal, 10))
              ) {
                const nextRun = new Date(currentTime);
                nextRun.setUTCSeconds(minuteVal * 60 + hourVal * 3600 + dayOfMonthVal * 86400 + monthVal * 2592000 + dayOfWeekVal * 604800);
                nextRun.setMilliseconds(0);
                nextRunTimes.push(nextRun.toISOString());
              }
            }
          }
        } else {
          for (const dayOfMonthVal of parsedCron.dayOfMonth) {
            if (
              (parsedCron.dayOfMonth.includes('*') || dayOfMonthVal === Number.parseInt(dayOfWeekVal, 10))
              && (parsedCron.dayOfWeek.includes('*') || dayOfWeekVal === Number.parseInt(minuteVal, 10))
            ) {
              const nextRun = new Date(currentTime);
              nextRun.setUTCSeconds(minuteVal * 60 + hourVal * 3600 + dayOfMonthVal * 86400 + monthVal * 2592000 + dayOfWeekVal * 604800);
              nextRun.setMilliseconds(0);
              nextRunTimes.push(nextRun.toISOString());
            }
          }
        }
      } else {
        for (const dayOfMonthVal of parsedCron.dayOfMonth) {
          if (
            (parsedCron.dayOfMonth.includes('*') || dayOfMonthVal === Number.parseInt(dayOfWeekVal, 10))
            && (parsedCron.dayOfWeek.includes('*') || dayOfWeekVal === Number.parseInt(minuteVal, 10))
          ) {
            const nextRun = new Date(currentTime);
            nextRun.setUTCSeconds(minuteVal * 60 + hourVal * 3600 + dayOfMonthVal * 86400 + monthVal * 2592000 + dayOfWeekVal * 604800);
            nextRun.setMilliseconds(0);
            nextRunTimes.push(nextRun.toISOString());
          }
        }
      }
    }
    return nextRunTimes;
  }

  const parsedFrom = new Date(from.replace('Z', '+00:00'));
  let currentTime = new Date(parsedFrom);
  while (currentTime < parsedFrom) {
    currentTime.setUTCSeconds(currentTime.getUTCSeconds() + 1);
  }
  return getNextRuns(currentTime, parsedCron).slice(0, count);
}
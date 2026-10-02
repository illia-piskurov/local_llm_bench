export function solve(input) {
  const parseField = (field, min, max) => {
    const result = new Set();
    if (field === '*') {
      for (let i = min; i <= max; i++) result.add(i);
      return result;
    }
    const parts = field.split(',');
    for (const part of parts) {
      let step = 1;
      let rangePart = part;
      if (part.includes('/')) {
        [rangePart, step] = part.split('/');
        step = parseInt(step, 10);
      }
      if (rangePart === '*') {
        for (let i = min; i <= max; i += step) result.add(i);
      } else if (rangePart.includes('-')) {
        const [a, b] = rangePart.split('-').map(Number);
        for (let i = a; i <= b; i += step) result.add(i);
      } else {
        const val = parseInt(rangePart, 10);
        if (val >= min && val <= max) result.add(val);
      }
    }
    return result;
  };

  const [cronMinute, cronHour, cronDom, cronMonth, cronDow] = input.cron.split(' ');
  const minutesSet = parseField(cronMinute, 0, 59);
  const hoursSet   = parseField(cronHour,   0, 23);
  const domSet     = parseField(cronDom,    1, 31);
  const monthSet   = parseField(cronMonth,  1, 12);
  const dowSet     = parseField(cronDow,    0, 6);

  const domStar   = cronDom === '*';
  const dowStar   = cronDow === '*';

  const start = new Date(input.from);
  start.setUTCSeconds(0, 0); // zero seconds and ms
  let current = new Date(start.getTime() + 60000); // first minute after 'from'
  const result = [];

  while (result.length < input.count) {
    const minute = current.getUTCMinutes();
    const hour   = current.getUTCHours();
    const day    = current.getUTCDate();
    const month  = current.getUTCMonth() + 1; // JS months 0-11
    const weekday= current.getUTCDay();

    if (!minutesSet.has(minute)) { current = new Date(current.getTime() + 60000); continue; }
    if (!hoursSet.has(hour)) { current = new Date(current.getTime() + 60000); continue; }
    if (!monthSet.has(month)) { current = new Date(current.getTime() + 60000); continue; }

    const domMatch = domSet.has(day);
    const dowMatch = dowSet.has(weekday);

    let dayMatches;
    if (!domStar && !dowStar) {
      dayMatches = domMatch || dowMatch;
    } else if (!domStar && dowStar) {
      dayMatches = domMatch;
    } else if (domStar && !dowStar) {
      dayMatches = dowMatch;
    } else {
      dayMatches = true; // both stars
    }

    if (dayMatches) {
      result.push(current.toISOString().replace(/\.\d{3}Z$/, '.000Z'));
    }
    current = new Date(current.getTime() + 60000);
  }

  return result;
}
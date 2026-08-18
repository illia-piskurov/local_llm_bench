export function solve(input) {
    // Helper to parse cron field syntax (e.g., "*/15", "9-17", "1,5") into an array of integers.
    const parseField = (fieldStr, maxVal) => {
        if (!fieldStr || fieldStr === "*") {
            return Array.from({ length: maxVal }, (_, i) => i);
        }

        const results = [];
        // Handle step/range syntax: X-Y/S or */S
        let segments = fieldStr.split(',');
        for (const segment of segments) {
            let parts = segment.split('/');
            let baseStr = parts[0];
            let step = 1;

            if (parts.length > 1) {
                step = parseInt(parts[1], 10);
            }

            let rangeStarts = [];
            if (baseStr.includes('-')) {
                // Range format: X-Y
                const [start, end] = baseStr.split('-').map(Number);
                rangeStarts.push({ start, end });
            } else {
                // Single value or step from start=0
                rangeStarts.push({ start: parseInt(baseStr), end: parseInt(baseStr) });
            }

            for (const range of rangeStarts) {
                let current = range.start;
                while (current <= range.end) {
                    if (current >= 0 && current < maxVal) {
                        results.push(current);
                    }
                    current += step;
                }
            }
        }

        // Ensure uniqueness and sort, although the process above should maintain order.
        return Array.from(new Set(results)).sort((a, b) => a - b);
    };

    // --- 1. Parse Cron Fields ---
    const [minuteCron, hourCron, dayOfMonthCron, monthCron, dayOfWeekCron] = input.cron.split(' ');

    // Field constraints (0-59 for minutes, 0-23 for hours, etc.)
    const M_MAX = 60;
    const H_MAX = 24;
    const DoM_MAX = 31;
    const Mth_MAX = 12;
    const DOW_MAX = 7;

    // Parse into lists of allowed values (0-indexed for arrays, but using natural ranges)
    const minutesAllowed = parseField(minuteCron, M_MAX);
    const hoursAllowed = parseField(hourCron, H_MAX);
    const daysOfMonthAllowed = parseField(dayOfMonthCron, DoM_MAX);
    // Month input is 1-indexed (1=Jan, 12=Dec)
    const monthsAllowed = parseField(monthCron, Mth_MAX + 1).map(m => m === 0 ? -1 : m); // Treat failure/out of bounds as invalid
    // DayOfWeek input is 0-6 (0=Sun, ..., 6=Sat)
    const daysOfWeekAllowed = parseField(dayOfWeekCron, DOW_MAX);

    /**
     * Checks if a given date matches the cron expression.
     * @param {Date} date - The date object to check (must be in UTC).
     * @returns {boolean} True if it matches the schedule.
     */
    const isMatch = (date) => {
        // Date components retrieved using UTC methods
        const m = date.getUTCMonth() + 1; // 1-12
        const h = date.getUTCHours();   // 0-23
        const dayOfMonth = date.getUTCDate(); // 1-31
        const month = date.getUTCMonth() + 1;  // 1-12 (M)
        const dow = date.getUTCDay();         // 0-6 (DOW)

        // 1. Check Minute and Hour
        if (!minutesAllowed.includes(date.getUTCMinutes())) return false;
        if (!hoursAllowed.includes(h)) return false;

        // 2. Check Month
        const monthsMatch = monthsAllowed.includes(m);
        if (!monthsMatch) return false;

        // 3. Check Day of Month and Day of Week (OR rule logic)
        let doM_match = daysOfMonthAllowed.includes(dayOfMonth);
        let dow_match = daysOfWeekAllowed.includes(dow);

        if (doM_match && dow_match) {
            // If both are specified, it must match EITHER OR
            return true;
        } else if (!doM_match && !dow_match) {
            // Must match nothing
            return false;
        } else if (doM_match && !doM_match && !*/*) { // This handles the case where both * and * are specified, but since they are parsed correctly, this path is simplified.

             // If one is '*' (meaning it's allowed by default), the other must be checked.
            const doM_star = dayOfMonthCron === "*";
            const dow_star = dayOfWeekCron === "*";

            if (doM_star && !dow_star) {
                // DoM matches (*), DayOfWeek must match specified range/list
                return dow_match;
            }
            if (!doM_star && doM_star) {
                // DayOfWeek matches (*), DoM must match specified range/list
                return doM_match;
            }
        }

        // The rule: If both are not *, day matches if EITHER matches (OR rule). If one is *, the other is strictly matched.
        if (!dayOfMonthCron === "*" && !dayOfWeekCron === "*") {
             // Both specified, use OR logic
             return doM_match || dow_match;
        } else if (dayOfMonthCron === "*" && dayOfWeekCron !== "*") {
            // DoM is *, DayOfWeek must match
            return dow_match;
        } else if (dayOfMonthCron !== "*" && dayOfWeekCron === "*") {
             // DoW is *, DoM must match
            return doM_match;
        } else {
            // Both are '*' (Always true for date components)
            return true;
        }
    };

    // --- 2. Iteration Setup ---
    let currentTime = new Date(input.from); // Start at the given 'from' time
    let countRemaining = input.count;
    const results = [];

    if (!isNaN(currentTime)) {
        // We must search for times STRICTLY AFTER input.from
        // Move time forward by 1 millisecond to start searching after the specified point.
        currentTime = new Date(currentTime.getTime() + 1);
    } else {
        throw new Error("Invalid 'from' timestamp provided.");
    }

    /**
     * Advances currentTime to the next moment that *might* be a match,
     * preventing minute-by-minute iteration if possible.
     */
    const advanceTime = () => {
        // Since cron matching is complex due to DoM/DoW interaction, 
        // simply advancing by one day or even an hour might miss matches.
        // The safest approach for reliability given the complexity of scheduling rules 
        // (especially year rollover) is usually millisecond advance, but that's slow.

        // Optimized Advance: Check every minute until a match is found or we exceed a reasonable search window.
        // For simplicity and robustness in this synchronous environment, we will advance by minutes,
        // assuming the input count is not astronomical (i.e., doesn't require simulating years).

        let nextTime = new Date(currentTime);
        nextTime.setMinutes(nextTime.getMinutes() + 1);
        return nextTime;
    };


    // --- 3. Search Loop ---
    while (countRemaining > 0) {
        const candidateDate = new Date(currentTime);

        if (isMatch(candidateDate)) {
            // Format output: ISO UTC timestamp string, seconds & ms set to 00:00.000Z
            const isoString = candidateDate.toISOString();
            results.push(isoString.substring(0, 19) + '.000Z');

            countRemaining--;
        }

        if (countRemaining > 0) {
            // Advance time to the next minute for checking
            currentTime = advanceTime();
        }
    }

    return results;
}
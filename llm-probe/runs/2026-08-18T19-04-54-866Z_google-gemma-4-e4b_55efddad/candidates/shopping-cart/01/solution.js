export function solve(input) {
    // Helper function for consistent rounding
    const roundToTwoDecimals = (value) => Math.round(value * 100) / 100;

    // --- 1. Calculate Subtotal ---
    let subtotal = input.items.reduce((sum, item) => {
        return sum + (item.price || 0) * (item.qty || 0);
    }, 0);

    subtotal = roundToTwoDecimals(subtotal);

    // --- 2. Calculate Discount ---
    let discount = 0;
    const coupon = input.coupon;

    if (coupon && typeof coupon.type === 'string') {
        let calculatedDiscount = 0;

        try {
            switch (coupon.type) {
                case 'percent':
                    {
                        // Rule: X% off subtotal
                        const value = parseFloat(coupon.value);
                        if (!isNaN(value) && value >= 0) {
                            calculatedDiscount = subtotal * (value / 100);
                        }
                    } break;

                case 'fixed':
                    {
                        // Rule: Flat $ amount off, capped at subtotal
                        const value = parseFloat(coupon.value);
                        if (!isNaN(value) && value >= 0) {
                            calculatedDiscount = Math.min(subtotal, value);
                        }
                    } break;

                case 'category_percent':
                    {
                        // Rule: % off specific category items
                        const category = coupon.category;
                        const value = parseFloat(coupon.value);

                        if (category && !isNaN(value) && value >= 0) {
                            let eligibleSubtotal = input.items.reduce((sum, item) => {
                                if (item.category === category) {
                                    return sum + (item.price || 0) * (item.qty || 0);
                                }
                                return sum;
                            }, 0);

                            // Apply discount percentage to eligible subtotal
                            calculatedDiscount = eligibleSubtotal * (value / 100);
                        }
                    } break;

                default:
                    // Unknown type, discount remains 0
            }
        } catch (e) {
            // Safety net for unknown coupon structures
        }

        discount = roundToTwoDecimals(calculatedDiscount);
    }
    
    // Ensure discount does not exceed subtotal (although the logic above should handle this, it's a safety check)
    discount = Math.min(subtotal, discount);


    // --- 3. Calculate Tax ---
    let taxRate = parseFloat(input.taxRate);
    if (isNaN(taxRate)) {
        taxRate = 0;
    }

    // Tax is calculated on (subtotal - discount)
    const taxableBase = subtotal - discount;
    
    // Math.round((base * taxRate) * 100) / 100
    let tax = roundToTwoDecimals(taxableBase * taxRate);


    // --- 4. Calculate Total ---
    // Formula: (subtotal - discount + tax) rounded to two decimal places
    const totalValue = subtotal - discount + tax;
    let total = roundToTwoDecimals(totalValue);

    return {
        subtotal: Math.round(subtotal * 100) / 100,
        discount: Math.round(discount * 100) / 100,
        tax: tax,
        total: total
    };
}
export function solve(input) {
    const round = (num) => Math.round(num * 100) / 100;

    // 1. Subtotal Calculation
    let subtotalRaw = input.items.reduce((acc, item) => acc + (item.price * item.qty), 0);
    const subtotal = round(subtotalRaw);

    // Initialize discount
    let discountAmount = 0;

    if (input.coupon && input.coupon.type) {
        const coupon = input.coupon;

        switch (coupon.type) {
            case 'percent':
                const percentDiscount = subtotal * (coupon.value / 100);
                discountAmount = Math.min(subtotal, percentDiscount);
                break;

            case 'fixed':
                // Fixed discount cannot exceed the subtotal
                discountAmount = Math.min(subtotal, coupon.value);
                break;

            case 'category_percent': {
                const category = coupon.category;
                const value = coupon.value;
                let categoryDiscountRaw = 0;

                if (category && typeof value === 'number' && value > 0) {
                    // Calculate discount only for matching categories
                    for (const item of input.items) {
                        if (item.category === category) {
                            const itemSubtotal = item.price * item.qty;
                            const categoryDiscountForItem = itemSubtotal * (value / 100);
                            categoryDiscountRaw += categoryDiscountForItem;
                        }
                    }
                }

                // Cap the discount at subtotal
                discountAmount = Math.min(subtotal, categoryDiscountRaw);
                break;
            }
        }
    } else {
        discountAmount = 0;
    }

    // Apply rounding to the determined discount amount
    const finalDiscount = round(discountAmount);

    // Calculate base for tax (must be non-negative)
    const taxableBase = Math.max(0, subtotal - finalDiscount);

    // 3. Tax Calculation
    let taxRate = input.taxRate !== undefined ? input.taxRate : 0;
    
    // Rule: Math.round((subtotal - discount) * taxRate * 100) / 100. (0 if taxRate omitted).
    const taxRaw = taxableBase * taxRate;
    const tax = round(taxRaw);

    // 4. Total Calculation
    // Rule: Math.round((subtotal - discount + tax) * 100) / 100
    const totalRaw = subtotal - finalDiscount + tax;
    const total = round(totalRaw);


    return {
        subtotal: parseFloat(subtotal.toFixed(2)),
        discount: parseFloat(finalDiscount.toFixed(2)),
        tax: parseFloat(tax.toFixed(2)),
        total: parseFloat(total.toFixed(2))
    };
}
export function solve(input) {
    let subtotal = 0;
    const items = input.items || [];

    // 1. Calculate Subtotal
    for (const item of items) {
        subtotal += item.price * item.qty;
    }

    let discount = 0;
    const coupon = input.coupon;
    const taxRate = input.taxRate || 0;

    if (coupon) {
        const type = coupon.type;
        const value = coupon.value;

        if (type === 'percent') {
            discount = subtotal * (value / 100);
        } else if (type === 'fixed') {
            discount = Math.min(subtotal, value);
        } else if (type === 'category_percent' && coupon.category) {
            let categorySubtotal = 0;
            for (const item of items) {
                if (item.category === coupon.category) {
                    categorySubtotal += item.price * item.qty;
                }
            }
            discount = categorySubtotal * (value / 100);
        }
    }

    // Ensure discount does not exceed subtotal
    if (discount > subtotal) {
        discount = subtotal;
    }

    // 2. Calculate Tax
    let netAmount = subtotal - discount;
    let tax = netAmount * taxRate;

    // 3. Calculate Total
    let total = netAmount + tax;


    // Helper function for rounding to 2 decimal places
    const roundToTwoDecimals = (amount) => Math.round(amount * 100) / 100;

    return {
        subtotal: roundToTwoDecimals(subtotal),
        discount: roundToTwoDecimals(discount),
        tax: roundToTwoDecimals(tax),
        total: roundToTwoDecimals(total)
    };
}
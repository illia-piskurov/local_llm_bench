/**
 * Calculates cart totals from input items, coupon, and tax rate.
 * 
 * Rules:
 * - subtotal: sum of (price * qty) for all items
 * - discount: based on coupon type (percent, fixed, or category-based)
 *   * percent type: applied to subtotal
 *   * fixed type: flat amount off (capped at subtotal if applicable)
 *   * category_percent type: applies only to specified categories
 *   * unknown or missing coupon: no discount applied
 * - tax: Math.round((subtotal - discount) * taxRate / 100), rounded to 2 decimals
 * - total: Math.round((subtotal - discount + tax) / 100), rounded to 2 decimals
 */
export function solve(input) {
    // Step 1: Calculate subtotal from items
    let subtotal = 0;
    for (const item of input.items) {
        const price = Number(item.price);
        const qty = Number(item.qty);
        if (!Number.isNaN(price) && !isNaN(qty)) {
            subtotal += price * qty;
        }
    }

    // Step 2: Handle discount from coupon
    let discount = 0;
    let hasCoupon = false;

    if (input.coupon !== undefined) {
        hasCoupon = true;
        const couponType = input.coupon.type.toLowerCase();
        
        if (couponType === 'percent') {
            // Percent-based discount: apply to subtotal
            discount = Math.round((subtotal * input.coupon.value) / 100);
        } else if (couponType === 'fixed') {
            // Fixed amount discount, capped at subtotal
            const flatDiscount = Number(input.coupon.value);
            if (!isNaN(flatDiscount)) {
                discount = Math.min(discount + flatDiscount, subtotal);
            }
        } else if (couponType === 'category_percent') {
            // Category-specific discount
            const category = input.coupon.category.toLowerCase();
            if (category) {
                for (const item of input.items) {
                    const price = Number(item.price);
                    const qty = Number(item.qty);
                    if (!isNaN(price) && !isNaN(qty)) {
                        subtotal += price * qty; // recalculate total with category items
                    }
                }
            }
        }
    }

    // Step 3: Calculate tax and total (after discount)
    const taxableAmount = subtotal - discount;
    const taxRate = input.taxRate !== undefined ? Number(input.taxRate) : 0;

    const tax = Math.round(taxableAmount * taxRate / 100);
    const total = Math.round((taxableAmount + tax) / 100);

    return { subtotal, discount: discount === 0 ? null : Number(discount.toFixed(2)), tax: parseFloat(tax), total: parseFloat(total.toFixed(2)) };
}
export function solve(input) {
    const items = input.items;
    let subtotal = 0;

    for (const item of items) {
        subtotal += Math.round((item.price * item.qty) * 100) / 100;
    }

    const discount = calculateDiscount(items, input.coupon);
    const taxableAmount = Math.round(((subtotal - discount) * 100) / 100);
    const tax = input.taxRate ? Math.round((taxableAmount * input.taxRate) * 100) / 100 : 0;
    const total = Math.round((subtotal - discount + tax) * 100) / 100;

    return {
        subtotal,
        discount: Math.round(discount * 100) / 100,
        tax: tax.toFixed(2),
        total: total.toFixed(2)
    };

    function calculateDiscount(items, coupon) {
        if (!coupon || !('type' in coupon)) return 0;

        const subtotal = items.reduce((sum, item) => sum + Math.round((item.price * item.qty) * 100) / 100, 0);

        switch (coupon.type) {
            case 'percent':
                return Math.min(subtotal * coupon.value / 100, subtotal);
            case 'fixed':
                return Math.min(coupon.value, subtotal);
            case 'category_percent':
                const categoryItems = items.filter(item => item.category === coupon.category);
                const categorySubtotal = categoryItems.reduce((sum, item) =>
                    sum + Math.round((item.price * item.qty) * 100) / 100, 0);
                return Math.min(categorySubtotal * coupon.value / 100, subtotal);
            default:
                return 0;
        }
    }
}
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

    return { subtotal, discount, tax, total };

    function calculateDiscount(items, coupon) {
        if (!coupon || !('type' in coupon)) return 0;

        switch (coupon.type) {
            case 'percent':
                const percentDiscount = Math.round((subtotal * coupon.value / 100) * 100) / 100;
                return Math.min(percentDiscount, subtotal);
            case 'fixed':
                const fixedDiscount = Math.min(coupon.value, subtotal);
                return Math.round(fixedDiscount * 100) / 100;
            case 'category_percent':
                let categorySubtotal = 0;
                for (const item of items) {
                    if (item.category === coupon.category) {
                        categorySubtotal += Math.round((item.price * item.qty) * 100) / 100;
                    }
                }
                const categoryPercentDiscount = Math.round((categorySubtotal * coupon.value / 100) * 100) / 100;
                return Math.min(categoryPercentDiscount, subtotal);
            default:
                return 0;
        }
    }
}
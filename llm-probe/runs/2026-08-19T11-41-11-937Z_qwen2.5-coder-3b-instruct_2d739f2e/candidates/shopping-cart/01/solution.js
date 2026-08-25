export function solve(input) {
    const { items, coupon, taxRate } = input;
    let subtotal = 0;
    let discount = 0;

    // Calculate subtotal
    items.forEach(item => {
        subtotal += item.price * item.qty;
    });

    // Apply discount based on coupon type and category
    if (coupon) {
        switch (coupon.type) {
            case 'percent':
                discount = Math.min(subtotal * coupon.value / 100, subtotal);
                break;
            case 'fixed':
                discount = Math.min(coupon.value, subtotal);
                break;
            case 'category_percent':
                const categoryDiscount = items.reduce((acc, item) => {
                    return acc + (item.category === coupon.category ? item.price * item.qty : 0);
                }, 0);
                discount = Math.min(categoryDiscount * coupon.value / 100, subtotal);
                break;
            default:
                discount = 0;
        }
    }

    // Calculate tax
    let tax = 0;
    if (taxRate !== undefined) {
        const netAmountAfterDiscount = subtotal - discount;
        tax = Math.round((netAmountAfterDiscount * taxRate * 100) / 100);
    }

    // Calculate total
    let total = Math.round((subtotal - discount + tax) * 100) / 100;

    return {
        subtotal: parseFloat(subtotal.toFixed(2)),
        discount: parseFloat(discount.toFixed(2)),
        tax: parseFloat(tax.toFixed(2)),
        total: parseFloat(total.toFixed(2))
    };
}
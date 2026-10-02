export function solve(input) {
  // Compute subtotal
  const rawSubtotal = input.items.reduce((sum, item) => sum + item.price * item.qty, 0);
  const subtotal = Math.round(rawSubtotal * 100) / 100;

  // Compute discount
  let rawDiscount = 0;
  const coupon = input.coupon;
  if (coupon && typeof coupon === 'object') {
    switch (coupon.type) {
      case 'percent':
        rawDiscount = subtotal * (coupon.value / 100);
        break;
      case 'fixed':
        rawDiscount = coupon.value;
        break;
      case 'category_percent':
        if (coupon.category) {
          const categorySubtotal = input.items
            .filter(item => item.category === coupon.category)
            .reduce((sum, item) => sum + item.price * item.qty, 0);
          rawDiscount = categorySubtotal * (coupon.value / 100);
        }
        break;
      default:
        rawDiscount = 0;
    }
  }
  // Cap discount at subtotal
  if (rawDiscount > subtotal) rawDiscount = subtotal;
  const discount = Math.round(rawDiscount * 100) / 100;

  // Compute tax
  const taxRate = typeof input.taxRate === 'number' ? input.taxRate : 0;
  const taxCalc = Math.round((subtotal - discount) * taxRate * 100) / 100;
  const tax = Math.round(taxCalc * 100) / 100;

  // Compute total
  const totalCalc = Math.round((subtotal - discount + tax) * 100) / 100;
  const total = Math.round(totalCalc * 100) / 100;

  return { subtotal, discount, tax, total };
}
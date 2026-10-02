export function solve(input) {
  const round = (x) => Math.round(x * 100) / 100;
  // Subtotal
  let subtotal = 0;
  for (const item of input.items || []) {
    subtotal += item.price * item.qty;
  }
  subtotal = round(subtotal);

  // Discount
  let discount = 0;
  const coupon = input.coupon;
  if (coupon && typeof coupon === 'object') {
    switch (coupon.type) {
      case 'percent':
        discount = subtotal * (coupon.value / 100);
        break;
      case 'fixed':
        discount = coupon.value;
        break;
      case 'category_percent':
        if (coupon.category) {
          let catTotal = 0;
          for (const item of input.items || []) {
            if (item.category === coupon.category) {
              catTotal += item.price * item.qty;
            }
          }
          discount = catTotal * (coupon.value / 100);
        }
        break;
      default:
        discount = 0;
    }
  }
  // Cap at subtotal
  if (discount > subtotal) discount = subtotal;
  discount = round(discount);

  // Tax
  let tax = 0;
  if ('taxRate' in input && typeof input.taxRate === 'number') {
    const taxable = subtotal - discount;
    tax = Math.round(taxable * input.taxRate * 100) / 100;
  }

  // Total
  const total = round(subtotal - discount + tax);

  return { subtotal, discount, tax, total };
}
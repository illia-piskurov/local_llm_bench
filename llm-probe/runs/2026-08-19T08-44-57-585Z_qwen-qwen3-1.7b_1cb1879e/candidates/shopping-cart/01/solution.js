export function solve(input) {
  const { items, coupon, taxRate } = input;

  let subtotal = 0;
  let discount = 0;

  // Calculate subtotal
  for (const item of items) {
    subtotal += item.price * item.qty;
  }

  // Apply coupon discount
  if (coupon) {
    const { type, value } = coupon;
    let discountAmount = 0;

    if (type === 'percent') {
      discountAmount = subtotal * (value / 100);
    } else if (type === 'fixed') {
      discountAmount = Math.min(value, subtotal);
    } else if (type === 'category_percent' && item.category) {
      // Apply category-based discount
      for (const item of items) {
        if (item.category === coupon.category) {
          discountAmount += item.price * item.qty;
        }
      }
    }

    discount = Math.min(discountAmount, subtotal);
  }

  // Calculate tax
  let tax = 0;
  if (taxRate !== undefined) {
    tax = Math.round((subtotal - discount) * taxRate * 100) / 100;
  }

  // Calculate total
  const total = Math.round(((subtotal - discount) + tax) * 100) / 100;

  return { subtotal, discount, tax, total };
}
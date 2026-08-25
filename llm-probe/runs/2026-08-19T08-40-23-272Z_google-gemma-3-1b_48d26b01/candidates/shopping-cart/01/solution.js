export function solve(input) {
  let subtotal = 0;
  let discount = 0;
  let tax = 0;

  if (input.coupon && input.coupon.type === 'percent') {
    const couponValue = input.coupon.value;
    if (couponValue === '20') {
      discount = 20;
    } else if (couponValue === '15') {
      discount = 15;
    } else if (couponValue === 'category_percent') {
      const category = input.items[0].category;
      if (category) {
        discount = input.items.filter(item => item.category === category).length > 0 ? 10 : 0;
      } else {
        discount = 0;
      }
    }
  }

  const taxRate = input.taxRate || 0;
  const subtotal -= discount * (input.items.length - 1) * taxRate;
  const total = subtotal + (input.items.length > 0 ? Math.round((subtotal - discount) * (taxRate * 100)) / 100 : 0) * 100;

  return {
    subtotal,
    discount,
    tax,
    total
  };
}
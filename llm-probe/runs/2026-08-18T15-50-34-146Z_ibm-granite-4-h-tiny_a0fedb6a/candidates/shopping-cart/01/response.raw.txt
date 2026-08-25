export function solve(input) {
  let subtotal = input.items.reduce((sum, item) => sum + item.price * item.qty, 0);
  let discount = 0;
  
  if (input.coupon) {
    switch (input.coupon.type) {
      case 'percent':
        discount = Math.min(subtotal * (input.coupon.value / 100), subtotal);
        break;
      case 'fixed':
        discount = Math.min(input.coupon.value, subtotal);
        break;
      case 'category_percent':
        if (input.coupon.category) {
          const categoryItems = input.items.filter(item => item.category === input.coupon.category);
          discount = Math.min(categoryItems.reduce((sum, item) => sum + item.price * item.qty, 0) * (input.coupon.value / 100), subtotal);
        }
        break;
    }
  }
  
  const taxRate = input.taxRate || 0;
  const tax = Math.round(((subtotal - discount) * taxRate) * 100) / 100;
  let total = Math.round((subtotal - discount + tax) * 100) / 100;
  
  return {
    subtotal: Number(subtotal.toFixed(2)),
    discount: Number(discount.toFixed(2)),
    tax: Number(tax.toFixed(2)),
    total: Number(total.toFixed(2))
  };
}
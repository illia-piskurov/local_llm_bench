export function solve(input) {
  let subtotal = input.items.reduce((sum, item) => sum + item.price * item.qty, 0);
  
  if (input.coupon) {
    switch (input.coupon.type) {
      case 'percent':
        let discountAmount = subtotal * input.coupon.value / 100;
        if (discountAmount > subtotal) discountAmount = subtotal;
        subtotal -= discountAmount;
        break;
      case 'fixed':
        let fixedDiscount = Math.min(subtotal, input.coupon.value);
        subtotal -= fixedDiscount;
        break;
      case 'category_percent':
        let categoryDiscount = 0;
        if (input.category && item.category === input.category) {
          categoryDiscount = subtotal * input.coupon.value / 100;
          if (categoryDiscount > subtotal) categoryDiscount = subtotal;
        }
        subtotal -= categoryDiscount;
        break;
    }
  }

  const tax = Math.round((subtotal - discount) * input.taxRate * 100) / 100;
  let total = Math.round((subtotal - discount + tax) * 100) / 100;

  return { subtotal, discount, tax, total };
}
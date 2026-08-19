export function solve(input) {
  const items = input?.items ?? []
  let subtotal = items.reduce((sum, item) => sum + Number(item.price) * Number(item.qty), 0)
  const round = x => Math.round(x * 100) / 100

  // discount
  let discount = 0
  if (input.coupon) {
    const coupon = input.coupon
    const typ = coupon.type
    if (typ === 'percent') {
      const value = Number(coupon.value)
      discount = round(subtotal * value / 100)
    } else if (typ === 'fixed') {
      discount = Math.min(15, subtotal)
    } else if (typ === 'category_percent' && coupon.category) {
      const cat = coupon.category
      let catSubtotal = 0
      for (const item of items) if (item.category === cat) catSubtotal += Number(item.price) * Number(item.qty)
      discount = round(catSubtotal * value / 100)
    }
  }

  // cap discount to subtotal
  if (discount > subtotal) discount = subtotal

  // tax
  const taxRate = input?.taxRate ?? 0
  let tax = Math.round((subtotal - discount) * taxRate * 100) / 100

  // total
  let total = Math.round((subtotal - discount + tax) * 100) / 100

  // round all values to 2 decimals
  const finalSubtotal = round(subtotal)
  const finalDiscount = round(discount)
  const finalTax = round(tax)

  return { subtotal: finalSubtotal, discount: finalDiscount, tax: finalTax, total }
}
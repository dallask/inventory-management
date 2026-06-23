import { ref } from 'vue'

const submittedOrders = ref([])
let orderCounter = 1

export function useRestockingOrders() {
  const submitOrder = (items, totalValue) => {
    const now = new Date()
    const deliveryDate = new Date(now)
    deliveryDate.setDate(deliveryDate.getDate() + 7)

    const order = {
      id: `rst-${orderCounter}`,
      order_number: `RST-${String(orderCounter).padStart(4, '0')}`,
      items,
      total_value: totalValue,
      submitted_at: now.toISOString(),
      status: 'Submitted',
      estimated_delivery_date: deliveryDate.toISOString()
    }

    submittedOrders.value.unshift(order)
    orderCounter++
    return order
  }

  return {
    submittedOrders,
    submitOrder
  }
}

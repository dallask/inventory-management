<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Budget-based restocking recommendations from demand forecast</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">Budget Control</h3>
        </div>
        <div class="budget-control">
          <div class="budget-label-row">
            <span class="budget-label">Available Budget</span>
            <span class="budget-amount">${{ budget.toLocaleString() }}</span>
          </div>
          <input
            type="range"
            class="budget-slider"
            min="1000"
            max="100000"
            step="1000"
            v-model.number="budget"
          />
          <div class="slider-range-labels">
            <span>$1K</span>
            <span>$100K</span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items</h3>
          <span class="card-subtitle">{{ recommendedItems.length }} item{{ recommendedItems.length !== 1 ? 's' : '' }} fit within budget</span>
        </div>

        <div v-if="successMessage" class="success-message">{{ successMessage }}</div>

        <div v-if="recommendedItems.length === 0" class="empty-state">
          No items fit within the current budget. Increase the budget to see recommendations.
        </div>
        <div v-else>
          <div class="table-container">
            <table class="restocking-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Item Name</th>
                  <th>Forecasted Demand</th>
                  <th>Unit Cost</th>
                  <th>Total Cost</th>
                  <th>Trend</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendedItems" :key="item.id">
                  <td><code class="sku-code">{{ item.item_sku }}</code></td>
                  <td>{{ item.item_name }}</td>
                  <td>{{ item.forecasted_demand.toLocaleString() }}</td>
                  <td>${{ item.unit_cost.toLocaleString() }}</td>
                  <td><strong>${{ (item.forecasted_demand * item.unit_cost).toLocaleString() }}</strong></td>
                  <td>
                    <span :class="['badge', item.trend.toLowerCase()]">{{ item.trend }}</span>
                  </td>
                </tr>
                <tr class="total-row">
                  <td><strong>Total</strong></td>
                  <td></td>
                  <td></td>
                  <td></td>
                  <td><strong>${{ totalCost.toLocaleString() }}</strong></td>
                  <td></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="order-action">
          <button
            class="place-order-btn"
            :disabled="recommendedItems.length === 0"
            @click="placeOrder"
          >
            Place Order
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useRestockingOrders } from '../composables/useRestockingOrders'

export default {
  name: 'Restocking',
  setup() {
    const { submitOrder } = useRestockingOrders()

    const budget = ref(25000)
    const forecasts = ref([])
    const loading = ref(true)
    const error = ref(null)
    const successMessage = ref(null)

    const sortedByDemand = computed(() => {
      return [...forecasts.value].sort((a, b) => b.forecasted_demand - a.forecasted_demand)
    })

    const recommendedItems = computed(() => {
      let remaining = budget.value
      const result = []
      for (const item of sortedByDemand.value) {
        const itemCost = item.forecasted_demand * item.unit_cost
        if (itemCost <= remaining) {
          result.push(item)
          remaining -= itemCost
        }
      }
      return result
    })

    const totalCost = computed(() => {
      return recommendedItems.value.reduce((sum, item) => sum + item.forecasted_demand * item.unit_cost, 0)
    })

    const loadForecasts = async () => {
      loading.value = true
      error.value = null
      try {
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = () => {
      if (recommendedItems.value.length === 0) return

      const items = recommendedItems.value.map(item => ({
        sku: item.item_sku,
        name: item.item_name,
        quantity: item.forecasted_demand,
        unit_price: item.unit_cost
      }))

      const order = submitOrder(items, totalCost.value)

      successMessage.value = `Order ${order.order_number} submitted successfully! Estimated delivery in 7 days.`
      setTimeout(() => {
        successMessage.value = null
      }, 4000)
    }

    onMounted(loadForecasts)

    return {
      budget,
      forecasts,
      loading,
      error,
      successMessage,
      recommendedItems,
      totalCost,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

.budget-card {
  margin-bottom: 1.25rem;
}

.budget-control {
  padding: 0.5rem 0;
}

.budget-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.budget-label {
  font-size: 0.938rem;
  font-weight: 600;
  color: var(--dk-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.budget-amount {
  font-size: 2rem;
  font-weight: 700;
  color: var(--dk-primary);
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  height: 16px;
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  outline: none;
  cursor: pointer;
  display: block;
}

.budget-slider::-webkit-slider-runnable-track {
  height: 4px;
  border-radius: 0;
  background: var(--dk-surface-3);
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--dk-primary);
  cursor: pointer;
  border: 2px solid var(--dk-surface-1);
  margin-top: -6px;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  background: var(--dk-primary-hover);
  box-shadow: 0 0 0 3px var(--dk-primary-subtle);
}

.budget-slider::-moz-range-track {
  height: 4px;
  background: var(--dk-surface-3);
  border: none;
}

.budget-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--dk-primary);
  cursor: pointer;
  border: 2px solid var(--dk-surface-1);
}

.slider-range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: var(--dk-text-muted);
  font-weight: 500;
}

.card-subtitle {
  font-size: 0.875rem;
  color: var(--dk-text-secondary);
  font-weight: 500;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: var(--dk-text-secondary);
  font-size: 0.938rem;
}

.restocking-table {
  width: 100%;
}

.sku-code {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.813rem;
  background: var(--dk-surface-2);
  padding: 0.188rem 0.5rem;
  border-radius: 0;
  color: var(--dk-text-heading);
}

.total-row {
  background: var(--dk-surface-2);
  border-top: 2px solid var(--dk-border);
}

.total-row td {
  font-weight: 600;
  color: var(--dk-text-heading);
  border-top: 2px solid var(--dk-border);
}

.order-action {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--dk-border);
}

.place-order-btn {
  background: var(--dk-primary);
  color: var(--dk-text-on-accent);
  padding: var(--dk-padding-md);
  border-radius: 0;
  font-weight: var(--dk-weight-semibold);
  font-size: var(--dk-text-sm);
  border: none;
  cursor: pointer;
  transition: background 0.15s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: var(--dk-primary-hover);
}

.place-order-btn:disabled {
  background: var(--dk-text-muted);
  cursor: not-allowed;
}

.success-message {
  background: var(--dk-success-subtle);
  border: 1px solid var(--dk-success);
  color: var(--dk-success-text);
  padding: 0.875rem 1rem;
  border-radius: 0;
  margin-bottom: 1rem;
  font-size: 0.938rem;
  font-weight: 500;
}
</style>

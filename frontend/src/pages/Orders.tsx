import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/axios'
import ConfirmDialog from '../components/ConfirmDialog'
import type { Order, PaginatedResponse } from '../types'

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-blue-100 text-blue-800',
  shipped: 'bg-purple-100 text-purple-800',
  delivered: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

export default function Orders() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [cancelId, setCancelId] = useState<number | null>(null)
  const [cancelling, setCancelling] = useState(false)

  const fetchOrders = useCallback(() => {
    setLoading(true)
    api.get<PaginatedResponse<Order>>('/orders/')
      .then(({ data }) => setOrders(data.results ?? data as unknown as Order[]))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { fetchOrders() }, [fetchOrders])

  const handleCancel = async () => {
    if (cancelId === null) return
    setCancelling(true)
    try {
      await api.post(`/orders/${cancelId}/cancel/`)
      setCancelId(null)
      fetchOrders()
    } catch (err) { console.error('Cancel error:', err) }
    finally { setCancelling(false) }
  }

  if (loading) return <div className="text-center text-gray-500 py-20 text-lg">Loading orders...</div>

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">My Orders</h1>

      {orders.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-500 dark:text-gray-400 text-lg mb-4">No orders yet</p>
          <Link to="/" className="text-blue-600 hover:underline">Browse products</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div key={order.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <span className="text-sm text-gray-500 dark:text-gray-400">{new Date(order.created_at).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-medium px-3 py-1 rounded-full ${statusColors[order.status] || 'bg-gray-100 text-gray-700'}`}>
                    {order.status}
                  </span>
                  <span className="font-bold text-blue-600">${order.total_price}</span>
                </div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 truncate">{order.shipping_address}</p>
              <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                {order.items?.length || 0} item(s)
              </div>
              <div className="mt-3 flex gap-2">
                {order.status === 'pending' && (
                  <>
                    <button onClick={() => navigate(`/orders/${order.id}/payment`)}
                      className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 transition">
                      Choose Payment
                    </button>
                    <button onClick={() => setCancelId(order.id)}
                      className="text-xs bg-red-500 text-white px-3 py-1.5 rounded-lg hover:bg-red-600 transition">
                      Cancel
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={cancelId !== null}
        title="Cancel Order"
        message="Are you sure you want to cancel this order? This action cannot be undone."
        confirmLabel="Cancel Order"
        onConfirm={handleCancel}
        onCancel={() => setCancelId(null)}
        loading={cancelling}
      />
    </div>
  )
}

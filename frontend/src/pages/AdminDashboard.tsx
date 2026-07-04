import { useState, useEffect, useCallback } from 'react'
import api from '../api/axios'
import ConfirmDialog from '../components/ConfirmDialog'
import AdminProducts from './AdminProducts'
import type { DashboardOverview, BestSeller, AdminOrder, PaginatedResponse } from '../types'

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-blue-100 text-blue-800',
  shipped: 'bg-purple-100 text-purple-800',
  delivered: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

const PAGE_SIZE = 20

type MainTab = 'overview' | 'orders' | 'products'

export default function AdminDashboard() {
  const [mainTab, setMainTab] = useState<MainTab>('overview')
  const [overview, setOverview] = useState<DashboardOverview | null>(null)
  const [bestSellers, setBestSellers] = useState<BestSeller[]>([])
  const [orders, setOrders] = useState<AdminOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<number | null>(null)
  const [orderTab, setOrderTab] = useState<'active' | 'archived'>('active')
  const [page, setPage] = useState(1)
  const [totalOrders, setTotalOrders] = useState(0)
  const [archiveTarget, setArchiveTarget] = useState<number | null>(null)
  const [archiving, setArchiving] = useState(false)

  const totalPages = Math.ceil(totalOrders / PAGE_SIZE)

  const loadDashboard = useCallback(() => {
    const archivedParam = orderTab === 'archived' ? '?archived=true' : ''
    Promise.all([
      api.get<DashboardOverview>('/dashboard/overview/'),
      api.get<PaginatedResponse<BestSeller>>('/dashboard/best-sellers/'),
      api.get<PaginatedResponse<AdminOrder>>(`/orders/admin-orders/${archivedParam}${archivedParam ? '&' : '?'}page=${page}`),
    ])
      .then(([ov, bs, ord]) => {
        setOverview(ov.data)
        setBestSellers(bs.data.results ?? bs.data as unknown as BestSeller[])
        const d = ord.data as PaginatedResponse<AdminOrder>
        setOrders(d.results ?? [])
        setTotalOrders(d.count ?? 0)
      })
      .catch((err) => { console.error('Dashboard load error:', err) })
      .finally(() => setLoading(false))
  }, [orderTab, page])

  useEffect(() => { loadDashboard() }, [loadDashboard])

  const tabButton = (tab: MainTab, label: string) => (
    <button onClick={() => { setMainTab(tab); setPage(1) }}
      className={`px-4 py-1.5 text-sm rounded-md transition ${mainTab === tab ? 'bg-white dark:bg-gray-600 shadow-sm font-medium text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}`}>
      {label}
    </button>
  )

  const handleUpdate = async (orderId: number, data: Partial<AdminOrder>) => {
    setUpdating(orderId)
    try {
      await api.patch(`/orders/admin-orders/${orderId}/`, data)
      loadDashboard()
    } catch (err) { console.error('Update error:', err) }
    finally { setUpdating(null) }
  }

  const handleArchive = async () => {
    if (archiveTarget === null) return
    setArchiving(true)
    try {
      await api.patch(`/orders/admin-orders/${archiveTarget}/`, { is_archived: true })
      setArchiveTarget(null)
      loadDashboard()
    } catch (err) { console.error('Archive error:', err) }
    finally { setArchiving(false) }
  }

  if (mainTab !== 'overview' && mainTab !== 'orders') {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Dashboard</h1>
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1 w-fit mb-8">
          {tabButton('overview', 'Overview')}
          {tabButton('orders', 'Orders')}
          {tabButton('products', 'Products')}
        </div>
        <AdminProducts />
      </div>
    )
  }

  if (loading) return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Dashboard</h1>
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1 w-fit mb-8">
        {tabButton('overview', 'Overview')}
        {tabButton('orders', 'Orders')}
        {tabButton('products', 'Products')}
      </div>
      <div className="text-center text-gray-500 py-20 text-lg">Loading dashboard...</div>
    </div>
  )

  if (!overview) return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Dashboard</h1>
      <div className="text-center text-red-500 py-20">Failed to load dashboard data.</div>
    </div>
  )

  const lowStock = overview.low_stock_products || []

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Dashboard</h1>
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1 w-fit mb-8">
        {tabButton('overview', 'Overview')}
        {tabButton('orders', 'Orders')}
        {tabButton('products', 'Products')}
      </div>

      {mainTab === 'overview' && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
            <StatCard label="Total Orders" value={overview.total_orders} color="bg-blue-500" />
            <StatCard label="Total Revenue" value={`$${overview.total_revenue}`} color="bg-green-500" />
            <StatCard label="Revenue This Month" value={`$${overview.revenue_this_month}`} color="bg-blue-500" />
            <StatCard label="Total Products" value={overview.total_products} color="bg-purple-500" />
            <StatCard label="Total Users" value={overview.total_users} color="bg-orange-500" />
            <StatCard label="New Users (Month)" value={overview.new_users_this_month} color="bg-teal-500" />
            <StatCard label="Avg Order Value" value={`$${overview.average_order_value}`} color="bg-pink-500" />
            <StatCard label="Low Stock Items" value={lowStock.length} color="bg-red-500" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Orders by Status</h2>
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm">
                {Object.entries(overview.orders_by_status || {}).length === 0 ? (
                  <p className="text-gray-500 dark:text-gray-400 text-sm">No orders yet.</p>
                ) : (
                  <div className="space-y-3">
                    {Object.entries(overview.orders_by_status).map(([status, count]) => (
                      <div key={status} className="flex items-center justify-between">
                        <span className="text-sm capitalize text-gray-700 dark:text-gray-300">{status}</span>
                        <div className="flex items-center gap-3">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div className="bg-blue-500 h-2 rounded-full"
                              style={{ width: `${overview.total_orders > 0 ? (count / overview.total_orders) * 100 : 0}%` }} />
                          </div>
                          <span className="text-sm font-semibold text-gray-900 w-8 text-right">{count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Best Sellers</h2>
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm overflow-hidden">
                {bestSellers.length === 0 ? (
                  <div className="p-5 text-gray-500 dark:text-gray-400 text-sm">No sales yet.</div>
                ) : (
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 dark:bg-gray-700 text-left">
                      <tr>
                        <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Product</th>
                        <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300 text-right">Sold</th>
                        <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300 text-right">Revenue</th>
                      </tr>
                    </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {bestSellers.slice(0, 10).map((item) => (
                        <tr key={item.product_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                          <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{item.name || `Product #${item.product_id}`}</td>
                          <td className="px-4 py-3 text-right">{item.total_quantity_sold}</td>
                          <td className="px-4 py-3 text-right text-blue-600 font-medium">${item.total_revenue}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>

          {lowStock.length > 0 && (
            <div className="mb-10">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Low Stock Alerts</h2>
              <div className="bg-white dark:bg-gray-800 border border-red-200 dark:border-red-800 rounded-xl shadow-sm overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-red-50 dark:bg-red-900/30 text-left">
                    <tr>
                      <th className="px-4 py-3 font-medium text-red-700">Product</th>
                      <th className="px-4 py-3 font-medium text-red-700 text-right">Stock</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {lowStock.map((p) => (
                      <tr key={p.id} className="hover:bg-red-50">
                        <td className="px-4 py-3 font-medium text-gray-900">{p.name || `#${p.id}`}</td>
                        <td className="px-4 py-3 text-right text-red-600 font-medium">{p.stock}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {mainTab === 'orders' && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">All Orders</h2>
            <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button onClick={() => { setOrderTab('active'); setPage(1) }}
                className={`px-4 py-1.5 text-sm rounded-md transition ${orderTab === 'active' ? 'bg-white dark:bg-gray-600 shadow-sm font-medium text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}`}>
                Active
              </button>
              <button onClick={() => { setOrderTab('archived'); setPage(1) }}
                className={`px-4 py-1.5 text-sm rounded-md transition ${orderTab === 'archived' ? 'bg-white dark:bg-gray-600 shadow-sm font-medium text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'}`}>
                Archived
              </button>
            </div>
          </div>

          {orders.length === 0 ? (
            <div className="p-10 text-center text-gray-500 dark:text-gray-400">No orders found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700 text-left">
                    <tr>
                      <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300">#</th>
                      <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Customer</th>
                      <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300 text-right">Total</th>
                      <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Status</th>
                      <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Payment</th>
                      <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Date</th>
                      <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {orders.map((order) => (
                    <tr key={order.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{new Date(order.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900 dark:text-white">{order.full_name || order.username || `User #${order.user}`}</div>
                        {order.email && <div className="text-xs text-gray-500 dark:text-gray-400">{order.email}</div>}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-blue-600">${order.total_price}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${statusColors[order.status] || 'bg-gray-100 text-gray-700'}`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{order.payment_method || '-'}</td>
                      <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{new Date(order.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1.5">
                          {order.status === 'pending' && (
                            <button onClick={() => handleUpdate(order.id, { status: 'confirmed' })}
                              disabled={updating === order.id}
                              className="text-xs bg-blue-500 text-white px-2.5 py-1.5 rounded-md hover:bg-blue-600 transition disabled:opacity-50">
                              Confirm
                            </button>
                          )}
                          {order.status === 'confirmed' && (
                            <button onClick={() => handleUpdate(order.id, { status: 'shipped' })}
                              disabled={updating === order.id}
                              className="text-xs bg-purple-500 text-white px-2.5 py-1.5 rounded-md hover:bg-purple-600 transition disabled:opacity-50">
                              Ship
                            </button>
                          )}
                          {order.status === 'shipped' && (
                            <button onClick={() => handleUpdate(order.id, { status: 'delivered' })}
                              disabled={updating === order.id}
                              className="text-xs bg-green-500 text-white px-2.5 py-1.5 rounded-md hover:bg-green-600 transition disabled:opacity-50">
                              Deliver
                            </button>
                          )}
                          {(order.status === 'delivered' || order.status === 'cancelled') && !order.is_archived && (
                            <button onClick={() => setArchiveTarget(order.id)}
                              disabled={updating === order.id}
                              className="text-xs bg-gray-500 text-white px-2.5 py-1.5 rounded-md hover:bg-gray-600 transition disabled:opacity-50">
                              Archive
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-5 py-3 border-t border-gray-200 dark:border-gray-700">
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Page {page} of {totalPages} ({totalOrders} orders)
              </span>
              <div className="flex gap-1">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}
                  className="px-3 py-1 text-sm rounded-md bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-40 transition">Previous</button>
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 2)
                  .map((p, idx, arr) => (
                    <span key={p} className="flex">
                      {idx > 0 && arr[idx - 1] !== p - 1 && <span className="px-1 self-end text-gray-400">...</span>}
                      <button onClick={() => setPage(p)}
                        className={`px-3 py-1 text-sm rounded-md transition ${p === page ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}`}>{p}</button>
                    </span>
                  ))}
                <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
                  className="px-3 py-1 text-sm rounded-md bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-40 transition">Next</button>
              </div>
            </div>
          )}
        </div>
      )}

      <ConfirmDialog
        open={archiveTarget !== null}
        title="Archive Order"
        message="Are you sure you want to archive this order? It will be hidden from the active orders list."
        confirmLabel="Archive"
        onConfirm={handleArchive}
        onCancel={() => setArchiveTarget(null)}
        loading={archiving}
      />
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm">
      <div className={`w-3 h-3 rounded-full ${color} mb-3`} />
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{label}</p>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import api from '../api/axios'
import type { Order, CodPaymentData } from '../types'

export default function PaymentSelection() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [step, setStep] = useState<'select' | 'form'>('select')
  const [updating, setUpdating] = useState(false)
  const [msg, setMsg] = useState('')
  const [form, setForm] = useState({ full_name: '', phone: '' })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    api.get<Order>(`/orders/${id}/`)
      .then(({ data }) => {
        setOrder(data)
        setForm((prev) => ({ ...prev, phone: data.phone || '' }))
      })
      .catch((err) => { console.error('Order load error:', err); navigate('/orders') })
      .finally(() => setLoading(false))
  }, [id, navigate])

  const handleSelect = (method: string) => {
    if (method === 'CARD') return
    setStep('form')
  }

  const validate = () => {
    const errs: Record<string, string> = {}
    const words = form.full_name.trim().split(/\s+/)
    if (words.length < 3) errs.full_name = 'Full name must contain at least three words'
    const cleanPhone = form.phone.replace(/\s+/g, '')
    if (!/^\d{7,}$/.test(cleanPhone)) errs.phone = 'Phone must be at least 7 digits'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setUpdating(true)
    try {
      await api.patch<Order>(`/orders/${id}/`, { payment_method: 'COD', full_name: form.full_name.trim(), phone: form.phone } as CodPaymentData)
      setMsg('Payment method set to COD. Order confirmed!')
      setTimeout(() => navigate('/orders'), 1500)
    } catch {
      setMsg('Failed to update payment method.')
    } finally {
      setUpdating(false)
    }
  }

  if (loading) return <div className="text-center text-gray-500 py-20 text-lg">Loading order...</div>
  if (!order) return null

  return (
    <div className="max-w-lg mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Choose Payment</h1>
      <p className="text-gray-500 dark:text-gray-400 mb-6">{new Date(order.created_at).toLocaleDateString()}</p>

      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 shadow-sm mb-6">
        <div className="flex justify-between mb-3">
          <span className="text-sm text-gray-500 dark:text-gray-400">Status</span>
          <span className="text-sm font-medium capitalize">{order.status}</span>
        </div>
        <div className="flex justify-between mb-3">
          <span className="text-sm text-gray-500 dark:text-gray-400">Total</span>
          <span className="text-lg font-bold text-blue-600">${order.total_price}</span>
        </div>
        <div className="flex justify-between mb-3">
          <span className="text-sm text-gray-500 dark:text-gray-400">Shipping</span>
          <span className="text-sm text-gray-700 dark:text-gray-300">{order.shipping_address}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500 dark:text-gray-400">Payment</span>
          <span className="text-sm text-gray-700 dark:text-gray-300">{order.payment_method || 'Not set'}</span>
        </div>
      </div>

      {msg && (
        <div className="bg-green-50 border border-green-200 text-green-800 text-sm rounded-lg p-4 mb-6">
          {msg}
        </div>
      )}

      {step === 'select' && (
        <div className="space-y-3">
          <button onClick={() => handleSelect('COD')}
            className="w-full flex items-center justify-between bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-xl p-5 hover:border-blue-400 hover:shadow-sm transition">
            <div className="flex items-center gap-3">
              <span className="text-2xl">💵</span>
              <div className="text-left">
                <p className="font-semibold text-gray-900 dark:text-white">Cash on Delivery</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">Pay when you receive</p>
              </div>
            </div>
            <span className="text-blue-600 text-sm font-medium">Select</span>
          </button>

          <div className="flex items-center justify-between bg-gray-100 border border-gray-200 rounded-xl p-5 opacity-60 cursor-not-allowed">
            <div className="flex items-center gap-3">
              <span className="text-2xl">💳</span>
              <div className="text-left">
                <p className="font-semibold text-gray-900 dark:text-white">Card Payment</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">Coming soon</p>
              </div>
            </div>
            <span className="text-gray-400 text-xs bg-gray-200 px-2 py-1 rounded">Soon</span>
          </div>

          <Link to="/orders" className="text-blue-600 hover:underline text-sm inline-block mt-6">&larr; Back to Orders</Link>
        </div>
      )}

      {step === 'form' && (
        <form onSubmit={handleConfirm} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Name</label>
            <input type="text" value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              placeholder="e.g. Ahmed Mohamed Ali"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400" />
            {errors.full_name && <p className="text-red-600 text-xs mt-1">{errors.full_name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone Number</label>
            <input type="text" value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              placeholder="+9639xxxxxxxx"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400" />
            {errors.phone && <p className="text-red-600 text-xs mt-1">{errors.phone}</p>}
          </div>

          {errors.general && <p className="text-red-600 text-sm">{errors.general}</p>}

          <button type="submit" disabled={updating}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50">
            {updating ? 'Confirming...' : 'Confirm Order'}
          </button>

            <button type="button" onClick={() => setStep('select')}
              className="w-full text-gray-500 dark:text-gray-400 py-2 text-sm hover:text-gray-700 dark:hover:text-gray-200 transition">
            &larr; Back to payment options
          </button>
        </form>
      )}
    </div>
  )
}

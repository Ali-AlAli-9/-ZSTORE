import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../api/axios'
import type { Order, CheckoutData, ApiError } from '../types'

export default function Checkout() {
  const { user, resendVerification, refreshUser } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<CheckoutData>({ shipping_address: '', phone: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [resent, setResent] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const { data } = await api.post<Order>('/orders/checkout/', form)
      navigate(`/orders/${data.id}/payment`)
    } catch (err: unknown) {
      const responseData = (err as { response?: { data?: ApiError | Record<string, string[]> } }).response?.data
      if (!responseData) {
        setError('Checkout failed. Please try again.')
      } else if ('detail' in responseData && typeof responseData.detail === 'string' && responseData.detail.toLowerCase().includes('verify your email')) {
        setError(responseData.detail)
      } else {
        const msgs = Object.values(responseData).flat().join('. ')
        setError(msgs || 'Checkout failed')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleResend = async () => {
    try {
      await resendVerification()
      setResent(true)
      setTimeout(() => refreshUser(), 2000)
    } catch { /* ignore */ }
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Checkout</h1>
      <p className="text-gray-500 dark:text-gray-400 mb-6">Enter your shipping details</p>

      {!user?.is_email_verified && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-yellow-600 mt-0.5 shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="text-sm text-yellow-800">
              <p className="font-medium mb-1">Please verify your email before checkout</p>
              <p className="mb-2">Check your inbox and click the verification link.</p>
              <button onClick={handleResend}
                className="text-yellow-900 underline hover:no-underline font-medium">
                {resent ? 'Verification sent!' : 'Resend verification email'}
              </button>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Shipping Address</label>
          <input type="text" required value={form.shipping_address}
            onChange={(e) => setForm({ ...form, shipping_address: e.target.value })}
            placeholder="123 Main St, City"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400" />
        </div>
        <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone</label>
          <input type="text" required value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            placeholder="+9639xxxxxxxx"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400" />
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <button type="submit" disabled={submitting}
          className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50">
          {submitting ? 'Placing order...' : 'Place Order'}
        </button>
      </form>

      <Link to="/cart" className="text-blue-600 hover:underline text-sm inline-block mt-4">&larr; Back to Cart</Link>
    </div>
  )
}

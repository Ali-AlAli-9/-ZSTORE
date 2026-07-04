import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/axios'
import type { Product, PaginatedResponse, CartResponse } from '../types'

let productsCache: Product[] | null = null
let productsCachePromise: Promise<Product[]> | null = null

async function getAllProducts(): Promise<Product[]> {
  if (productsCache) return productsCache
  if (productsCachePromise) return productsCachePromise

  productsCachePromise = (async () => {
    let page = 1
    const all: Product[] = []
    while (true) {
      const { data } = await api.get<PaginatedResponse<Product>>(`/products/?page=${page}`)
      all.push(...data.results)
      if (!data.next) break
      page++
    }
    productsCache = all
    return all
  })()

  return productsCachePromise
}

export default function Cart() {
  const [cart, setCart] = useState<CartResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const productMap = useRef<Record<string, Product>>({})

  const fetchAll = async () => {
    const [cartRes, allProds] = await Promise.all([
      api.get<CartResponse>('/cart/'),
      getAllProducts(),
    ])
    setCart(Array.isArray(cartRes.data) ? { cart_id: 0, items: cartRes.data as unknown as CartResponse['items'] } : cartRes.data)
    const map: Record<string, Product> = {}
    allProds.forEach((p) => { map[p.name] = p })
    productMap.current = map
  }

  useEffect(() => {
    fetchAll().catch((err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
      setError(detail || 'Failed to load cart')
    }).finally(() => setLoading(false))
  }, [])

  const updateCart = async (productName: string, quantity: number) => {
    const product = productMap.current[productName]
    if (!product) return
    try {
      await api.post('/cart/', { product: product.id, quantity })
      const { data } = await api.get<CartResponse>('/cart/')
      setCart(Array.isArray(data) ? { cart_id: 0, items: data as unknown as CartResponse['items'] } : data)
      setError('')
    } catch (err: unknown) {
      const errorData = (err as { response?: { data?: { error?: string; non_field_errors?: string[] } } }).response?.data
      setError(errorData?.error || errorData?.non_field_errors?.[0] || 'Failed to update cart')
    }
  }

  if (loading) return <div className="text-center text-gray-500 py-20 text-lg">Loading cart...</div>
  if (error) return <div className="text-center text-red-500 py-20">{error}</div>

  const items = cart?.items || []

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">Shopping Cart</h1>

      {items.length === 0 ? (
        <div className="text-center py-16">
                <p className="text-gray-500 dark:text-gray-400 text-lg mb-4">Your cart is empty</p>
          <Link to="/" className="text-blue-600 hover:underline">Browse products</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item, idx) => {
            const p = productMap.current[item.product]
            if (!p) {
              return (
                <div key={idx} className="flex items-center justify-between bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm opacity-60">
                  <div className="flex-1">
                    <p className="font-semibold text-gray-400 dark:text-gray-500">{item.product} [Deleted]</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="w-8 text-center font-medium dark:text-white">{item.quantity}</span>
                    <button
                      onClick={() => updateCart(item.product, 0)}
                      className="text-red-500 hover:text-red-700 text-sm font-medium"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )
            }
            const price = parseFloat(p.price)
            return (
              <div key={idx} className="flex items-center justify-between bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm">
                <div className="flex-1">
                  <p className="font-semibold text-gray-900 dark:text-white">{item.product}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">${price.toFixed(2)} each</p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => updateCart(item.product, Math.max(0, item.quantity - 1))}
                    className="w-8 h-8 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 text-lg font-bold dark:text-white transition"
                  >-</button>
                  <span className="w-8 text-center font-medium dark:text-white">{item.quantity}</span>
                  <button
                    onClick={() => updateCart(item.product, item.quantity + 1)}
                    className="w-8 h-8 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 text-lg font-bold dark:text-white transition"
                  >+</button>
                  <span className="w-16 text-right font-bold text-blue-600">
                    ${(price * item.quantity).toFixed(2)}
                  </span>
                  <button
                    onClick={() => updateCart(item.product, 0)}
                    className="text-red-500 hover:text-red-700 ml-2 text-sm font-medium"
                  >
                    Remove
                  </button>
                </div>
              </div>
            )
          })}

          <div className="text-right mt-6">
            <Link
              to="/checkout"
              className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition font-medium inline-block"
            >
              Proceed to Checkout
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

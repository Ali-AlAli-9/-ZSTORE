import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'
import type { Product } from '../types'

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [product, setProduct] = useState<Product | null>(null)
  const [quantity, setQuantity] = useState(1)
  const [msg, setMsg] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<Product>(`/products/${id}/`)
      .then(({ data }) => setProduct(data))
      .finally(() => setLoading(false))
  }, [id])

  const addToCart = async () => {
    if (!user) { navigate('/login'); return }
    if (!product) return
    try {
      await api.post('/cart/', { product: product.id, quantity })
      setMsg('Added to cart!')
      setTimeout(() => setMsg(''), 2000)
    } catch (err: unknown) {
      const errorData = (err as { response?: { data?: { error?: string; non_field_errors?: string[] } } }).response?.data
      setMsg(errorData?.error || errorData?.non_field_errors?.[0] || 'Failed to add')
    }
  }

  if (loading) return <div className="text-center text-gray-500 py-20 text-lg">Loading...</div>
  if (!product) return <div className="text-center text-gray-500 py-20">Product not found</div>

  const imgUrl = product.image || null

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      <button onClick={() => navigate(-1)} className="text-blue-600 hover:underline mb-6 inline-block">&larr; Back</button>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
        {imgUrl ? (
          <img src={imgUrl} alt={product.name} className="w-full rounded-xl shadow-md object-cover max-h-96" />
        ) : (
          <div className="w-full h-80 bg-gray-100 dark:bg-gray-700 rounded-xl flex items-center justify-center text-gray-400">No Image</div>
        )}

        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{product.name}</h1>
          <p className="text-2xl font-bold text-blue-600 mt-3">${product.price}</p>
          {product.stock !== undefined && (
            <p className={`mt-2 text-sm font-medium ${product.stock > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
            </p>
          )}
          <p className="text-gray-600 dark:text-gray-400 mt-4 leading-relaxed">{product.description}</p>

          <div className="mt-6 flex items-center gap-4">
            <input
              type="number"
              min={1}
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
              className="w-20 px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg text-center"
            />
            <button
              onClick={addToCart}
              className="bg-blue-600 text-white px-6 py-2.5 rounded-lg hover:bg-blue-700 transition font-medium"
            >
              Add to Cart
            </button>
          </div>

          {msg && (
            <p className={`mt-4 text-sm font-medium ${msg === 'Added to cart!' ? 'text-green-600' : 'text-red-600'}`}>
              {msg}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

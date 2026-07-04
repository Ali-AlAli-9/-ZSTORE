import { useState, useEffect } from 'react'
import api from '../api/axios'
import ProductCard from '../components/ProductCard'
import type { Product, PaginatedResponse } from '../types'

export default function Home() {
  const [products, setProducts] = useState<Product[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<PaginatedResponse<Product>>('/products/')
      .then(({ data }) => setProducts(data.results ?? data as unknown as Product[]))
      .finally(() => setLoading(false))
  }, [])

  const filtered = products.filter((p) =>
    !search || p.name.toLowerCase().includes(search.toLowerCase()) || p.description?.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) return <div className="text-center text-gray-500 py-20 text-lg">Loading products...</div>

  return (
    <>
      <section className="relative min-h-[520px] flex items-center justify-center overflow-hidden bg-gradient-to-b from-blue-600 to-blue-800 dark:from-blue-800 dark:to-blue-950">
        <div className="absolute inset-0">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent" />
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl" />
          <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-indigo-400/20 rounded-full blur-3xl" />
        </div>
        <div className="relative z-10 w-full max-w-6xl mx-auto px-4 grid md:grid-cols-2 gap-12 items-center py-16">
          <div>
            <div className="inline-flex items-center gap-2 bg-white/10 border border-white/10 rounded-full px-4 py-1 text-white/80 text-sm mb-6">
              <span className="w-1.5 h-1.5 bg-green-400 rounded-full" />
              New Arrivals 2026
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 leading-tight">
              Premium Electronics
            </h1>
            <p className="text-base md:text-lg text-blue-100/80 mb-8 leading-relaxed max-w-lg">
              Discover cutting-edge gadgets and accessories at unbeatable prices. Quality you can trust.
            </p>
            <a
              href="#products"
              className="inline-flex items-center gap-2 bg-white text-blue-700 px-7 py-3 rounded-lg font-semibold hover:bg-blue-50 transition shadow-lg w-fit"
            >
              Shop Now
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
            </a>
            <div className="mt-10 flex items-center gap-8 text-white/60 text-sm">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                Free Delivery
              </div>
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                Secure Payment
              </div>
            </div>
          </div>
          <div className="hidden md:flex items-center justify-center">
            <div className="relative w-80 h-80">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-400/30 to-indigo-500/30 rounded-3xl rotate-6" />
              <div className="absolute inset-0 bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl -rotate-3 flex items-center justify-center">
                <div className="text-center p-8">
                  <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-2xl flex items-center justify-center">
                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" /></svg>
                  </div>
                  <p className="text-white/90 font-semibold text-lg">Fast & Reliable</p>
                  <p className="text-white/50 text-sm mt-1">Free shipping over $50</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div id="products" className="max-w-6xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">Products</h2>
            <p className="text-gray-500 dark:text-gray-400 mt-1">Browse our collection</p>
          </div>
          <input
            type="text"
            placeholder="Search products..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full max-w-xs px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {filtered.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>

          {filtered.length === 0 && (
            <p className="text-gray-400 text-center py-10">No products found.</p>
          )}
        </div>
    </>
  )
}

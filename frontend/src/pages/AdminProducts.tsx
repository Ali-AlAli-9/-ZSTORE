import { useState, useEffect, useCallback } from 'react'
import api from '../api/axios'
import ConfirmDialog from '../components/ConfirmDialog'
import type { Product, PaginatedResponse } from '../types'

interface FormState {
  name: string
  description: string
  price: string
  stock: string
  image: File | null
}

const emptyForm: FormState = { name: '', description: '', price: '', stock: '', image: null }

export default function AdminProducts() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [form, setForm] = useState<FormState>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)
  const [formError, setFormError] = useState('')

  const totalPages = Math.ceil(totalCount / 20)

  const fetchProducts = useCallback(() => {
    setLoading(true)
    const searchParam = search ? `&search=${encodeURIComponent(search)}` : ''
    api.get<PaginatedResponse<Product>>(`/products/?page=${page}${searchParam}`)
      .then(({ data }) => {
        setProducts(data.results ?? [])
        setTotalCount(data.count ?? 0)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [page, search])

  useEffect(() => { fetchProducts() }, [fetchProducts])

  const openAdd = () => {
    setEditId(null)
    setForm(emptyForm)
    setPreview(null)
    setFormError('')
    setShowForm(true)
  }

  const openEdit = async (id: number) => {
    setEditId(id)
    setFormError('')
    try {
      const { data } = await api.get<Product>(`/products/${id}/`)
      setForm({ name: data.name, description: data.description, price: data.price, stock: String(data.stock ?? 0), image: null })
      setPreview(data.image ? `${data.image}` : null)
      setShowForm(true)
    } catch { setFormError('Failed to load product') }
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null
    setForm((prev) => ({ ...prev, image: file }))
    if (file) {
      const reader = new FileReader()
      reader.onload = () => setPreview(reader.result as string)
      reader.readAsDataURL(file)
    } else {
      setPreview(null)
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim() || !form.price || !form.stock) {
      setFormError('Name, price, and stock are required')
      return
    }
    setSaving(true)
    setFormError('')
    try {
      const fd = new FormData()
      fd.append('name', form.name.trim())
      fd.append('description', form.description.trim())
      fd.append('price', form.price)
      fd.append('stock', form.stock)
      if (form.image) fd.append('image', form.image)

      if (editId) {
        await api.patch(`/products/${editId}/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      } else {
        await api.post('/products/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      }
      setShowForm(false)
      fetchProducts()
    } catch (err: unknown) {
      const data = (err as { response?: { data?: Record<string, string | string[]> } }).response?.data
      const msgs = data ? Object.values(data).flat().join('. ') : 'Failed to save product'
      setFormError(msgs)
    } finally { setSaving(false) }
  }

  const handleDelete = async () => {
    if (deleteTarget === null) return
    setDeleting(true)
    try {
      await api.delete(`/products/${deleteTarget}/`)
      setDeleteTarget(null)
      fetchProducts()
    } catch (err) { console.error('Delete error:', err) }
    finally { setDeleting(false) }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Products</h2>
          <input
            type="text" placeholder="Search products..." value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="max-w-xs px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
        <button onClick={openAdd}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm font-medium">
          + Add Product
        </button>
      </div>

      {loading ? (
        <div className="text-center text-gray-500 py-10">Loading products...</div>
      ) : products.length === 0 ? (
        <div className="text-center text-gray-500 dark:text-gray-400 py-10">No products found.</div>
      ) : (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700 text-left">
                <tr>
                  <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300 w-16">Image</th>
                  <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Name</th>
                  <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300 text-right">Price</th>
                  <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300 text-right">Stock</th>
                  <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-300 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {products.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">
                      {p.image ? (
                        <img src={p.image} alt={p.name} className="w-12 h-12 object-cover rounded-lg" />
                      ) : (
                        <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center text-gray-400 text-xs">N/A</div>
                      )}
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{p.name}</td>
                    <td className="px-4 py-3 text-right font-semibold text-blue-600">${p.price}</td>
                    <td className="px-4 py-3 text-right">
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${(p.stock ?? 0) > 5 ? 'bg-green-100 text-green-700' : (p.stock ?? 0) > 0 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                        {p.stock ?? 0}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-1.5">
                        <button onClick={() => openEdit(p.id)}
                          className="text-xs bg-blue-500 text-white px-2.5 py-1.5 rounded-md hover:bg-blue-600 transition">
                          Edit
                        </button>
                        <button onClick={() => setDeleteTarget(p.id)}
                          className="text-xs bg-red-500 text-white px-2.5 py-1.5 rounded-md hover:bg-red-600 transition">
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-5 py-3 border-t border-gray-200 dark:border-gray-700">
              <span className="text-sm text-gray-500 dark:text-gray-400">Page {page} of {totalPages} ({totalCount} products)</span>
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
        open={deleteTarget !== null}
        title="Delete Product"
        message="Are you sure you want to delete this product? This action cannot be undone."
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        loading={deleting}
      />

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => !saving && setShowForm(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">{editId ? 'Edit Product' : 'Add Product'}</h3>
            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                <input type="text" required value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                <textarea value={form.description} rows={3}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Price ($)</label>
                  <input type="number" step="0.01" min="0.01" required value={form.price}
                    onChange={(e) => setForm({ ...form, price: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Stock</label>
                  <input type="number" min="0" required value={form.stock}
                    onChange={(e) => setForm({ ...form, stock: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Image</label>
                <input type="file" accept="image/*" onChange={handleImageChange}
                  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 dark:file:bg-blue-900/30 file:text-blue-700 dark:file:text-blue-400 hover:file:cursor-pointer" />
                {preview && (
                  <img src={preview} alt="Preview" className="mt-2 w-24 h-24 object-cover rounded-lg border border-gray-200 dark:border-gray-600" />
                )}
              </div>
              {formError && <p className="text-red-600 text-sm">{formError}</p>}
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setShowForm(false)} disabled={saving}
                  className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition">Cancel</button>
                <button type="submit" disabled={saving}
                  className="px-4 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition disabled:opacity-50">
                  {saving ? 'Saving...' : editId ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export interface Product {
  id: number
  name: string
  description: string
  price: string
  stock?: number
  image: string | null
  created_at: string
}

export interface CartItemData {
  product: string
  quantity: number
}

export interface CartResponse {
  cart_id: number
  items: CartItemData[]
}

export interface OrderItem {
  id: number
  order: number
  product: number
  quantity: number
  price: string
}

export type OrderStatus = 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled'
export type PaymentMethod = 'COD' | 'CARD'
export type PaymentStatus = 'pending' | 'paid' | 'failed'

export interface Order {
  id: number
  user: number
  items: OrderItem[]
  created_at: string
  updated_at: string
  shipping_address: string
  status: OrderStatus
  total_price: string
  phone: string
  payment_method: PaymentMethod
  payment_status: PaymentStatus
  full_name: string
}

export interface AdminOrder extends Order {
  username: string
  email: string
  is_archived: boolean
}

export interface User {
  id: number
  username: string
  email: string
  is_staff: boolean
  is_email_verified: boolean
}

export interface LowStockProduct {
  id: number
  name: string
  stock: number
}

export interface DashboardOverview {
  total_orders: number
  total_revenue: number
  orders_by_status: Record<string, number>
  revenue_this_month: number
  average_order_value: number
  total_products: number
  total_users: number
  new_users_this_month: number
  low_stock_products: LowStockProduct[]
}

export interface BestSeller {
  product_id: number
  name: string
  total_quantity_sold: number
  total_revenue: string
  current_stock: number
}

export interface LoginResponse {
  access: string
}

export interface RegisterResponse {
  user: User
  access: string
}

export interface RefreshResponse {
  access: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface CheckoutData {
  shipping_address: string
  phone: string
}

export interface CodPaymentData {
  payment_method: 'COD'
  full_name: string
  phone: string
}

export interface ApiError {
  detail?: string
  error?: string
  [key: string]: unknown
}

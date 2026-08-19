export interface Application {
  id: number
  listing_id: number
  user_id: number
  status: 'new' | 'contacted' | 'accepted' | 'declined'
  message?: string
  created_at: string
  updated_at: string
  listing?: {
    id: number
    title: string
    price: number
    currency: string
    price_period: string
    organization?: { id: number; name: string }
  }
  applicant?: {
    id: number
    full_name: string
    email: string
    phone?: string
  }
}

export interface ApplicationStatistics {
  total: number
  new: number
  contacted: number
  accepted: number
  declined: number
}

export interface ApplicationsListParams {
  page?: number
  per_page?: number
  search?: string
  'filter[status]'?: string
  'filter[listing_id]'?: number
  sort?: string
}

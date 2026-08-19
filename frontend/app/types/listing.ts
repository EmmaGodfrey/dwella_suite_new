export interface PropertyType {
  id: number
  name: string
  slug: string
}

export interface Province {
  id: number
  name: string
}

export interface District {
  id: number
  name: string
  province_id: number
}

export interface Constituency {
  id: number
  name: string
  district_id: number
}

export interface ListingImage {
  id: number
  listing_id: number
  path: string
  disk: string
  is_thumbnail: boolean
  order: number
  url?: string
}

export interface Amenity {
  id: number
  name: string
  icon?: string
  category_id?: number
}

export interface Organization {
  id: number
  name: string
}

export interface User {
  id: number
  full_name: string
  email: string
}

export interface Listing {
  id: number
  organization_id: number
  created_by_user_id: number
  title: string
  description: string
  property_type_id: number
  status: 'draft' | 'pending' | 'approved' | 'published' | 'rejected' | 'archived'
  rejection_reason?: string
  price_amount_minor: number
  price: number
  currency: string
  price_period: string
  province_id: number
  district_id?: number
  constituency_id?: number
  address_line?: string
  location_text?: string
  latitude?: number
  longitude?: number
  created_at: string
  updated_at: string
  property_type?: PropertyType
  province?: Province
  district?: District
  constituency?: Constituency
  images?: ListingImage[]
  thumbnail?: ListingImage
  amenities?: Amenity[]
  organization?: Organization
  creator?: User
}

export interface ListingsListParams {
  page?: number
  per_page?: number
  search?: string
  'filter[status]'?: string
  'filter[organization_id]'?: number
  'filter[property_type_id]'?: number
  'filter[province_id]'?: number
  'filter[district_id]'?: number
  'filter[price_period]'?: string
  sort?: string
  export?: boolean
}

export interface ListingStatistics {
  total: number
  published: number
  pending: number
  draft: number
  rejected: number
  archived: number
}

export interface CreateListingInput {
  organization_id?: number
  title: string
  description: string
  property_type_id: number
  price_amount_minor: number
  currency?: string
  price_period: string
  province_id: number
  district_id?: number
  ward_id?: number
  address_line?: string
  location_text?: string
  latitude?: number
  longitude?: number
  amenity_ids?: number[]
  status?: 'draft' | 'pending' | 'published' | 'approved'
  images?: File[]
  thumbnail_index?: number
}

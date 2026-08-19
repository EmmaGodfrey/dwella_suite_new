export interface AmenityCategory {
  id: number
  name: string
  slug: string
  description?: string
  is_active: number | boolean
  created_at?: string
  updated_at?: string
}

export interface Amenity {
  id: number
  name: string
  category_id?: number
  icon?: string
  is_active: number | boolean
  category?: AmenityCategory
  created_at?: string
  updated_at?: string
}

export interface AmenityCreateInput {
  name: string
  category_id?: number
  icon?: string
  is_active: number | boolean
}

export interface AmenityUpdateInput {
  name?: string
  category_id?: number
  icon?: string
  is_active?: number | boolean
}

export interface CategoryCreateInput {
  name: string
  slug: string
  description?: string
  is_active: number | boolean
}

export interface CategoryUpdateInput {
  name?: string
  slug?: string
  description?: string
  is_active?: number | boolean
}

export interface AmenitiesListParams {
  page?: number
  per_page?: number
  search?: string
  'filter[category_id]'?: number
  'filter[is_active]'?: boolean
  sort?: string
  export?: boolean
}

export interface CategoriesListParams {
  page?: number
  per_page?: number
  search?: string
}

export interface User {
  id: number
  full_name: string
  email: string
  phone?: string
  is_admin: boolean
  is_lister: boolean
  system_roles: string[]
  is_active?: number
  created_at?: string
  updated_at?: string
}

export interface UserCreateInput {
  full_name: string
  email: string
  password: string
  phone?: string
  role?: string
}

export interface UserUpdateInput {
  full_name?: string
  email?: string
  phone?: string
  password?: string
  role?: string
}

export interface UsersListParams {
  page?: number
  per_page?: number
  search?: string
  role?: string
  'filter[is_admin]'?: boolean
  'filter[is_lister]'?: boolean
}

import type { ApiResponse } from '~/types/api'

interface RequestOptions extends RequestInit {
  params?: Record<string, any>
}

class ApiService {
  private baseUrl: string
  private getToken: () => string | null

  constructor(baseUrl: string, getToken: () => string | null) {
    this.baseUrl = baseUrl
    this.getToken = getToken
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    }

    const token = this.getToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    return headers
  }

  private async request<T = any>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const { params, ...fetchOptions } = options

    let url = `${this.baseUrl}${endpoint}`

    // Add query parameters
    if (params) {
      const searchParams = new URLSearchParams()
      Object.keys(params).forEach((key) => {
        if (params[key] !== undefined && params[key] !== null && params[key] !== '') {
          searchParams.append(key, params[key].toString())
        }
      })
      const queryString = searchParams.toString()
      if (queryString) {
        url += `?${queryString}`
      }
    }

    try {
      console.log('[API Request]', url)
      
      const response = await fetch(url, {
        ...fetchOptions,
        headers: {
          ...this.getHeaders(),
          ...fetchOptions.headers,
        },
      })

      const data = await response.json()

      if (!response.ok) {
        console.error('[API Error]', response.status, data)
        
        // Handle 401 Unauthorized - auto logout
        if (response.status === 401 && process.client) {
          console.warn('[API] Unauthorized - clearing auth state')
          sessionStorage.removeItem('authToken')
          sessionStorage.removeItem('authUser')
          sessionStorage.removeItem('authPermissions')
          
          // Only redirect if not already on login or logout endpoint
          if (!endpoint.includes('/login') && !endpoint.includes('/logout')) {
            navigateTo('/login', { replace: true })
          }
        }
        
        return {
          success: false,
          message: data.message || 'Request failed',
          errors: data.errors,
          status: response.status,
        }
      }

      return {
        ...data,
        status: response.status,
      }
    } catch (error: any) {
      console.error('[API Network Error]', error.message, 'URL:', url)
      return {
        success: false,
        message: error.message || 'Network error - Is your backend running?',
      }
    }
  }

  async get<T = any>(endpoint: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'GET' })
  }

  async post<T = any>(endpoint: string, body?: any, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  async put<T = any>(endpoint: string, body?: any, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  async delete<T = any>(endpoint: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' })
  }
}

export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig()
  
  const getToken = () => {
    const authStore = useAuthStore()
    return authStore.token
  }
  
  const api = new ApiService(config.public.apiBaseUrl as string, getToken)

  return {
    provide: {
      api,
    },
  }
})

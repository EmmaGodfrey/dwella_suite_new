import type { ApiResponse } from './api'

interface ApiService {
  get<T = any>(endpoint: string, options?: any): Promise<ApiResponse<T>>
  post<T = any>(endpoint: string, body?: any, options?: any): Promise<ApiResponse<T>>
  put<T = any>(endpoint: string, body?: any, options?: any): Promise<ApiResponse<T>>
  delete<T = any>(endpoint: string, options?: any): Promise<ApiResponse<T>>
}

declare module '#app' {
  interface NuxtApp {
    $api: ApiService
  }
}

declare module 'vue' {
  interface ComponentCustomProperties {
    $api: ApiService
  }
}

export {}

import type { ApiResponse } from '~/types/api'

/**
 * Normalized output structure
 */
export interface NormalizedResponse<T = any> {
  success: boolean
  message: string
  data: T | null
  errors: Record<string, string[]> | null
  status?: number
}

const STATUS_DEFAULTS: Record<number, string> = {
  400: 'Invalid request. Please check your input.',
  401: 'You are not authorized. Please sign in again.',
  403: 'You do not have permission to perform this action.',
  404: 'We could not find what you requested.',
  409: 'There is a conflict with existing data.',
  413: 'The uploaded data is too large.',
  415: 'Unsupported media type. Please check the Content-Type.',
  422: 'Validation failed. Please fix the highlighted fields.',
  429: 'Too many requests. Please slow down and try again.',
  500: 'Something went wrong on our side.',
  502: 'Upstream service is unavailable.',
  503: 'Service temporarily unavailable. Please try again later.',
  504: 'Server took too long to respond.',
}

/**
 * Normalize error object from Laravel validation errors
 */
export function normalizeErrors(errors: any): Record<string, string[]> | null {
  if (!errors) return null
  
  if (typeof errors === 'string') {
    return { _general: [errors] }
  }
  
  if (Array.isArray(errors)) {
    return { _general: errors }
  }
  
  if (typeof errors === 'object') {
    const normalized: Record<string, string[]> = {}
    
    for (const [key, value] of Object.entries(errors)) {
      if (Array.isArray(value)) {
        normalized[key] = value as string[]
      } else if (typeof value === 'string') {
        normalized[key] = [value]
      }
    }
    
    return Object.keys(normalized).length > 0 ? normalized : null
  }
  
  return null
}

/**
 * Get first error message from normalized errors
 */
export function getFirstError(errors: Record<string, string[]> | null): string | null {
  if (!errors) return null
  
  const firstKey = Object.keys(errors)[0]
  if (!firstKey) return null
  
  const messages = errors[firstKey]
  return messages && messages.length > 0 ? messages[0] ?? null : null
}

/**
 * Handle API response and normalize the output
 */
export function handleResponse<T = any>(
  response: ApiResponse<T>,
  opts: {
    successMessage?: string
    errorMessage?: string
    status?: number
  } = {}
): NormalizedResponse<T> {
  const { successMessage, errorMessage, status } = opts
  
  // Check if response has success property (Laravel format)
  if (response && typeof response === 'object' && 'success' in response) {
    const success = !!response.success
    const message = response.message || (success ? successMessage : errorMessage) || (success ? 'Success' : 'Request failed')
    const errors = normalizeErrors(response.errors)
    
    return {
      success,
      message,
      data: response.data ?? null,
      errors,
      status,
    }
  }
  
  // Fallback for unexpected response format
  return {
    success: false,
    message: errorMessage || STATUS_DEFAULTS[status || 500] || 'Request failed',
    data: null,
    errors: null,
    status,
  }
}

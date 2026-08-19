import { handleResponse, type NormalizedResponse } from './handleResponse'
import { toast } from 'vue3-toastify'
import type { ApiResponse } from '~/types/api'

export interface QueryWrapOptions {
  showToast?: boolean
  successMessage?: string
  errorMessage?: string
  silentCodes?: number[]
}

export interface MutationWrapOptions extends QueryWrapOptions {
  return?: 'normalized' | 'data'
}

/**
 * Custom error class that includes normalized response
 */
export class ApiError extends Error {
  normalized: NormalizedResponse
  
  constructor(message: string, normalized: NormalizedResponse) {
    super(message)
    this.name = 'ApiError'
    this.normalized = normalized
  }
}

/**
 * Extract validation errors from a mutation
 * Returns errors object and helper function to get field errors
 */
export function useMutationErrors(mutation: any) {
  const errors = computed(() => {
    if (mutation.error.value instanceof ApiError) {
      return mutation.error.value.normalized.errors || {}
    }
    return {}
  })

  const getFieldError = (field: string) => {
    const fieldErrors = errors.value[field]
    return fieldErrors && fieldErrors.length > 0 ? fieldErrors[0] : ''
  }

  return {
    errors,
    getFieldError,
  }
}

/**
 * Wrap query function for Vue Query
 * - Returns plain data on success (for cache)
 * - Throws ApiError on failure with normalized response
 */
export function queryWrap<T = any>(
  factory: () => Promise<ApiResponse<T>>,
  opts: QueryWrapOptions = {}
) {
  return async (): Promise<T> => {
    const { showToast = false } = opts
    
    try {
      const response = await factory()
      const normalized = handleResponse(response, opts)
      
      if (!normalized.success) {
        if (showToast) {
          toast.error(normalized.message)
        }
        throw new ApiError(normalized.message || 'Request failed', normalized)
      }
      
      if (showToast && opts.successMessage) {
        toast.success(normalized.message)
      }
      
      return normalized.data as T
    } catch (error: any) {
      // If it's already an ApiError, re-throw it
      if (error instanceof ApiError) {
        throw error
      }
      
      // Handle unexpected errors
      const errorMessage = error.message || opts.errorMessage || 'Request failed'
      const normalized: NormalizedResponse = {
        success: false,
        message: errorMessage,
        data: null,
        errors: null,
      }
      
      if (showToast) {
        toast.error(errorMessage)
      }
      
      throw new ApiError(errorMessage, normalized)
    }
  }
}

/**
 * Wrap mutation function for Vue Query
 * - Returns normalized response or plain data (based on options)
 * - Throws ApiError on failure with normalized response
 * - Shows toasts by default
 */
export function mutationWrap<TData = any, TVariables = any>(
  factory: (variables: TVariables) => Promise<ApiResponse<TData>>,
  opts: MutationWrapOptions = {}
) {
  return async (variables: TVariables): Promise<NormalizedResponse<TData> | TData> => {
    const { showToast = true, return: returnType = 'normalized', silentCodes = [] } = opts
    
    try {
      const response = await factory(variables)
      const normalized = handleResponse(response, opts)
      
      if (!normalized.success) {
        // Check if we should show toast for this error
        const shouldShowToast = showToast && !silentCodes.includes(normalized.status || 0)
        
        if (shouldShowToast) {
          // Show validation errors if present
          if (normalized.errors) {
            const firstError = Object.values(normalized.errors)[0]?.[0]
            toast.error(firstError || normalized.message)
          } else {
            toast.error(normalized.message)
          }
        }
        
        throw new ApiError(normalized.message || 'Request failed', normalized)
      }
      
      if (showToast && normalized.message) {
        toast.success(normalized.message)
      }
      
      return returnType === 'data' ? (normalized.data as TData) : normalized
    } catch (error: any) {
      // If it's already an ApiError, re-throw it
      if (error instanceof ApiError) {
        throw error
      }
      
      // Handle unexpected errors
      const errorMessage = error.message || opts.errorMessage || 'Request failed'
      const normalized: NormalizedResponse = {
        success: false,
        message: errorMessage,
        data: null,
        errors: null,
      }
      
      if (showToast) {
        toast.error(errorMessage)
      }
      
      throw new ApiError(errorMessage, normalized)
    }
  }
}

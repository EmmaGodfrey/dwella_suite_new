import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { queryWrap, mutationWrap, useMutationErrors } from '~/utils/queryWrap'
import type { User, UserCreateInput, UserUpdateInput, UsersListParams } from '../types/user'
import type { PaginatedResponse } from '../types/api'

export const useUsers = () => {
  const usersStore = useUsersStore()
  const queryClient = useQueryClient()

  // Fetch users query
  const useFetchUsersQuery = (params: Ref<UsersListParams>) => {
    return useQuery({
      queryKey: ['users', params],
      queryFn: queryWrap(
        () => usersStore.fetchUsers(params.value),
        { showToast: false }
      ),
      select: (data) => {
        return data as PaginatedResponse<User>
      },
    })
  }

  // Create user mutation
  const useCreateUserMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap<User, UserCreateInput>(
        (userData) => usersStore.createUser(userData),
        { 
          successMessage: 'User created successfully',
          showToast: true,
          silentCodes: [422], // Don't show toast for validation errors
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['users'] })
      },
    })

    const { errors, getFieldError } = useMutationErrors(mutation)

    return {
      ...mutation,
      errors,
      getFieldError,
    }
  }

  // Update user mutation
  const useUpdateUserMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap<User, { id: number; userData: UserUpdateInput }>(
        ({ id, userData }) => usersStore.updateUser(id, userData),
        { 
          successMessage: 'User updated successfully',
          showToast: true,
          silentCodes: [422], // Don't show toast for validation errors
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['users'] })
      },
    })

    const { errors, getFieldError } = useMutationErrors(mutation)

    return {
      ...mutation,
      errors,
      getFieldError,
    }
  }

  // Delete user mutation
  const useDeleteUserMutation = () => {
    return useMutation({
      mutationFn: mutationWrap<void, number>(
        (id) => usersStore.deleteUser(id),
        { 
          successMessage: 'User deleted successfully',
          showToast: true, // Show toast for delete success/errors
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['users'] })
      },
    })
  }

  return {
    useFetchUsersQuery,
    useCreateUserMutation,
    useUpdateUserMutation,
    useDeleteUserMutation,
  }
}

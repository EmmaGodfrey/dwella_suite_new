import { defineStore, acceptHMRUpdate } from 'pinia'
import type { User, UserCreateInput, UserUpdateInput, UsersListParams } from '../types/user'
import type { PaginatedResponse } from '../types/api'

export const useUsersStore = defineStore('users', () => {
  const { $api } = useNuxtApp()
  
  const users = ref<User[]>([])
  const pagination = ref({
    currentPage: 1,
    lastPage: 1,
    perPage: 10,
    total: 0,
    from: 0,
    to: 0,
  })

  async function fetchUsers(params: UsersListParams = {}) {
    const response = await $api.get<PaginatedResponse<User>>('/admin/users', { params })
    
    if (response.success && response.data) {
      users.value = response.data.data
      pagination.value = {
        currentPage: response.data.current_page,
        lastPage: response.data.last_page,
        perPage: response.data.per_page,
        total: response.data.total,
        from: response.data.from,
        to: response.data.to,
      }
    }
    
    return response
  }

  async function createUser(userData: UserCreateInput) {
    const response = await $api.post<User>('/admin/users', userData)
    return response
  }

  async function updateUser(id: number, userData: UserUpdateInput) {
    const response = await $api.put<User>(`/admin/users/${id}`, userData)
    return response
  }

  async function deleteUser(id: number) {
    const response = await $api.delete(`/admin/users/${id}`)
    return response
  }

  return {
    users,
    pagination,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
  }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useUsersStore, import.meta.hot))
}

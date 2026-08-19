<template>
  <div>
    <BreadCrumbs title="Users Management" main="Admin" />

    <div class="container-fluid">
      <!-- Role Tabs -->
      <div class="row mb-3">
        <div class="col-sm-12">
          <div class="card">
            <div class="card-body pb-0">
              <ul class="nav nav-tabs border-tab" role="tablist">
                <li class="nav-item" v-for="tab in tabs" :key="tab.key">
                  <a
                    class="nav-link"
                    :class="{ active: activeTab === tab.key }"
                    @click.prevent="setTab(tab.key)"
                    href="#"
                  >
                    <i :class="tab.icon" class="me-2"></i>{{ tab.label }}
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- DataTable -->
      <div class="row">
        <div class="col-sm-12">
          <DataTable
            :title="activeTabLabel"
            :headers="headers"
            :items="users"
            :loading="isLoading"
            :items-per-page="params.per_page"
            :total-items="usersStore.pagination.total"
            :current-page="params.page"
            :searchable="true"
            search-placeholder="Search by name or email..."
            @update:current-page="p => { params.page = p }"
            @update:items-per-page="n => { params.per_page = n; params.page = 1 }"
            @update:search="s => { params.search = s; params.page = 1 }"
          >
            <template #header-actions>
              <button class="btn btn-primary" @click="openCreate">
                <i class="fa fa-plus me-1"></i>Add User
              </button>
            </template>

            <template #cell-is_admin="{ row }">
              <span class="badge" :class="row.original.is_admin ? 'badge-danger' : 'badge-secondary'">
                {{ row.original.is_admin ? 'Admin' : 'User' }}
              </span>
            </template>

            <template #cell-is_lister="{ row }">
              <span class="badge" :class="row.original.is_lister ? 'badge-success' : 'badge-secondary'">
                {{ row.original.is_lister ? 'Lister' : '—' }}
              </span>
            </template>

            <template #cell-created_at="{ row }">
              {{ fmtDate(row.original.created_at) }}
            </template>

            <template #cell-actions="{ row }">
              <div class="dropstart">
                <button
                  class="btn btn-sm btn-light border-0 p-1"
                  type="button"
                  :id="`dd-${row.original.id}`"
                  data-bs-toggle="dropdown"
                  aria-expanded="false"
                  style="width:30px;height:30px;line-height:1;"
                >
                  <i class="fa fa-ellipsis-v"></i>
                </button>
                <ul class="dropdown-menu dropdown-menu-sm" :aria-labelledby="`dd-${row.original.id}`">
                  <li>
                    <a class="dropdown-item dropdown-item-sm" href="#" @click.prevent="openEdit(row.original)">
                      <i class="fa fa-pencil me-2"></i>Edit
                    </a>
                  </li>
                  <li><hr class="dropdown-divider my-1"></li>
                  <li>
                    <a class="dropdown-item dropdown-item-sm text-danger" href="#" @click.prevent="handleDelete(row.original)">
                      <i class="fa fa-trash me-2"></i>Delete
                    </a>
                  </li>
                </ul>
              </div>
            </template>
          </DataTable>
        </div>
      </div>
    </div>

    <!-- Create / Edit Modal -->
    <div class="modal fade" id="userModal" tabindex="-1" ref="modalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ editingId ? 'Edit' : 'Add' }} User</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="handleSave">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">Full Name <span class="text-danger">*</span></label>
                <input
                  type="text"
                  class="form-control"
                  v-model="form.full_name"
                  :class="activeMutation.getFieldError('full_name') ? 'is-invalid' : ''"
                  required
                />
                <div class="invalid-feedback" v-if="activeMutation.getFieldError('full_name')">
                  {{ activeMutation.getFieldError('full_name') }}
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Email <span class="text-danger">*</span></label>
                <input
                  type="email"
                  class="form-control"
                  v-model="form.email"
                  :class="activeMutation.getFieldError('email') ? 'is-invalid' : ''"
                  required
                />
                <div class="invalid-feedback" v-if="activeMutation.getFieldError('email')">
                  {{ activeMutation.getFieldError('email') }}
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Phone</label>
                <input
                  type="tel"
                  class="form-control"
                  v-model="form.phone"
                  placeholder="e.g. 0971234567"
                />
              </div>

              <div class="mb-3">
                <label class="form-label">
                  Password {{ editingId ? '(leave blank to keep current)' : '*' }}
                </label>
                <input
                  :type="showPw ? 'text' : 'password'"
                  class="form-control"
                  v-model="form.password"
                  :class="activeMutation.getFieldError('password') ? 'is-invalid' : ''"
                  :required="!editingId"
                />
                <div class="invalid-feedback" v-if="activeMutation.getFieldError('password')">
                  {{ activeMutation.getFieldError('password') }}
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Role</label>
                <select class="form-select" v-model="form.role">
                  <option value="">Standard User</option>
                  <option value="admin">Admin</option>
                  <option value="property_lister">Property Lister</option>
                  <option value="tenant">Tenant</option>
                </select>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="activeMutation.isPending.value">
                <span v-if="activeMutation.isPending.value" class="spinner-border spinner-border-sm me-2"></span>
                {{ editingId ? 'Update' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { User, UserCreateInput, UserUpdateInput, UsersListParams } from '~/types/user'
import BreadCrumbs from '~/components/breadCrumbs.vue'
import DataTable from '~/components/tables/DataTable.vue'
import { Modal } from 'bootstrap'

definePageMeta({
  name: 'admin-users',
  path: '/users',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([
  { title: 'Home', url: '/dashboard' },
  { title: 'Users', active: true },
])

const usersStore = useUsersStore()
const { useFetchUsersQuery, useCreateUserMutation, useUpdateUserMutation, useDeleteUserMutation } = useUsers()

const tabs = [
  { key: '', label: 'All Users', icon: 'fa fa-users' },
  { key: 'tenant', label: 'Tenants', icon: 'fa fa-user' },
  { key: 'property_lister', label: 'Property Listers', icon: 'fa fa-home' },
  { key: 'admin', label: 'Admins', icon: 'fa fa-shield' },
]
const activeTab = ref('')
const activeTabLabel = computed(() => tabs.find(t => t.key === activeTab.value)?.label ?? 'All Users')

const params = ref<UsersListParams>({ page: 1, per_page: 10, search: '' })

const setTab = (key: string) => {
  activeTab.value = key
  params.value.role = key || undefined
  params.value.page = 1
}

const { isLoading } = useFetchUsersQuery(params)
const users = computed(() => usersStore.users)

const headers = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'full_name', title: 'Name' },
  { key: 'email', title: 'Email' },
  { key: 'phone', title: 'Phone', width: 140 },
  { key: 'is_admin', title: 'Admin', width: 90 },
  { key: 'is_lister', title: 'Lister', width: 90 },
  { key: 'created_at', title: 'Joined', width: 130 },
  { key: 'actions', title: 'Actions', align: 'center', width: 60 },
]

const modalEl = ref<HTMLElement | null>(null)
let modalInstance: Modal | null = null
onMounted(() => { if (modalEl.value) modalInstance = new Modal(modalEl.value) })
onBeforeUnmount(() => modalInstance?.dispose())

const editingId = ref<number | null>(null)
const showPw = ref(false)
const form = ref<any>({ full_name: '', email: '', phone: '', password: '', role: '' })

const createMutation = useCreateUserMutation()
const updateMutation = useUpdateUserMutation()
const deleteMutation = useDeleteUserMutation()

const activeMutation = computed(() => editingId.value ? updateMutation : createMutation)

const openCreate = () => {
  editingId.value = null
  form.value = { full_name: '', email: '', phone: '', password: '', role: '' }
  createMutation.reset()
  modalInstance?.show()
}

const openEdit = (user: User) => {
  editingId.value = user.id
  form.value = {
    full_name: user.full_name,
    email: user.email,
    phone: user.phone || '',
    password: '',
    role: user.system_roles?.[0] || '',
  }
  updateMutation.reset()
  modalInstance?.show()
}

const handleSave = async () => {
  try {
    if (editingId.value) {
      const updateData: UserUpdateInput = {
        full_name: form.value.full_name,
        email: form.value.email,
        phone: form.value.phone,
        role: form.value.role,
      }
      if (form.value.password) updateData.password = form.value.password
      await updateMutation.mutateAsync({ id: editingId.value, userData: updateData })
    } else {
      await createMutation.mutateAsync(form.value as UserCreateInput)
    }
    modalInstance?.hide()
  } catch { /* handled by mutation */ }
}

const handleDelete = async (user: User) => {
  if (confirm(`Delete user "${user.full_name}"? This cannot be undone.`)) {
    await deleteMutation.mutateAsync(user.id)
  }
}

const fmtDate = (d?: string) =>
  d ? new Date(d).toLocaleDateString('en-ZM', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'
</script>

<style scoped>
.nav-tabs .nav-link { cursor: pointer; }
.dropdown-menu-sm { min-width: 8rem; font-size: 0.875rem; }
.dropdown-item-sm { padding: 0.4rem 1rem; font-size: 0.875rem; }
.badge-success   { background-color: #51bb25; }
.badge-danger    { background-color: #dc3545; }
.badge-secondary { background-color: #6c757d; }
</style>

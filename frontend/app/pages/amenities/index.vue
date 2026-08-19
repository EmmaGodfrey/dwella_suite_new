<template>
  <div>
    <BreadCrumbs title="Amenities Management" main="Admin" />
    
    <div class="container-fluid">
      <div class="row">
        <div class="col-sm-12">
          <div class="card">
            <div class="card-body">
              <!-- Tabs -->
              <ul class="nav nav-tabs border-tab" role="tablist">
                <li class="nav-item">
                  <a 
                    class="nav-link" 
                    :class="{ active: activeTab === 'amenities' }"
                    @click.prevent="activeTab = 'amenities'"
                    href="#"
                  >
                    <i class="fa fa-th me-2"></i>Amenities
                  </a>
                </li>
                <li class="nav-item">
                  <a 
                    class="nav-link" 
                    :class="{ active: activeTab === 'categories' }"
                    @click.prevent="activeTab = 'categories'"
                    href="#"
                  >
                    <i class="fa fa-list me-2"></i>Categories
                  </a>
                </li>
              </ul>

              <!-- Tab Content -->
              <div class="tab-content mt-4">
                <!-- Amenities Tab -->
                <div v-show="activeTab === 'amenities'">
                  <!-- Search and Add Button -->
                  <div class="d-flex justify-content-between align-items-center mb-4">
                    <div class="d-flex gap-2 align-items-center">
                      <input 
                        type="text" 
                        class="form-control" 
                        placeholder="Search amenities..."
                        v-model="amenitySearch"
                        style="width: 300px;"
                      />
                      <select 
                        class="form-select" 
                        v-model="amenityFilters['filter[category_id]']"
                        style="width: 200px;"
                      >
                        <option :value="undefined">All Categories</option>
                        <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                          {{ cat.name }}
                        </option>
                      </select>
                      <select 
                        class="form-select" 
                        v-model="amenityFilters['filter[is_active]']"
                        style="width: 150px;"
                      >
                        <option :value="undefined">All Status</option>
                        <option :value="true">Active</option>
                        <option :value="false">Inactive</option>
                      </select>
                    </div>
                    <button 
                      type="button"
                      class="btn btn-primary"
                      @click="openAddAmenityDialog"
                    >
                      <i class="fa fa-plus me-1"></i>
                      Add Amenity
                    </button>
                  </div>

                  <!-- Amenities Grid -->
                  <div v-if="amenitiesLoading" class="text-center py-5">
                    <div class="spinner-border" role="status"></div>
                    <p class="mt-2">Loading amenities...</p>
                  </div>

                  <div v-else-if="!amenities.length" class="text-center py-5 text-muted">
                    <i class="fa fa-inbox fa-3x mb-3 d-block opacity-25"></i>
                    <p>No amenities found</p>
                  </div>

                  <div v-else class="row g-3">
                    <div 
                      v-for="amenity in amenities" 
                      :key="amenity.id"
                      class="col-xl-2 col-lg-3 col-md-4 col-sm-6"
                    >
                      <div class="card amenity-card h-100">
                        <div class="card-body text-center position-relative">
                          <!-- Status Badge -->
                          <span 
                            class="badge position-absolute top-0 end-0 m-2"
                            :class="amenity.is_active ? 'badge-success' : 'badge-secondary'"
                          >
                            {{ amenity.is_active ? 'Active' : 'Inactive' }}
                          </span>

                          <!-- Icon -->
                          <div class="amenity-icon mb-3">
                            <i v-if="amenity.icon" :class="amenity.icon" class="fa-3x text-primary"></i>
                            <i v-else class="fa fa-cube fa-3x text-muted"></i>
                          </div>

                          <!-- Name -->
                          <h6 class="mb-2">{{ amenity.name }}</h6>

                          <!-- Category -->
                          <p class="text-muted small mb-3">
                            {{ amenity.category?.name || 'No Category' }}
                          </p>

                          <!-- Actions -->
                          <div class="d-flex gap-2 justify-content-center">
                            <button 
                              class="btn btn-sm btn-outline-primary"
                              @click="openEditAmenityDialog(amenity)"
                            >
                              <i class="fa fa-pencil"></i>
                            </button>
                            <button 
                              class="btn btn-sm btn-outline-danger"
                              @click="handleDeleteAmenity(amenity)"
                            >
                              <i class="fa fa-trash"></i>
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Pagination -->
                  <div v-if="amenitiesPagination.lastPage > 1" class="d-flex justify-content-center mt-4">
                    <ul class="pagination pagination-primary">
                      <li class="page-item" :class="{ disabled: amenityPage === 1 }">
                        <a class="page-link" @click.prevent="amenityPage = amenityPage - 1">
                          <span>&laquo;</span>
                        </a>
                      </li>
                      <li 
                        v-for="page in amenitiesPagination.lastPage" 
                        :key="page"
                        class="page-item" 
                        :class="{ active: page === amenityPage }"
                      >
                        <a class="page-link" @click.prevent="amenityPage = page">{{ page }}</a>
                      </li>
                      <li class="page-item" :class="{ disabled: amenityPage === amenitiesPagination.lastPage }">
                        <a class="page-link" @click.prevent="amenityPage = amenityPage + 1">
                          <span>&raquo;</span>
                        </a>
                      </li>
                    </ul>
                  </div>
                </div>

                <!-- Categories Tab -->
                <div v-show="activeTab === 'categories'">
                  <DataTable
                    title="Amenity Categories"
                    :headers="categoryHeaders"
                    :items="categories"
                    :loading="categoriesLoading"
                    :items-per-page="categoryFilters.per_page"
                    :total-items="categoriesPagination.total"
                    :current-page="categoryPage"
                    :searchable="true"
                    @update:current-page="handleCategoryPageChange"
                    @update:items-per-page="handleCategoryItemsPerPageChange"
                    @update:search="handleCategorySearch"
                  >
                    <!-- Header actions -->
                    <template #header-actions>
                      <button 
                        type="button"
                        class="btn btn-primary"
                        @click="openAddCategoryDialog"
                      >
                        <i class="fa fa-plus me-1"></i>
                        Add Category
                      </button>
                    </template>

                    <!-- Status column -->
                    <template #cell-is_active="{ row }">
                      <span class="badge" :class="row.original.is_active ? 'badge-success' : 'badge-secondary'">
                        {{ row.original.is_active ? 'Active' : 'Inactive' }}
                      </span>
                    </template>

                    <!-- Actions column -->
                    <template #cell-actions="{ row }">
                      <div class="dropstart">
                        <button 
                          class="btn btn-sm btn-light border-0 p-1" 
                          type="button" 
                          :id="`dropdown-${row.original.id}`"
                          data-bs-toggle="dropdown" 
                          aria-expanded="false"
                          style="width: 30px; height: 30px; line-height: 1;"
                        >
                          <i class="fa fa-ellipsis-v"></i>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-sm" :aria-labelledby="`dropdown-${row.original.id}`">
                          <li>
                            <a class="dropdown-item dropdown-item-sm" href="#" @click.prevent="openEditCategoryDialog(row.original)">
                              <i class="fa fa-pencil me-2"></i>Edit
                            </a>
                          </li>
                          <li><hr class="dropdown-divider my-1"></li>
                          <li>
                            <a class="dropdown-item dropdown-item-sm text-danger" href="#" @click.prevent="handleDeleteCategory(row.original)">
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
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Amenity Modal -->
    <div class="modal fade" id="amenityModal" tabindex="-1" ref="amenityModalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ amenityForm.id ? 'Edit' : 'Add' }} Amenity</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="handleAmenitySave" class="needs-validation" :class="{ 'was-validated': amenityFormSubmitted }" novalidate>
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">Name</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="amenityForm.name"
                  :class="amenityMutation.getFieldError('name') ? 'is-invalid' : ''"
                  required
                />
                <div class="invalid-feedback" v-if="amenityMutation.getFieldError('name')">
                  {{ amenityMutation.getFieldError('name') }}
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Category</label>
                <select 
                  class="form-select" 
                  v-model="amenityForm.category_id"
                  :class="amenityMutation.getFieldError('category_id') ? 'is-invalid' : ''"
                >
                  <option :value="undefined">No Category</option>
                  <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                    {{ cat.name }}
                  </option>
                </select>
                <div class="invalid-feedback" v-if="amenityMutation.getFieldError('category_id')">
                  {{ amenityMutation.getFieldError('category_id') }}
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Icon (Font Awesome class)</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="amenityForm.icon"
                  placeholder="e.g., fa fa-wifi"
                  :class="amenityMutation.getFieldError('icon') ? 'is-invalid' : ''"
                />
                <small class="text-muted">Leave empty for default icon</small>
                <div class="invalid-feedback" v-if="amenityMutation.getFieldError('icon')">
                  {{ amenityMutation.getFieldError('icon') }}
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Status</label>
                <select 
                  class="form-select" 
                  v-model="amenityForm.is_active"
                  required
                >
                  <option :value="1">Active</option>
                  <option :value="0">Inactive</option>
                </select>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="amenityMutation.isPending.value">
                <span v-if="amenityMutation.isPending.value" class="spinner-border spinner-border-sm me-2"></span>
                {{ amenityForm.id ? 'Update' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Add/Edit Category Modal -->
    <div class="modal fade" id="categoryModal" tabindex="-1" ref="categoryModalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ categoryForm.id ? 'Edit' : 'Add' }} Category</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="handleCategorySave" class="needs-validation" :class="{ 'was-validated': categoryFormSubmitted }" novalidate>
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">Name</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="categoryForm.name"
                  :class="categoryMutation.getFieldError('name') ? 'is-invalid' : ''"
                  required
                />
                <div class="invalid-feedback" v-if="categoryMutation.getFieldError('name')">
                  {{ categoryMutation.getFieldError('name') }}
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Slug</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="categoryForm.slug"
                  :class="categoryMutation.getFieldError('slug') ? 'is-invalid' : ''"
                  required
                />
                <small class="text-muted">URL-friendly identifier</small>
                <div class="invalid-feedback" v-if="categoryMutation.getFieldError('slug')">
                  {{ categoryMutation.getFieldError('slug') }}
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Description</label>
                <textarea 
                  class="form-control" 
                  v-model="categoryForm.description"
                  rows="3"
                  :class="categoryMutation.getFieldError('description') ? 'is-invalid' : ''"
                ></textarea>
                <div class="invalid-feedback" v-if="categoryMutation.getFieldError('description')">
                  {{ categoryMutation.getFieldError('description') }}
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Status</label>
                <select 
                  class="form-select" 
                  v-model="categoryForm.is_active"
                  required
                >
                  <option :value="1">Active</option>
                  <option :value="0">Inactive</option>
                </select>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="categoryMutation.isPending.value">
                <span v-if="categoryMutation.isPending.value" class="spinner-border spinner-border-sm me-2"></span>
                {{ categoryForm.id ? 'Update' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Amenity, AmenityCategory, AmenityCreateInput, AmenityUpdateInput, CategoryCreateInput, CategoryUpdateInput, AmenitiesListParams, CategoriesListParams } from '~/types/amenity'
import BreadCrumbs from '~/components/breadCrumbs.vue'
import DataTable from '~/components/tables/DataTable.vue'
import { Modal } from 'bootstrap'

definePageMeta({
  name: 'amenities',
  path: '/amenities/all',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
const amenitiesStore = useAmenitiesStore()
const { 
  useFetchAmenitiesQuery,
  useCreateAmenityMutation,
  useUpdateAmenityMutation,
  useDeleteAmenityMutation,
  useFetchCategoriesQuery,
  useCreateCategoryMutation,
  useUpdateCategoryMutation,
  useDeleteCategoryMutation,
} = useAmenities()

// Set breadcrumbs
setBreadcrumbs([
  { title: 'Home', url: '/dashboard' },
  { title: 'Amenities', active: true },
])

// Tabs
const activeTab = ref<'amenities' | 'categories'>('amenities')

// Modal refs
const amenityModalEl = ref<HTMLElement | null>(null)
const categoryModalEl = ref<HTMLElement | null>(null)
let amenityModalInstance: Modal | null = null
let categoryModalInstance: Modal | null = null

// Amenities
const amenityPage = ref(1)
const amenitySearch = ref('')
const amenityFilters = ref<AmenitiesListParams>({
  page: 1,
  per_page: 12,
  search: '',
})

const amenitiesParams = computed(() => ({
  ...amenityFilters.value,
  page: amenityPage.value,
  search: amenitySearch.value,
}))

const { data: amenitiesData, isLoading: amenitiesLoading } = useFetchAmenitiesQuery(amenitiesParams)
const amenities = computed(() => amenitiesStore.amenities || [])
const amenitiesPagination = computed(() => amenitiesStore.amenitiesPagination)

// Categories
const categoryPage = ref(1)
const categoryFilters = ref<CategoriesListParams>({
  page: 1,
  per_page: 10,
  search: '',
})

const categoriesParams = computed(() => ({
  ...categoryFilters.value,
  page: categoryPage.value,
}))

const { data: categoriesData, isLoading: categoriesLoading } = useFetchCategoriesQuery(categoriesParams)
const categories = computed(() => amenitiesStore.categories || [])
const categoriesPagination = computed(() => amenitiesStore.categoriesPagination)

// Category table headers
const categoryHeaders = [
  { title: 'ID', key: 'id', sortable: false, width: 80 },
  { title: 'NAME', key: 'name', sortable: false },
  { title: 'SLUG', key: 'slug', sortable: false },
  { title: 'DESCRIPTION', key: 'description', sortable: false },
  { title: 'STATUS', key: 'is_active', sortable: false, width: 100 },
  { title: 'ACTIONS', key: 'actions', sortable: false, align: 'center', width: 60 },
]

// Amenity form
const amenityFormSubmitted = ref(false)
const amenityForm = ref<AmenityCreateInput & { id?: number }>({
  name: '',
  category_id: undefined,
  icon: '',
  is_active: 1,
})

// Category form
const categoryFormSubmitted = ref(false)
const categoryForm = ref<CategoryCreateInput & { id?: number }>({
  name: '',
  slug: '',
  description: '',
  is_active: 1,
})

// Initialize modals
onMounted(() => {
  if (amenityModalEl.value) {
    amenityModalInstance = new Modal(amenityModalEl.value)
  }
  if (categoryModalEl.value) {
    categoryModalInstance = new Modal(categoryModalEl.value)
  }
})

onBeforeUnmount(() => {
  amenityModalInstance?.dispose()
  categoryModalInstance?.dispose()
})

// Mutations
const createAmenityMutation = useCreateAmenityMutation()
const updateAmenityMutation = useUpdateAmenityMutation()
const deleteAmenityMutation = useDeleteAmenityMutation()
const createCategoryMutation = useCreateCategoryMutation()
const updateCategoryMutation = useUpdateCategoryMutation()
const deleteCategoryMutation = useDeleteCategoryMutation()

const amenityMutation = computed(() => amenityForm.value.id ? updateAmenityMutation : createAmenityMutation)
const categoryMutation = computed(() => categoryForm.value.id ? updateCategoryMutation : createCategoryMutation)

// Amenity handlers
const openAddAmenityDialog = () => {
  amenityForm.value = {
    name: '',
    category_id: undefined,
    icon: '',
    is_active: 1,
  }
  amenityFormSubmitted.value = false
  createAmenityMutation.reset()
  amenityModalInstance?.show()
}

const openEditAmenityDialog = (amenity: Amenity) => {
  amenityForm.value = {
    id: amenity.id,
    name: amenity.name,
    category_id: amenity.category_id,
    icon: amenity.icon || '',
    is_active: amenity.is_active ? 1 : 0,
  }
  amenityFormSubmitted.value = false
  updateAmenityMutation.reset()
  amenityModalInstance?.show()
}

const handleAmenitySave = async () => {
  amenityFormSubmitted.value = true
  
  const { id, ...data } = amenityForm.value
  
  try {
    if (id) {
      await updateAmenityMutation.mutateAsync({ id, data })
    } else {
      await createAmenityMutation.mutateAsync(data)
    }
    amenityModalInstance?.hide()
    amenityFormSubmitted.value = false
  } catch (error) {
    amenityFormSubmitted.value = false
  }
}

const handleDeleteAmenity = async (amenity: Amenity) => {
  if (confirm(`Are you sure you want to delete "${amenity.name}"?`)) {
    await deleteAmenityMutation.mutateAsync(amenity.id)
  }
}

// Category handlers
const openAddCategoryDialog = () => {
  categoryForm.value = {
    name: '',
    slug: '',
    description: '',
    is_active: 1,
  }
  categoryFormSubmitted.value = false
  createCategoryMutation.reset()
  categoryModalInstance?.show()
}

const openEditCategoryDialog = (category: AmenityCategory) => {
  categoryForm.value = {
    id: category.id,
    name: category.name,
    slug: category.slug,
    description: category.description || '',
    is_active: category.is_active ? 1 : 0,
  }
  categoryFormSubmitted.value = false
  updateCategoryMutation.reset()
  categoryModalInstance?.show()
}

const handleCategorySave = async () => {
  categoryFormSubmitted.value = true
  
  const { id, ...data } = categoryForm.value
  
  try {
    if (id) {
      await updateCategoryMutation.mutateAsync({ id, data })
    } else {
      await createCategoryMutation.mutateAsync(data)
    }
    categoryModalInstance?.hide()
    categoryFormSubmitted.value = false
  } catch (error) {
    categoryFormSubmitted.value = false
  }
}

const handleDeleteCategory = async (category: AmenityCategory) => {
  if (confirm(`Are you sure you want to delete "${category.name}"?`)) {
    await deleteCategoryMutation.mutateAsync(category.id)
  }
}

// Category table handlers
const handleCategoryPageChange = (page: number) => {
  categoryPage.value = page
}

const handleCategoryItemsPerPageChange = (perPage: number) => {
  categoryFilters.value.per_page = perPage
  categoryPage.value = 1
}

const handleCategorySearch = (search: string) => {
  categoryFilters.value.search = search
  categoryPage.value = 1
}

// Auto-generate slug from name for categories
watch(() => categoryForm.value.name, (newName) => {
  if (!categoryForm.value.id) {
    categoryForm.value.slug = newName.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '')
  }
})
</script>

<style scoped>
.amenity-card {
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
}

.amenity-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.amenity-icon {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-tabs .nav-link {
  cursor: pointer;
}

.page-link {
  cursor: pointer;
}

/* Compact dropdown styling */
.dropdown-menu-sm {
  min-width: 8rem;
  font-size: 0.875rem;
}

.dropdown-item-sm {
  padding: 0.4rem 1rem;
  font-size: 0.875rem;
}

.dropdown-item-sm i {
  font-size: 0.875rem;
  width: 16px;
}

.dropstart .btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.dropstart .btn:focus {
  box-shadow: none;
}

.dropstart .btn:hover {
  background-color: #e9ecef;
}
</style>

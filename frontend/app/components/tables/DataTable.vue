<template>
  <div class="card">
    <div class="card-header pb-0" v-if="title || $slots.header">
      <slot name="header">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <h4>{{ title }}</h4>
            <span v-if="description" class="text-muted">{{ description }}</span>
          </div>
          <slot name="header-actions"></slot>
        </div>
      </slot>
    </div>
    <div class="card-body">
      <div class="table-responsive data-table custom-scrollbar">
        <!-- Top Controls Section -->
        <div class="mb-3 d-flex justify-content-between align-items-center flex-wrap gap-2">
          <!-- Left side: Rows per page -->
          <div class="d-flex align-items-center gap-2">
            <div class="d-flex align-items-center">
              <label class="col-form-label me-2 mb-0 text-nowrap">Show</label>
              <select 
                class="form-select form-select-sm" 
                v-model="localItemsPerPage"
                style="width: auto; min-width: 70px;"
              >
                <option v-for="option in rowsPerPageOptions" :key="option" :value="option">
                  {{ option }}
                </option>
              </select>
              <span class="col-form-label ms-2 mb-0 text-nowrap">entries</span>
            </div>
          </div>
          
          <!-- Right side: Search + Filter Toggle -->
          <div class="d-flex align-items-center gap-2">
            <div class="d-flex align-items-center" v-if="searchable">
              <label for="table-search" class="col-form-label me-2 mb-0 text-nowrap">Search:</label>
              <input 
                id="table-search" 
                type="text" 
                class="form-control form-control-sm" 
                v-model="localSearch"
                :placeholder="searchPlaceholder"
                style="min-width: 200px;"
              />
            </div>
            
            <button 
              v-if="hasFilters" 
              class="btn btn-sm btn-outline-secondary"
              @click="showFilters = !showFilters"
            >
              <i class="fa fa-filter me-1"></i>
              {{ showFilters ? 'Hide' : 'Show' }} Filters
            </button>
          </div>
        </div>

        <!-- Filters Section (Collapsible) -->
        <div v-if="hasFilters && showFilters" class="mb-3 p-3 bg-light rounded">
          <div class="row g-2">
            <div 
              v-for="header in filterableHeaders" 
              :key="`filter-${header.key}`"
              class="col-md-3"
            >
              <label class="form-label small fw-bold">
                {{ header.title }}
              </label>
              <input 
                type="text" 
                class="form-control form-control-sm" 
                :placeholder="`Filter by ${header.title}`"
                v-model="columnFilters[header.key]"
              />
            </div>
          </div>
          <div class="mt-2 d-flex gap-2">
            <button 
              class="btn btn-sm btn-primary"
              @click="applyFilters"
            >
              <i class="fa fa-check me-1"></i>Apply Filters
            </button>
            <button 
              class="btn btn-sm btn-secondary"
              @click="clearFilters"
            >
              <i class="fa fa-times me-1"></i>Clear
            </button>
          </div>
        </div>

        <!-- Bootstrap Table -->
        <div class="table-responsive">
          <table class="table table-striped table-bordered table-hover">
            <thead>
              <tr>
                <th 
                  v-for="header in headers" 
                  :key="header.key" 
                  :style="header.width ? `width: ${header.width}px` : ''"
                  :class="header.align ? `text-${header.align}` : ''"
                >
                  {{ header.title }}
                </th>
              </tr>
            </thead>
            <tbody v-if="loading">
              <tr>
                <td :colspan="headers.length" class="text-center py-4">
                  <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                  Loading...
                </td>
              </tr>
            </tbody>
            <tbody v-else-if="!displayItems.length">
              <tr>
                <td :colspan="headers.length" class="text-center text-muted py-4">
                  <i class="fa fa-inbox fa-2x mb-2 d-block"></i>
                  No data available
                </td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr v-for="(item, index) in displayItems" :key="item.id || index">
                <td 
                  v-for="header in headers" 
                  :key="header.key"
                  :class="header.align ? `text-${header.align}` : ''"
                >
                  <!-- Check if there's a custom slot for this column -->
                  <slot 
                    v-if="$slots[`cell-${header.key}`]" 
                    :name="`cell-${header.key}`" 
                    :row="{ original: item, index }"
                  />
                  <!-- Otherwise show the value -->
                  <template v-else>
                    {{ getNestedValue(item, header.key) }}
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Custom Pagination -->
        <div class="d-flex justify-content-between align-items-center mt-3 flex-wrap gap-2">
          <div class="text-muted" v-if="showPaginationInfo">
            Showing {{ paginationFrom }} to {{ paginationTo }} of {{ totalItems }} entries
          </div>
          
          <ul class="pagination pagination-primary mb-0" v-if="totalPages > 1">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" @click.prevent="goToPage(currentPage - 1)" aria-label="Previous">
                <span aria-hidden="true">&laquo;</span>
              </a>
            </li>
            
            <template v-for="page in displayedPages" :key="page">
              <li 
                v-if="page !== '...'" 
                class="page-item" 
                :class="{ active: page === currentPage }"
              >
                <a class="page-link" @click.prevent="goToPage(page as number)">{{ page }}</a>
              </li>
              <li v-else class="page-item disabled">
                <span class="page-link">...</span>
              </li>
            </template>
            
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <a class="page-link" @click.prevent="goToPage(currentPage + 1)" aria-label="Next">
                <span aria-hidden="true">&raquo;</span>
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title?: string
  description?: string
  headers: any[]
  items: any[]
  loading?: boolean
  itemsPerPage?: number
  totalItems?: number
  currentPage?: number
  searchable?: boolean
  searchPlaceholder?: string
  showPaginationInfo?: boolean
  tableClass?: string
  rowsPerPageOptions?: number[]
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  itemsPerPage: 10,
  currentPage: 1,
  searchable: true,
  searchPlaceholder: 'Search...',
  showPaginationInfo: true,
  tableClass: '',
  rowsPerPageOptions: () => [5, 10, 25, 50, 100],
})

const emit = defineEmits<{
  'update:currentPage': [page: number]
  'update:search': [search: string]
  'update:itemsPerPage': [perPage: number]
  'update:columnFilters': [filters: Record<string, string>]
}>()

const localSearch = ref('')
const localItemsPerPage = ref(props.itemsPerPage)
const columnFilters = ref<Record<string, string>>({})
const showFilters = ref(false)
const searchDebounceTimer = ref<NodeJS.Timeout | null>(null)

// Check if any column has filterable enabled
const hasFilters = computed(() => {
  return props.headers.some(h => h.filterable)
})

// Get only filterable headers
const filterableHeaders = computed(() => {
  return props.headers.filter(h => h.filterable)
})

// Display items for VDataTable
const displayItems = computed(() => {
  // For server-side pagination, return items as is
  if (props.totalItems) {
    return props.items
  }
  
  // For client-side, VDataTable handles pagination
  return props.items
})

const totalPages = computed(() => {
  const total = props.totalItems || props.items.length
  if (total === 0) return 1
  return Math.ceil(total / localItemsPerPage.value)
})

const paginationFrom = computed(() => {
  if (!props.items.length) return 0
  return (props.currentPage - 1) * localItemsPerPage.value + 1
})

const paginationTo = computed(() => {
  const to = props.currentPage * localItemsPerPage.value
  const total = props.totalItems || props.items.length
  return to > total ? total : to
})

const displayedPages = computed(() => {
  const pages: (number | string)[] = []
  const total = totalPages.value
  const current = props.currentPage
  
  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    pages.push(1)
    
    if (current > 3) {
      pages.push('...')
    }
    
    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)
    
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
    
    if (current < total - 2) {
      pages.push('...')
    }
    
    pages.push(total)
  }
  
  return pages
})

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    emit('update:currentPage', page)
  }
}

function applyFilters() {
  emit('update:columnFilters', { ...columnFilters.value })
  // Reset to page 1 when applying filters
  emit('update:currentPage', 1)
}

function clearFilters() {
  columnFilters.value = {}
  emit('update:columnFilters', {})
  emit('update:currentPage', 1)
}

watch(localSearch, (value) => {
  // Clear existing timeout
  if (searchDebounceTimer.value) {
    clearTimeout(searchDebounceTimer.value)
  }
  
  // If search is empty, clear immediately without debounce
  if (value.trim() === '') {
    emit('update:search', '')
    return
  }
  
  // Set new timeout for debounced search
  searchDebounceTimer.value = setTimeout(() => {
    emit('update:search', value)
  }, 500) // 500ms delay after user stops typing
})

watch(localItemsPerPage, (value) => {
  emit('update:itemsPerPage', value)
  // Reset to page 1 when changing items per page
  emit('update:currentPage', 1)
})

// Helper to get nested values (e.g., "user.name")
function getNestedValue(obj: any, path: string) {
  return path.split('.').reduce((current, key) => current?.[key], obj)
}

// Cleanup on unmount
onBeforeUnmount(() => {
  if (searchDebounceTimer.value) {
    clearTimeout(searchDebounceTimer.value)
  }
})
</script>

<style scoped>
.table-responsive {
  overflow-x: auto;
}

.pagination {
  margin-bottom: 0;
}

.page-link {
  cursor: pointer;
}

.page-item.disabled .page-link {
  cursor: not-allowed;
}

/* Filter section styling */
.bg-light {
  background-color: #f8f9fa !important;
}

.bg-light label {
  margin-bottom: 0.25rem;
  color: #495057;
}

/* Table enhancements */
.table-hover tbody tr {
  transition: background-color 0.2s ease;
}

.table-hover tbody tr:hover {
  background-color: #e9ecef !important;
}

/* Dropdown action button */
:deep(.dropdown-toggle::after) {
  vertical-align: middle;
}

:deep(.dropdown-menu) {
  min-width: 8rem;
  z-index: 1050;
}

:deep(.dropstart .dropdown-menu) {
  margin-right: 0.125rem;
}

:deep(.dropstart .btn) {
  border-radius: 0.25rem;
}

/* Prevent dropdown from causing horizontal scroll */
.table-responsive {
  overflow-x: auto;
  position: relative;
}

/* Empty state icon */
.fa-inbox {
  opacity: 0.3;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .d-flex.justify-content-between {
    flex-direction: column;
    align-items: flex-start !important;
  }
  
  .d-flex.justify-content-between > div {
    width: 100%;
    justify-content: space-between;
  }
  
  .bg-light .row {
    margin: 0;
  }
  
  .bg-light .col-md-3 {
    margin-bottom: 0.5rem;
  }
}
</style>

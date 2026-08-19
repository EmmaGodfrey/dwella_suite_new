<template>
  <div>
    <BreadCrumbs title="Listings Management" main="Admin" />
    
    <div class="container-fluid">
      <!-- Statistics Cards -->
      <div class="row mb-4">
        <div class="col-xl-2 col-sm-6">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Total</p>
                  <h4 class="mb-0">{{ statistics.total }}</h4>
                </div>
                <div class="bg-light-primary p-3 rounded">
                  <i class="fa fa-home fa-2x text-primary"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-xl-2 col-sm-6">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Pending</p>
                  <h4 class="mb-0 text-warning">{{ statistics.pending }}</h4>
                </div>
                <div class="bg-light-warning p-3 rounded">
                  <i class="fa fa-clock-o fa-2x text-warning"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-xl-2 col-sm-6">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Published</p>
                  <h4 class="mb-0 text-success">{{ statistics.published }}</h4>
                </div>
                <div class="bg-light-success p-3 rounded">
                  <i class="fa fa-check-circle fa-2x text-success"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-xl-2 col-sm-6">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Draft</p>
                  <h4 class="mb-0">{{ statistics.draft }}</h4>
                </div>
                <div class="bg-light-secondary p-3 rounded">
                  <i class="fa fa-file-text-o fa-2x text-secondary"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-xl-2 col-sm-6">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Rejected</p>
                  <h4 class="mb-0 text-danger">{{ statistics.rejected }}</h4>
                </div>
                <div class="bg-light-danger p-3 rounded">
                  <i class="fa fa-times-circle fa-2x text-danger"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-xl-2 col-sm-6">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <p class="text-muted mb-1">Archived</p>
                  <h4 class="mb-0">{{ statistics.archived }}</h4>
                </div>
                <div class="bg-light-info p-3 rounded">
                  <i class="fa fa-archive fa-2x text-info"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters and Search -->
      <div class="row mb-4">
        <div class="col-sm-12">
          <div class="card">
            <div class="card-body">
              <div class="row g-3">
                <div class="col-lg-3 col-md-4">
                  <input 
                    type="text" 
                    class="form-control" 
                    placeholder="Search listings..."
                    v-model="filters.search"
                  />
                </div>
                <div class="col-lg-2 col-md-4">
                  <select class="form-select" v-model="filters['filter[status]']">
                    <option :value="undefined">All Statuses</option>
                    <option value="pending">Pending</option>
                    <option value="published">Published</option>
                    <option value="draft">Draft</option>
                    <option value="rejected">Rejected</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
                <div class="col-lg-2 col-md-4">
                  <select class="form-select" v-model="filters.sort">
                    <option :value="undefined">Default Sort</option>
                    <option value="-created_at">Newest First</option>
                    <option value="created_at">Oldest First</option>
                    <option value="price_amount_minor">Price: Low to High</option>
                    <option value="-price_amount_minor">Price: High to Low</option>
                    <option value="title">Title: A-Z</option>
                    <option value="-title">Title: Z-A</option>
                  </select>
                </div>
                <div class="col-lg-1 col-md-6">
                  <select class="form-select" v-model="filters.per_page">
                    <option :value="9">9</option>
                    <option :value="18">18</option>
                    <option :value="36">36</option>
                    <option :value="54">54</option>
                  </select>
                </div>
                <div class="col-lg-2 col-md-6">
                  <button class="btn btn-secondary w-100" @click="clearFilters">
                    <i class="fa fa-refresh me-1"></i>Clear Filters
                  </button>
                </div>
                <div class="col-lg-2 col-md-6">
                  <NuxtLink to="/listings/create" class="btn btn-primary w-100">
                    <i class="fa fa-plus me-1"></i>Add Listing
                  </NuxtLink>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Listings Grid -->
      <div class="row">
        <div class="col-sm-12">
          <div v-if="isLoading" class="text-center py-5">
            <div class="spinner-border spinner-border-lg" role="status"></div>
            <p class="mt-3">Loading listings...</p>
          </div>

          <div v-else-if="!listings.length" class="card">
            <div class="card-body text-center py-5 text-muted">
              <i class="fa fa-inbox fa-4x mb-3 d-block opacity-25"></i>
              <h5>No listings found</h5>
              <p>Try adjusting your filters or search criteria</p>
            </div>
          </div>

          <div v-else class="row g-3">
            <div 
              v-for="listing in listings" 
              :key="listing.id"
              class="col-xxl-4 col-xl-6 col-lg-6 col-md-6"
            >
              <div class="card listing-card h-100">
                <!-- Image Carousel -->
                <div :id="`carousel-${listing.id}`" class="carousel slide listing-carousel" data-bs-ride="false">
                  <div class="carousel-inner">
                    <div 
                      v-if="listing.images && listing.images.length"
                      v-for="(image, index) in listing.images" 
                      :key="image.id"
                      class="carousel-item"
                      :class="{ active: index === 0 }"
                    >
                      <div class="listing-image" :style="{ backgroundImage: `url(${image.url || '/images/placeholder.jpg'})` }"></div>
                    </div>
                    <div v-else class="carousel-item active">
                      <div class="listing-image" style="background-image: url('/images/placeholder.jpg')"></div>
                    </div>
                  </div>
                  <button 
                    v-if="listing.images && listing.images.length > 1"
                    class="carousel-control-prev" 
                    type="button" 
                    :data-bs-target="`#carousel-${listing.id}`" 
                    data-bs-slide="prev"
                  >
                    <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                    <span class="visually-hidden">Previous</span>
                  </button>
                  <button 
                    v-if="listing.images && listing.images.length > 1"
                    class="carousel-control-next" 
                    type="button" 
                    :data-bs-target="`#carousel-${listing.id}`"  
                    data-bs-slide="next"
                  >
                    <span class="carousel-control-next-icon" aria-hidden="true"></span>
                    <span class="visually-hidden">Next</span>
                  </button>

                  <!-- Status Badge -->
                  <span class="badge position-absolute top-0 end-0 m-2" :class="getStatusBadgeClass(listing.status)">
                    {{ listing.status }}
                  </span>
                </div>

                <div class="card-body">
                  <!-- Title and Price -->
                  <div class="d-flex justify-content-between align-items-start mb-2">
                    <NuxtLink :to="`/listings/${listing.id}`" class="mb-0 listing-title text-decoration-none text-dark">
                      <h5 class="mb-0 listing-title">{{ listing.title }}</h5>
                    </NuxtLink>
                    <h5 class="text-primary mb-0 ms-2 text-nowrap">
                      {{ formatPrice(listing.price, listing.currency) }}
                      <small class="text-muted">/{{ listing.price_period }}</small>
                    </h5>
                  </div>

                  <!-- Property Type and Location -->
                  <p class="text-muted small mb-2">
                    <i class="fa fa-building-o me-1"></i>{{ listing.property_type?.name || 'N/A' }}
                    <span class="mx-2">•</span>
                    <i class="fa fa-map-marker me-1"></i>{{ getLocationDisplay(listing) }}
                  </p>

                  <!-- Description -->
                  <p class="listing-description mb-3">
                    {{ truncateText(listing.description, 100) }}
                  </p>

                  <!-- Amenities -->
                  <div v-if="listing.amenities && listing.amenities.length" class="amenities-list mb-3">
                    <span 
                      v-for="(amenity, index) in listing.amenities.slice(0, MAX_AMENITIES_DISPLAY)" 
                      :key="amenity.id"
                      class="amenity-badge"
                      :title="amenity.name"
                    >
                      <i v-if="amenity.icon" :class="amenity.icon"></i>
                      <i v-else class="fa fa-check"></i>
                    </span>
                    <span 
                      v-if="listing.amenities.length > MAX_AMENITIES_DISPLAY" 
                      class="amenity-badge extra-count"
                    >
                      +{{ listing.amenities.length - MAX_AMENITIES_DISPLAY }}
                    </span>
                  </div>

                  <!-- Organization and Creator -->
                  <div class="small text-muted mb-3">
                    <div>
                      <strong>Organization:</strong> {{ listing.organization?.name || 'N/A' }}
                    </div>
                    <div>
                      <strong>Posted by:</strong> {{ listing.creator?.full_name || 'N/A' }}
                    </div>
                  </div>

                  <!-- Actions -->
                  <div class="d-flex gap-2">
                    <button 
                      v-if="listing.status === 'pending'"
                      class="btn btn-sm btn-success flex-fill"
                      @click="handleApprove(listing)"
                      :disabled="approveMutation.isPending.value"
                    >
                      <i class="fa fa-check me-1"></i>Approve
                    </button>
                    <button 
                      v-if="listing.status === 'pending'"
                      class="btn btn-sm btn-danger flex-fill"
                      @click="openRejectModal(listing)"
                    >
                      <i class="fa fa-times me-1"></i>Reject
                    </button>
                    <button 
                      v-if="['draft', 'approved'].includes(listing.status)"
                      class="btn btn-sm btn-primary flex-fill"
                      @click="handlePublish(listing)"
                      :disabled="publishMutation.isPending.value"
                    >
                      <i class="fa fa-globe me-1"></i>Publish
                    </button>
                    <button 
                      v-if="listing.status !== 'archived'"
                      class="btn btn-sm btn-warning flex-fill"
                      @click="handleArchive(listing)"
                      :disabled="archiveMutation.isPending.value"
                    >
                      <i class="fa fa-archive me-1"></i>Archive
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-danger"
                      @click="handleDelete(listing)"
                      :disabled="deleteMutation.isPending.value"
                    >
                      <i class="fa fa-trash"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Pagination -->
          <div v-if="pagination.lastPage > 1" class="d-flex justify-content-center mt-4">
            <ul class="pagination pagination-primary">
              <li class="page-item" :class="{ disabled: currentPage === 1 }">
                <a class="page-link" @click.prevent="currentPage = currentPage - 1">
                  <span>&laquo;</span>
                </a>
              </li>
              <li 
                v-for="page in displayedPages" 
                :key="page"
                class="page-item" 
                :class="{ active: page === currentPage, disabled: page === '...' }"
              >
                <a v-if="page !== '...'" class="page-link" @click.prevent="currentPage = page as number">{{ page }}</a>
                <span v-else class="page-link">...</span>
              </li>
              <li class="page-item" :class="{ disabled: currentPage === pagination.lastPage }">
                <a class="page-link" @click.prevent="currentPage = currentPage + 1">
                  <span>&raquo;</span>
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Reject Modal -->
    <div class="modal fade" id="rejectModal" tabindex="-1" ref="rejectModalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Reject Listing</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="handleReject">
            <div class="modal-body">
              <p><strong>{{ selectedListing?.title }}</strong></p>
              <div class="mb-3">
                <label class="form-label">Rejection Reason</label>
                <textarea 
                  class="form-control" 
                  v-model="rejectReason"
                  rows="4"
                  :class="rejectMutation.getFieldError('reason') ? 'is-invalid' : ''"
                  required
                  placeholder="Explain why this listing is being rejected..."
                ></textarea>
                <div class="invalid-feedback" v-if="rejectMutation.getFieldError('reason')">
                  {{ rejectMutation.getFieldError('reason') }}
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-danger" :disabled="rejectMutation.isPending.value">
                <span v-if="rejectMutation.isPending.value" class="spinner-border spinner-border-sm me-2"></span>
                Reject Listing
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Listing, ListingsListParams } from '~/types/listing'
import BreadCrumbs from '~/components/breadCrumbs.vue'
import { Modal } from 'bootstrap'

definePageMeta({
  name: 'listings',
  path: '/listings',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
const listingsStore = useListingsStore()
const { 
  useFetchListingsQuery,
  useFetchStatisticsQuery,
  useApproveListingMutation,
  useRejectListingMutation,
  usePublishListingMutation,
  useArchiveListingMutation,
  useDeleteListingMutation,
} = useListings()

// Set breadcrumbs
setBreadcrumbs([
  { title: 'Home', url: '/dashboard' },
  { title: 'Listings', active: true },
])

// Constants
const MAX_AMENITIES_DISPLAY = 6

// Filters
const currentPage = ref(1)
const filters = ref<ListingsListParams>({
  page: 1,
  per_page: 9,
  search: '',
  sort: '-created_at',
})

const listingsParams = computed(() => ({
  ...filters.value,
  page: currentPage.value,
}))

// Fetch data
const { data: listingsData, isLoading } = useFetchListingsQuery(listingsParams)
const { data: statsData } = useFetchStatisticsQuery()

const listings = computed(() => listingsStore.listings || [])
const statistics = computed(() => listingsStore.statistics)
const pagination = computed(() => listingsStore.pagination)

// Pagination
const displayedPages = computed(() => {
  const pages: (number | string)[] = []
  const total = pagination.value.lastPage
  const current = currentPage.value
  
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

// Modals
const rejectModalEl = ref<HTMLElement | null>(null)
let rejectModalInstance: Modal | null = null

const selectedListing = ref<Listing | null>(null)
const rejectReason = ref('')

onMounted(() => {
  if (rejectModalEl.value) {
    rejectModalInstance = new Modal(rejectModalEl.value)
  }
})

onBeforeUnmount(() => {
  rejectModalInstance?.dispose()
})

// Mutations
const approveMutation = useApproveListingMutation()
const rejectMutation = useRejectListingMutation()
const publishMutation = usePublishListingMutation()
const archiveMutation = useArchiveListingMutation()
const deleteMutation = useDeleteListingMutation()

// Handlers
const handleApprove = async (listing: Listing) => {
  if (confirm(`Approve listing "${listing.title}"?`)) {
    await approveMutation.mutateAsync(listing.id)
  }
}

const openRejectModal = (listing: Listing) => {
  selectedListing.value = listing
  rejectReason.value = ''
  rejectMutation.reset()
  rejectModalInstance?.show()
}

const handleReject = async () => {
  if (selectedListing.value) {
    try {
      await rejectMutation.mutateAsync({
        id: selectedListing.value.id,
        reason: rejectReason.value,
      })
      rejectModalInstance?.hide()
    } catch (error) {
      // Error handled in mutation
    }
  }
}

const handlePublish = async (listing: Listing) => {
  if (confirm(`Publish listing "${listing.title}"?`)) {
    await publishMutation.mutateAsync(listing.id)
  }
}

const handleArchive = async (listing: Listing) => {
  if (confirm(`Archive listing "${listing.title}"?`)) {
    await archiveMutation.mutateAsync(listing.id)
  }
}

const handleDelete = async (listing: Listing) => {
  if (confirm(`Delete listing "${listing.title}" permanently? This action cannot be undone.`)) {
    await deleteMutation.mutateAsync(listing.id)
  }
}

const clearFilters = () => {
  filters.value = {
    page: 1,
    per_page: 9,
    search: '',
    sort: '-created_at',
  }
  currentPage.value = 1
}

// Utility functions
const getStatusBadgeClass = (status: string) => {
  const classes: Record<string, string> = {
    draft: 'badge-secondary',
    pending: 'badge-warning',
    approved: 'badge-info',
    published: 'badge-success',
    rejected: 'badge-danger',
    archived: 'badge-dark',
  }
  return classes[status] || 'badge-secondary'
}

const formatPrice = (price: number, currency: string) => {
  return new Intl.NumberFormat('en-ZM', {
    style: 'currency',
    currency: currency || 'ZMW',
  }).format(price)
}

const getLocationDisplay = (listing: Listing) => {
  const parts = []
  if (listing.constituency?.name) parts.push(listing.constituency.name)
  if (listing.district?.name) parts.push(listing.district.name)
  if (listing.province?.name) parts.push(listing.province.name)
  return parts.join(', ') || 'Location not specified'
}

const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// Watch filters for debounced search
watch(() => filters.value.search, () => {
  currentPage.value = 1
})

watch(() => filters.value['filter[status]'], () => {
  currentPage.value = 1
})
</script>

<style scoped>
.listing-card {
  transition: all 0.3s ease;
  overflow: hidden;
}

.listing-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.listing-carousel {
  position: relative;
  height: 250px;
  background: #f8f9fa;
}

.listing-image {
  width: 100%;
  height: 250px;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.carousel-control-prev,
.carousel-control-next {
  width: 40px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.listing-card:hover .carousel-control-prev,
.listing-card:hover .carousel-control-next {
  opacity: 0.8;
}

.carousel-control-prev:hover,
.carousel-control-next:hover {
  opacity: 1 !important;
}

.listing-title {
  font-size: 1.1rem;
  line-height: 1.3;
  max-height: 2.6em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.listing-description {
  font-size: 0.9rem;
  color: #6c757d;
  line-height: 1.5;
  max-height: 4.5em;
  overflow: hidden;
}

.amenities-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.amenity-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 50%;
  font-size: 14px;
  color: #495057;
  transition: all 0.2s ease;
}

.amenity-badge:hover {
  background: #e9ecef;
  transform: scale(1.1);
}

.amenity-badge.extra-count {
  font-size: 11px;
  font-weight: 600;
  background: var(--theme-default);
  color: white;
  border-color: var(--theme-default);
}

.page-link {
  cursor: pointer;
}

/* Status badge colors */
.badge-success { background-color: #51bb25; }
.badge-warning { background-color: #f8d62b; color: #000; }
.badge-danger { background-color: #dc3545; }
.badge-info { background-color: #4099ff; }
.badge-secondary { background-color: #6c757d; }
.badge-dark { background-color: #343a40; }
</style>

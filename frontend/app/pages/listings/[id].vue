<template>
  <div>
    <BreadCrumbs title="Listing Detail" main="Listings" />

    <div class="container-fluid">
      <!-- Loading -->
      <div v-if="isLoading" class="text-center py-5">
        <div class="spinner-border spinner-border-lg" role="status"></div>
        <p class="mt-3">Loading listing...</p>
      </div>

      <!-- Error -->
      <div v-else-if="isError" class="card">
        <div class="card-body text-center py-5 text-danger">
          <i class="fa fa-exclamation-circle fa-4x mb-3 d-block opacity-50"></i>
          <h5>Failed to load listing</h5>
          <NuxtLink to="/listings" class="btn btn-secondary mt-3">
            <i class="fa fa-arrow-left me-2"></i>Back to Listings
          </NuxtLink>
        </div>
      </div>

      <template v-else-if="listing">
        <!-- Header row: back + status + actions -->
        <div class="row mb-4">
          <div class="col-sm-12">
            <div class="card">
              <div class="card-body">
                <div class="d-flex flex-wrap justify-content-between align-items-center gap-3">
                  <div class="d-flex align-items-center gap-3">
                    <NuxtLink to="/listings" class="btn btn-outline-secondary btn-sm">
                      <i class="fa fa-arrow-left me-1"></i>Back
                    </NuxtLink>
                    <div>
                      <h4 class="mb-1">{{ listing.title }}</h4>
                      <span class="badge" :class="getStatusBadgeClass(listing.status)">
                        {{ listing.status }}
                      </span>
                    </div>
                  </div>

                  <!-- Moderation actions -->
                  <div class="d-flex flex-wrap gap-2">
                    <button
                      v-if="listing.status === 'pending'"
                      class="btn btn-success"
                      @click="handleApprove"
                      :disabled="approveMutation.isPending.value"
                    >
                      <span v-if="approveMutation.isPending.value" class="spinner-border spinner-border-sm me-1"></span>
                      <i v-else class="fa fa-check me-1"></i>Approve
                    </button>
                    <button
                      v-if="listing.status === 'pending'"
                      class="btn btn-danger"
                      @click="openRejectModal"
                    >
                      <i class="fa fa-times me-1"></i>Reject
                    </button>
                    <button
                      v-if="['draft', 'approved'].includes(listing.status)"
                      class="btn btn-primary"
                      @click="handlePublish"
                      :disabled="publishMutation.isPending.value"
                    >
                      <span v-if="publishMutation.isPending.value" class="spinner-border spinner-border-sm me-1"></span>
                      <i v-else class="fa fa-globe me-1"></i>Publish
                    </button>
                    <button
                      v-if="listing.status !== 'archived'"
                      class="btn btn-warning"
                      @click="handleArchive"
                      :disabled="archiveMutation.isPending.value"
                    >
                      <span v-if="archiveMutation.isPending.value" class="spinner-border spinner-border-sm me-1"></span>
                      <i v-else class="fa fa-archive me-1"></i>Archive
                    </button>
                    <button
                      class="btn btn-outline-danger"
                      @click="handleDelete"
                      :disabled="deleteMutation.isPending.value"
                    >
                      <span v-if="deleteMutation.isPending.value" class="spinner-border spinner-border-sm me-1"></span>
                      <i v-else class="fa fa-trash me-1"></i>Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="row">
          <!-- Left: Images + Details -->
          <div class="col-xl-8">
            <!-- Image Gallery -->
            <div class="card mb-4">
              <div class="card-body p-0">
                <div v-if="listing.images && listing.images.length">
                  <div :id="`carousel-detail-${listing.id}`" class="carousel slide" data-bs-ride="false">
                    <div class="carousel-inner">
                      <div
                        v-for="(image, index) in listing.images"
                        :key="image.id"
                        class="carousel-item"
                        :class="{ active: index === 0 }"
                      >
                        <div class="detail-image" :style="{ backgroundImage: `url(${image.url || '/images/placeholder.jpg'})` }">
                          <span v-if="image.is_thumbnail" class="badge bg-primary position-absolute top-0 start-0 m-3">
                            <i class="fa fa-star me-1"></i>Thumbnail
                          </span>
                        </div>
                      </div>
                    </div>
                    <button
                      v-if="listing.images.length > 1"
                      class="carousel-control-prev"
                      type="button"
                      :data-bs-target="`#carousel-detail-${listing.id}`"
                      data-bs-slide="prev"
                    >
                      <span class="carousel-control-prev-icon"></span>
                    </button>
                    <button
                      v-if="listing.images.length > 1"
                      class="carousel-control-next"
                      type="button"
                      :data-bs-target="`#carousel-detail-${listing.id}`"
                      data-bs-slide="next"
                    >
                      <span class="carousel-control-next-icon"></span>
                    </button>
                    <!-- Image count badge -->
                    <span class="badge bg-dark position-absolute bottom-0 end-0 m-3">
                      {{ listing.images.length }} photo{{ listing.images.length !== 1 ? 's' : '' }}
                    </span>
                  </div>

                  <!-- Thumbnail strip -->
                  <div v-if="listing.images.length > 1" class="thumbnail-strip p-3">
                    <div
                      v-for="(image, index) in listing.images"
                      :key="image.id"
                      class="thumbnail-item"
                      :data-bs-target="`#carousel-detail-${listing.id}`"
                      :data-bs-slide-to="index"
                    >
                      <div class="thumbnail-img" :style="{ backgroundImage: `url(${image.url || '/images/placeholder.jpg'})` }"></div>
                    </div>
                  </div>
                </div>

                <div v-else class="detail-image-placeholder d-flex align-items-center justify-content-center">
                  <div class="text-center text-muted">
                    <i class="fa fa-image fa-4x mb-3 opacity-25 d-block"></i>
                    <p>No images uploaded</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Description -->
            <div class="card mb-4">
              <div class="card-header pb-0">
                <h5 class="mb-0"><i class="fa fa-file-text-o me-2"></i>Description</h5>
              </div>
              <div class="card-body">
                <p class="mb-0" style="white-space: pre-wrap;">{{ listing.description }}</p>
              </div>
            </div>

            <!-- Rejection reason (when rejected) -->
            <div v-if="listing.status === 'rejected' && listing.rejection_reason" class="card mb-4 border-danger">
              <div class="card-header pb-0 bg-light-danger">
                <h5 class="mb-0 text-danger"><i class="fa fa-times-circle me-2"></i>Rejection Reason</h5>
              </div>
              <div class="card-body">
                <p class="mb-0 text-danger">{{ listing.rejection_reason }}</p>
              </div>
            </div>

            <!-- Amenities -->
            <div v-if="listing.amenities && listing.amenities.length" class="card mb-4">
              <div class="card-header pb-0">
                <h5 class="mb-0"><i class="fa fa-th me-2"></i>Amenities ({{ listing.amenities.length }})</h5>
              </div>
              <div class="card-body">
                <div class="amenities-grid">
                  <div
                    v-for="amenity in listing.amenities"
                    :key="amenity.id"
                    class="amenity-item"
                    :title="amenity.name"
                  >
                    <div class="amenity-icon-wrap">
                      <i v-if="amenity.icon" :class="amenity.icon"></i>
                      <i v-else class="fa fa-check"></i>
                    </div>
                    <span class="amenity-label">{{ amenity.name }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right: Meta info -->
          <div class="col-xl-4">
            <!-- Pricing & type -->
            <div class="card mb-4">
              <div class="card-header pb-0">
                <h5 class="mb-0"><i class="fa fa-info-circle me-2"></i>Listing Info</h5>
              </div>
              <div class="card-body">
                <ul class="list-group list-group-flush">
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Price</span>
                    <strong class="text-primary">
                      {{ formatPrice(listing.price, listing.currency) }}
                      <small class="text-muted fw-normal">/{{ listing.price_period }}</small>
                    </strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Property Type</span>
                    <strong>{{ listing.property_type?.name || 'N/A' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Status</span>
                    <span class="badge" :class="getStatusBadgeClass(listing.status)">{{ listing.status }}</span>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Created</span>
                    <strong>{{ formatDate(listing.created_at) }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Last Updated</span>
                    <strong>{{ formatDate(listing.updated_at) }}</strong>
                  </li>
                </ul>
              </div>
            </div>

            <!-- Location -->
            <div class="card mb-4">
              <div class="card-header pb-0">
                <h5 class="mb-0"><i class="fa fa-map-marker me-2"></i>Location</h5>
              </div>
              <div class="card-body">
                <ul class="list-group list-group-flush">
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Province</span>
                    <strong>{{ listing.province?.name || 'N/A' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">District</span>
                    <strong>{{ listing.district?.name || 'N/A' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Constituency</span>
                    <strong>{{ listing.constituency?.name || 'N/A' }}</strong>
                  </li>
                  <li v-if="listing.address_line" class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Address</span>
                    <strong class="text-end" style="max-width: 60%;">{{ listing.address_line }}</strong>
                  </li>
                  <li v-if="listing.location_text" class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Description</span>
                    <strong class="text-end" style="max-width: 60%;">{{ listing.location_text }}</strong>
                  </li>
                  <li v-if="listing.latitude && listing.longitude" class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Coordinates</span>
                    <strong>{{ listing.latitude }}, {{ listing.longitude }}</strong>
                  </li>
                </ul>
              </div>
            </div>

            <!-- Organization -->
            <div class="card mb-4">
              <div class="card-header pb-0">
                <h5 class="mb-0"><i class="fa fa-building-o me-2"></i>Organization</h5>
              </div>
              <div class="card-body">
                <ul class="list-group list-group-flush">
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Name</span>
                    <strong>{{ listing.organization?.name || 'N/A' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Org ID</span>
                    <strong>{{ listing.organization_id }}</strong>
                  </li>
                </ul>
              </div>
            </div>

            <!-- Creator -->
            <div class="card mb-4">
              <div class="card-header pb-0">
                <h5 class="mb-0"><i class="fa fa-user-o me-2"></i>Posted By</h5>
              </div>
              <div class="card-body">
                <ul class="list-group list-group-flush">
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Name</span>
                    <strong>{{ listing.creator?.full_name || 'N/A' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">Email</span>
                    <strong>{{ listing.creator?.email || 'N/A' }}</strong>
                  </li>
                  <li class="list-group-item px-0 d-flex justify-content-between">
                    <span class="text-muted">User ID</span>
                    <strong>{{ listing.created_by_user_id }}</strong>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </template>
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
              <p><strong>{{ listing?.title }}</strong></p>
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
import type { Listing } from '~/types/listing'
import BreadCrumbs from '~/components/breadCrumbs.vue'
import { Modal } from 'bootstrap'

definePageMeta({
  name: 'listing-detail',
  path: '/listings/:id',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const route = useRoute()
const router = useRouter()
const listingId = computed(() => Number(route.params.id))

const { setBreadcrumbs } = useBreadcrumbs()
const {
  useFetchListingQuery,
  useApproveListingMutation,
  useRejectListingMutation,
  usePublishListingMutation,
  useArchiveListingMutation,
  useDeleteListingMutation,
} = useListings()

const { data, isLoading, isError } = useFetchListingQuery(listingId)

const listing = computed<Listing | null>(() => {
  const d = data.value as any
  return d?.data ?? d ?? null
})

watch(listing, (l) => {
  if (l) {
    setBreadcrumbs([
      { title: 'Home', url: '/dashboard' },
      { title: 'Listings', url: '/listings' },
      { title: l.title, active: true },
    ])
  }
}, { immediate: true })

// Reject modal
const rejectModalEl = ref<HTMLElement | null>(null)
let rejectModalInstance: Modal | null = null
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

const handleApprove = async () => {
  if (!listing.value) return
  if (confirm(`Approve listing "${listing.value.title}"?`)) {
    await approveMutation.mutateAsync(listing.value.id)
  }
}

const openRejectModal = () => {
  rejectReason.value = ''
  rejectMutation.reset()
  rejectModalInstance?.show()
}

const handleReject = async () => {
  if (!listing.value) return
  try {
    await rejectMutation.mutateAsync({ id: listing.value.id, reason: rejectReason.value })
    rejectModalInstance?.hide()
  } catch {
    // Error handled in mutation
  }
}

const handlePublish = async () => {
  if (!listing.value) return
  if (confirm(`Publish listing "${listing.value.title}"?`)) {
    await publishMutation.mutateAsync(listing.value.id)
  }
}

const handleArchive = async () => {
  if (!listing.value) return
  if (confirm(`Archive listing "${listing.value.title}"?`)) {
    await archiveMutation.mutateAsync(listing.value.id)
  }
}

const handleDelete = async () => {
  if (!listing.value) return
  if (confirm(`Delete listing "${listing.value.title}" permanently? This action cannot be undone.`)) {
    await deleteMutation.mutateAsync(listing.value.id)
    if (!deleteMutation.isError.value) {
      router.push('/listings')
    }
  }
}

// Helpers
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

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('en-ZM', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.detail-image {
  width: 100%;
  height: 400px;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  position: relative;
}

.detail-image-placeholder {
  height: 300px;
  background: #f8f9fa;
}

.thumbnail-strip {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 12px;
  background: #f8f9fa;
}

.thumbnail-item {
  flex-shrink: 0;
  cursor: pointer;
  border-radius: 6px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: border-color 0.2s;
}

.thumbnail-item:hover {
  border-color: var(--theme-default);
}

.thumbnail-img {
  width: 70px;
  height: 55px;
  background-size: cover;
  background-position: center;
}

.amenities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.amenity-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  text-align: center;
  transition: all 0.2s ease;
}

.amenity-item:hover {
  background: #e9ecef;
  transform: translateY(-2px);
}

.amenity-icon-wrap {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: var(--theme-default);
}

.amenity-label {
  font-size: 12px;
  color: #495057;
  line-height: 1.3;
}

/* Status badge colours */
.badge-success  { background-color: #51bb25; }
.badge-warning  { background-color: #f8d62b; color: #000; }
.badge-danger   { background-color: #dc3545; }
.badge-info     { background-color: #4099ff; }
.badge-secondary { background-color: #6c757d; }
.badge-dark     { background-color: #343a40; }
</style>

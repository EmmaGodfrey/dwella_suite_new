<template>
  <div>
    <BreadCrumbs title="Create Listing" main="Listings" />
    
    <div class="container-fluid">
      <div class="row">
        <div class="col-sm-12">
          <div class="card">
            <div class="card-header pb-0">
              <h5>Add New Listing</h5>
              <span class="d-block mt-1 f-m-light">Create a new property listing with detailed information</span>
            </div>
            <div class="card-body">
              <!-- Progress Steps -->
              <div class="wizard-tabs mb-4">
                <button 
                  v-for="step in totalSteps" 
                  :key="step" 
                  type="button" 
                  :class="['wizard-tab', { active: currentStep === step, completed: step < currentStep }]" 
                  @click="goToStep(step)"
                >
                  <span class="step-number">{{ step }}</span>
                  <span class="step-title d-none d-md-block">{{ stepTitles[step - 1] }}</span>
                </button>
              </div>

              <form @submit.prevent="handleSubmit">
                <!-- Step 1: Basic Information -->
                <div v-show="currentStep === 1" class="wizard-step">
                  <h5 class="mb-4">Basic Information</h5>
                  <div class="row">
                    <!-- Organization -->
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Organization (Optional)</label>
                      <select 
                        v-model="form.organization_id" 
                        class="form-select"
                        :class="{ 'is-invalid': getFieldError('organization_id') }"
                      >
                        <option :value="undefined">No Organization (Admin Direct)</option>
                        <option 
                          v-for="org in referenceStore.organizations" 
                          :key="org.id" 
                          :value="org.id"
                        >
                          {{ org.name }}
                        </option>
                      </select>
                      <div v-if="getFieldError('organization_id')" class="invalid-feedback">
                        {{ getFieldError('organization_id') }}
                      </div>
                    </div>

                    <!-- Status -->
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Status <span class="text-danger">*</span></label>
                      <select 
                        v-model="form.status" 
                        class="form-select"
                        :class="{ 'is-invalid': getFieldError('status') }"
                      >
                        <option value="draft">Draft</option>
                        <option value="pending">Pending</option>
                        <option value="published">Published</option>
                        <option value="approved">Approved</option>
                      </select>
                      <div v-if="getFieldError('status')" class="invalid-feedback">
                        {{ getFieldError('status') }}
                      </div>
                    </div>

                    <!-- Title -->
                    <div class="col-md-12 mb-3">
                      <label class="form-label">Title <span class="text-danger">*</span></label>
                      <input 
                        type="text" 
                        v-model="form.title" 
                        class="form-control"
                        :class="{ 'is-invalid': getFieldError('title') }"
                        placeholder="e.g. Luxury 3-Bedroom Apartment in Lusaka"
                      />
                      <div v-if="getFieldError('title')" class="invalid-feedback">
                        {{ getFieldError('title') }}
                      </div>
                    </div>

                    <!-- Description -->
                    <div class="col-md-12 mb-3">
                      <label class="form-label">Description <span class="text-danger">*</span></label>
                      <textarea 
                        v-model="form.description" 
                        class="form-control"
                        :class="{ 'is-invalid': getFieldError('description') }"
                        rows="4"
                        placeholder="Provide a detailed description of the property..."
                      ></textarea>
                      <div v-if="getFieldError('description')" class="invalid-feedback">
                        {{ getFieldError('description') }}
                      </div>
                    </div>

                    <!-- Property Type -->
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Property Type <span class="text-danger">*</span></label>
                      <select 
                        v-model="form.property_type_id" 
                        class="form-select"
                        :class="{ 'is-invalid': getFieldError('property_type_id') }"
                      >
                        <option :value="undefined">Select Property Type</option>
                        <option 
                          v-for="type in referenceStore.propertyTypes" 
                          :key="type.id" 
                          :value="type.id"
                        >
                          {{ type.name }}
                        </option>
                      </select>
                      <div v-if="getFieldError('property_type_id')" class="invalid-feedback">
                        {{ getFieldError('property_type_id') }}
                      </div>
                    </div>

                    <!-- Price Period -->
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Price Period <span class="text-danger">*</span></label>
                      <select 
                        v-model="form.price_period" 
                        class="form-select"
                        :class="{ 'is-invalid': getFieldError('price_period') }"
                      >
                        <option :value="undefined">Select Price Period</option>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                        <option value="yearly">Yearly</option>
                      </select>
                      <div v-if="getFieldError('price_period')" class="invalid-feedback">
                        {{ getFieldError('price_period') }}
                      </div>
                    </div>

                    <!-- Price Amount -->
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Price Amount (in minor units) <span class="text-danger">*</span></label>
                      <input 
                        type="number" 
                        v-model.number="form.price_amount_minor" 
                        class="form-control"
                        :class="{ 'is-invalid': getFieldError('price_amount_minor') }"
                        placeholder="e.g. 450000 (for K4,500.00)"
                        min="0"
                      />
                      <small class="form-text text-muted">Enter amount in ngwee (1 Kwacha = 100 ngwee)</small>
                      <div v-if="getFieldError('price_amount_minor')" class="invalid-feedback">
                        {{ getFieldError('price_amount_minor') }}
                      </div>
                    </div>

                    <!-- Currency -->
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Currency</label>
                      <select 
                        v-model="form.currency" 
                        class="form-select"
                        :class="{ 'is-invalid': getFieldError('currency') }"
                      >
                        <option value="ZMW">ZMW (Zambian Kwacha)</option>
                        <option value="USD">USD (US Dollar)</option>
                        <option value="EUR">EUR (Euro)</option>
                        <option value="GBP">GBP (British Pound)</option>
                      </select>
                      <div v-if="getFieldError('currency')" class="invalid-feedback">
                        {{ getFieldError('currency') }}
                      </div>
                    </div>
                  </div>

                  <div class="mt-4 d-flex justify-content-end">
                    <button type="button" class="btn btn-primary" @click="nextStep">
                      Next <i class="fa fa-arrow-right ms-2"></i>
                    </button>
                  </div>
                </div>

                <!-- Step 2: Location & Amenities -->
                <div v-show="currentStep === 2" class="wizard-step">
                  <h5 class="mb-4">Location & Amenities</h5>
                  <div class="row">
                    <!-- Province -->
                    <div class="col-md-4 mb-3">
                      <label class="form-label">Province <span class="text-danger">*</span></label>
                      <select 
                        v-model="form.province_id" 
                        class="form-select"
                        :class="{ 'is-invalid': getFieldError('province_id') }"
                        @change="onProvinceChange"
                      >
                        <option :value="undefined">Select Province</option>
                        <option 
                          v-for="province in referenceStore.provinces" 
                          :key="province.id" 
                          :value="province.id"
                        >
                          {{ province.name }}
                        </option>
                      </select>
                      <div v-if="getFieldError('province_id')" class="invalid-feedback">
                        {{ getFieldError('province_id') }}
                      </div>
                    </div>

                    <!-- District -->
                    <div class="col-md-4 mb-3">
                      <label class="form-label">District</label>
                      <select 
                        v-model="form.district_id" 
                        class="form-select"
                        :class="{ 'is-invalid': getFieldError('district_id') }"
                        :disabled="!form.province_id"
                        @change="onDistrictChange"
                      >
                        <option :value="undefined">Select District</option>
                        <option 
                          v-for="district in filteredDistricts" 
                          :key="district.id" 
                          :value="district.id"
                        >
                          {{ district.name }}
                        </option>
                      </select>
                      <div v-if="getFieldError('district_id')" class="invalid-feedback">
                        {{ getFieldError('district_id') }}
                      </div>
                    </div>

                    <!-- Constituency -->
                    <div class="col-md-4 mb-3">
                      <label class="form-label">Constituency/Ward</label>
                      <select 
                        v-model="form.ward_id" 
                        class="form-select"
                        :class="{ 'is-invalid': getFieldError('ward_id') }"
                        :disabled="!form.district_id"
                      >
                        <option :value="undefined">Select Constituency</option>
                        <option 
                          v-for="constituency in filteredConstituencies" 
                          :key="constituency.id" 
                          :value="constituency.id"
                        >
                          {{ constituency.name }}
                        </option>
                      </select>
                      <div v-if="getFieldError('ward_id')" class="invalid-feedback">
                        {{ getFieldError('ward_id') }}
                      </div>
                    </div>

                    <!-- Address Line -->
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Address Line</label>
                      <input 
                        type="text" 
                        v-model="form.address_line" 
                        class="form-control"
                        :class="{ 'is-invalid': getFieldError('address_line') }"
                        placeholder="e.g. 123 Independence Avenue"
                      />
                      <div v-if="getFieldError('address_line')" class="invalid-feedback">
                        {{ getFieldError('address_line') }}
                      </div>
                    </div>

                    <!-- Location Text -->
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Location Description</label>
                      <input 
                        type="text" 
                        v-model="form.location_text" 
                        class="form-control"
                        :class="{ 'is-invalid': getFieldError('location_text') }"
                        placeholder="e.g. Near Manda Hill Mall"
                      />
                      <div v-if="getFieldError('location_text')" class="invalid-feedback">
                        {{ getFieldError('location_text') }}
                      </div>
                    </div>

                    <!-- Latitude -->
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Latitude</label>
                      <input 
                        type="number" 
                        v-model.number="form.latitude" 
                        class="form-control"
                        :class="{ 'is-invalid': getFieldError('latitude') }"
                        placeholder="e.g. -15.4167"
                        step="any"
                      />
                      <div v-if="getFieldError('latitude')" class="invalid-feedback">
                        {{ getFieldError('latitude') }}
                      </div>
                    </div>

                    <!-- Longitude -->
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Longitude</label>
                      <input 
                        type="number" 
                        v-model.number="form.longitude" 
                        class="form-control"
                        :class="{ 'is-invalid': getFieldError('longitude') }"
                        placeholder="e.g. 28.2833"
                        step="any"
                      />
                      <div v-if="getFieldError('longitude')" class="invalid-feedback">
                        {{ getFieldError('longitude') }}
                      </div>
                    </div>

                    <!-- Amenities -->
                    <div class="col-md-12 mb-3">
                      <label class="form-label d-block mb-3">Amenities</label>
                      <div v-if="groupedAmenities.length === 0" class="text-center py-4 text-muted">
                        <i class="fa fa-info-circle me-2"></i>No amenities available
                      </div>
                      <div v-for="group in groupedAmenities" :key="group.categoryId ?? 'uncategorized'" class="mb-4">
                        <h6 class="text-muted mb-3">
                          <i class="fa fa-tags me-2"></i>{{ group.categoryName }}
                        </h6>
                        <div class="amenities-grid">
                          <div 
                            v-for="amenity in group.amenities" 
                            :key="amenity.id"
                            class="amenity-icon-card"
                            :class="{ 'selected': form.amenity_ids?.includes(amenity.id) }"
                            @click="toggleAmenity(amenity.id)"
                            :title="amenity.name"
                          >
                            <i v-if="amenity.icon" :class="amenity.icon"></i>
                            <i v-else class="fa fa-check"></i>
                            <div class="amenity-check-badge" v-if="form.amenity_ids?.includes(amenity.id)">
                              <i class="fa fa-check"></i>
                            </div>
                            <div class="amenity-tooltip">{{ amenity.name }}</div>
                          </div>
                        </div>
                      </div>
                      <div v-if="getFieldError('amenity_ids')" class="text-danger small mt-2">
                        {{ getFieldError('amenity_ids') }}
                      </div>
                    </div>
                  </div>

                  <div class="mt-4 d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary" @click="prevStep">
                      <i class="fa fa-arrow-left me-2"></i> Back
                    </button>
                    <button type="button" class="btn btn-primary" @click="nextStep">
                      Next <i class="fa fa-arrow-right ms-2"></i>
                    </button>
                  </div>
                </div>

                <!-- Step 3: Images & Submit -->
                <div v-show="currentStep === 3" class="wizard-step">
                  <h5 class="mb-4">Property Images</h5>
                  <div class="row">
                    <div class="col-md-12">
                      <!-- File Upload Dropzone -->
                      <div class="mb-4">
                        <div 
                          class="image-dropzone"
                          @click="triggerFileInput"
                          @dragover.prevent="isDragging = true"
                          @dragleave.prevent="isDragging = false"
                          @drop.prevent="handleDrop"
                          :class="{ 'dragging': isDragging }"
                        >
                          <input 
                            type="file" 
                            ref="fileInputRef"
                            class="d-none"
                            @change="handleFileUpload"
                            accept="image/*"
                            multiple
                          />
                          <div class="dropzone-content">
                            <i class="fa fa-cloud-upload fa-4x mb-3 text-primary"></i>
                            <h5>Click to upload or drag and drop</h5>
                            <p class="text-muted mb-0">PNG, JPG, JPEG (MAX. 10MB each)</p>
                          </div>
                        </div>
                        <div v-if="getFieldError('images')" class="text-danger text-center mt-2">
                          {{ getFieldError('images') }}
                        </div>
                      </div>

                      <!-- Image Previews -->
                      <div v-if="imagePreviews.length > 0">
                        <h6 class="mb-3">Uploaded Images ({{ imagePreviews.length }})</h6>
                        <div class="row g-3">
                          <div 
                            v-for="(preview, index) in imagePreviews" 
                            :key="index"
                            class="col-xl-3 col-lg-4 col-md-6"
                          >
                            <div class="image-preview-card">
                              <img 
                                :src="preview.url" 
                                class="img-fluid rounded"
                              />
                              <button 
                                type="button"
                                class="btn btn-danger btn-sm image-remove-btn"
                                @click="removeImage(index)"
                              >
                                <i class="fa fa-times"></i>
                              </button>
                              <div class="form-check image-thumbnail-check">
                                <input 
                                  type="radio" 
                                  class="form-check-input" 
                                  :id="`thumbnail-${index}`"
                                  name="thumbnail"
                                  :value="index"
                                  v-model="form.thumbnail_index"
                                />
                                <label class="form-check-label" :for="`thumbnail-${index}`">
                                  <span class="badge bg-primary">Thumbnail</span>
                                </label>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div v-else class="text-center py-5">
                        <i class="fa fa-image fa-4x text-muted mb-3 opacity-25"></i>
                        <p class="text-muted">No images uploaded yet</p>
                      </div>
                    </div>
                  </div>

                  <div class="mt-4 d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary" @click="prevStep">
                      <i class="fa fa-arrow-left me-2"></i> Back
                    </button>
                    <button 
                      type="submit" 
                      class="btn btn-success btn-lg"
                      :disabled="createMutation.isPending.value"
                    >
                      <span v-if="createMutation.isPending.value">
                        <span class="spinner-border spinner-border-sm me-2"></span>
                        Creating...
                      </span>
                      <span v-else>
                        <i class="fa fa-check me-2"></i>
                        Create Listing
                      </span>
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
       
<script setup lang="ts">
import type { CreateListingInput } from '~/types/listing'

definePageMeta({
  name: 'create-listing',
  path: '/listings/create',
  middleware: ['auth'],
})

const router = useRouter()
const referenceStore = useReferenceStore()
const { useCreateListingMutation } = useListings()
const { 
  useFetchPropertyTypesQuery,
  useFetchProvincesQuery,
  useFetchDistrictsQuery,
  useFetchConstituenciesQuery,
  useFetchAmenitiesForSelectQuery,
  useFetchOrganizationsQuery,
} = useReference()

// Fetch reference data
useFetchPropertyTypesQuery()
useFetchProvincesQuery()
useFetchDistrictsQuery()
useFetchConstituenciesQuery()
useFetchAmenitiesForSelectQuery()
useFetchOrganizationsQuery()

// Stepper
const currentStep = ref<number>(1)
const totalSteps = 3
const stepTitles = ['Basic Info', 'Location & Amenities', 'Images']

const nextStep = () => {
  if (currentStep.value < totalSteps) currentStep.value++
}

const prevStep = () => {
  if (currentStep.value > 1) currentStep.value--
}

const goToStep = (step: number) => {
  if (step >= 1 && step <= totalSteps) currentStep.value = step
}

// Form state
const form = ref<CreateListingInput>({
  organization_id: undefined,
  title: '',
  description: '',
  property_type_id: undefined as any,
  price_amount_minor: 0,
  currency: 'ZMW',
  price_period: undefined as any,
  province_id: undefined as any,
  district_id: undefined,
  ward_id: undefined,
  address_line: '',
  location_text: '',
  latitude: undefined,
  longitude: undefined,
  amenity_ids: [],
  status: 'published',
  images: [],
  thumbnail_index: 0,
})

// Image previews
const imagePreviews = ref<{ url: string; file: File }[]>([])

// Filtered districts based on selected province
const filteredDistricts = computed(() => {
  if (!form.value.province_id) return []
  return referenceStore.districts.filter(d => d.province_id === form.value.province_id)
})

// Filtered constituencies based on selected district
const filteredConstituencies = computed(() => {
  if (!form.value.district_id) return []
  return referenceStore.constituencies.filter(c => c.district_id === form.value.district_id)
})

// When province changes, clear district and constituency
function onProvinceChange() {
  form.value.district_id = undefined
  form.value.ward_id = undefined
  
  // Fetch districts for the selected province
  if (form.value.province_id) {
    referenceStore.fetchDistricts(form.value.province_id)
  }
}

// When district changes, clear constituency
function onDistrictChange() {
  form.value.ward_id = undefined
  
  // Fetch constituencies for the selected district
  if (form.value.district_id) {
    referenceStore.fetchConstituencies(form.value.district_id)
  }
}

// Group amenities by category
const groupedAmenities = computed(() => {
  const groups: { categoryId: number | null; categoryName: string; amenities: any[] }[] = []
  const amenitiesByCategory = new Map<number | null, any[]>()
  
  // Group amenities
  referenceStore.amenities.forEach(amenity => {
    const categoryId = amenity.category_id ?? null
    if (!amenitiesByCategory.has(categoryId)) {
      amenitiesByCategory.set(categoryId, [])
    }
    amenitiesByCategory.get(categoryId)!.push(amenity)
  })
  
  // Convert to array and sort
  amenitiesByCategory.forEach((amenities, categoryId) => {
    const categoryName = categoryId 
      ? amenities[0]?.category?.name ?? 'Uncategorized'
      : 'Uncategorized'
    
    groups.push({
      categoryId,
      categoryName,
      amenities: amenities.sort((a, b) => a.name.localeCompare(b.name))
    })
  })
  
  // Sort groups by category name
  return groups.sort((a, b) => a.categoryName.localeCompare(b.categoryName))
})

// Toggle amenity selection
function toggleAmenity(amenityId: number) {
  if (!form.value.amenity_ids) {
    form.value.amenity_ids = []
  }
  
  const index = form.value.amenity_ids.indexOf(amenityId)
  if (index > -1) {
    form.value.amenity_ids.splice(index, 1)
  } else {
    form.value.amenity_ids.push(amenityId)
  }
}

// File input ref and drag state
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

// Trigger file input click
function triggerFileInput() {
  fileInputRef.value?.click()
}

// Handle file upload
function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files) {
    addFiles(Array.from(target.files))
    target.value = ''
  }
}

// Handle drag and drop
function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files) {
    addFiles(Array.from(event.dataTransfer.files))
  }
}

// Add files helper
function addFiles(files: File[]) {
  // Filter only image files
  const imageFiles = files.filter(file => file.type.startsWith('image/'))
  
  // Add new files to existing images
  imageFiles.forEach((file) => {
    const url = URL.createObjectURL(file)
    imagePreviews.value.push({ url, file })
  })
  
  // Update form images
  if (!form.value.images) {
    form.value.images = []
  }
  form.value.images.push(...imageFiles)
}

// Remove an image
function removeImage(index: number) {
  const preview = imagePreviews.value[index]
  if (preview) {
    URL.revokeObjectURL(preview.url)
  }
  imagePreviews.value.splice(index, 1)
  
  if (form.value.images) {
    form.value.images.splice(index, 1)
  }
  
  // Adjust thumbnail index if needed
  if (form.value.thumbnail_index === index) {
    form.value.thumbnail_index = 0
  } else if (form.value.thumbnail_index && form.value.thumbnail_index > index) {
    form.value.thumbnail_index--
  }
}

// Create mutation
const createMutation = useCreateListingMutation()
const { getFieldError } = createMutation

// Handle form submit
async function handleSubmit() {
  await createMutation.mutateAsync(form.value)
  
  if (!createMutation.isError.value) {
    // Redirect to listings page
    router.push('/listings')
  }
}

// Cleanup on unmount
onUnmounted(() => {
  imagePreviews.value.forEach(preview => URL.revokeObjectURL(preview.url))
})
</script>

<style scoped>
/* Wizard Tabs */
.wizard-tabs {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 20px 0;
  border-bottom: 2px solid #f8f9fa;
  margin-bottom: 30px;
}

.wizard-tab {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f8f9fa;
  border: 2px solid #dee2e6;
  border-radius: 8px;
  padding: 12px 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 120px;
}

.wizard-tab:hover {
  background: #e9ecef;
  transform: translateY(-2px);
}

.wizard-tab.active {
  background: var(--theme-default);
  border-color: var(--theme-default);
  color: white;
}

.wizard-tab.completed {
  background: #51bb25;
  border-color: #51bb25;
  color: white;
}

.step-number {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  color: #495057;
  border-radius: 50%;
  font-weight: 600;
  font-size: 16px;
}

.wizard-tab.active .step-number {
  background: white;
  color: var(--theme-default);
}

.wizard-tab.completed .step-number {
  background: white;
  color: #51bb25;
}

.step-title {
  font-weight: 500;
  font-size: 14px;
}

/* Wizard Step */
.wizard-step {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Amenities Grid */
.amenities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
  gap: 10px;
}

.amenity-icon-card {
  position: relative;
  background: #f8f9fa;
  border: 2px solid #dee2e6;
  border-radius: 10px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 24px;
  color: #495057;
}

.amenity-icon-card:hover {
  background: #e9ecef;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.amenity-icon-card:hover .amenity-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.amenity-icon-card.selected {
  background: var(--theme-default);
  border-color: var(--theme-default);
  color: white;
}

.amenity-check-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  width: 20px;
  height: 20px;
  background: #51bb25;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 11px;
  border: 2px solid white;
}

.amenity-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-5px);
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
  pointer-events: none;
  z-index: 10;
  margin-bottom: 5px;
}

.amenity-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.9);
}

/* Image Dropzone */
.image-dropzone {
  border: 3px dashed #dee2e6;
  border-radius: 12px;
  padding: 60px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #f8f9fa;
}

.image-dropzone:hover {
  border-color: var(--theme-default);
  background: #f0f7ff;
}

.image-dropzone.dragging {
  border-color: var(--theme-default);
  background: #e7f4ff;
  border-style: solid;
}

.dropzone-content {
  pointer-events: none;
}

.dropzone-content h5 {
  color: #495057;
  font-weight: 500;
  margin-bottom: 10px;
}

/* Image Preview */
.image-preview-card {
  position: relative;
  border: 2px solid #dee2e6;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  background: #f8f9fa;
}

.image-preview-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.image-preview-card img {
  width: 100%;
  height: 200px;
  object-fit: cover;
}

.image-remove-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  padding: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.image-preview-card:hover .image-remove-btn {
  opacity: 1;
}

.image-thumbnail-check {
  position: absolute;
  bottom: 8px;
  left: 8px;
  background: rgba(0, 0, 0, 0.7);
  padding: 4px 8px;
  border-radius: 6px;
}

.image-thumbnail-check .form-check-label {
  color: white;
  cursor: pointer;
  margin-bottom: 0;
}

.image-thumbnail-check .badge {
  font-size: 11px;
}

/* Responsive */
@media (max-width: 768px) {
  .wizard-tabs {
    gap: 10px;
  }
  
  .wizard-tab {
    min-width: auto;
    padding: 10px 16px;
  }
  
  .step-title {
    display: none;
  }
  
  .amenities-grid {
    grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
    gap: 8px;
  }
  
  .amenity-icon-card {
    width: 50px;
    height: 50px;
    font-size: 20px;
  }
}
</style>

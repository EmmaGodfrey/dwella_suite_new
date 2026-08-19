import ClassicEditor from '@ckeditor/ckeditor5-build-classic';
import CKEditor from '@ckeditor/ckeditor5-vue';
import VueJsTour from '@globalhive/vuejs-tour';
import Notifications from '@kyvg/vue3-notification';
import { createToaster } from '@meforma/vue-toaster';
import 'cropperjs/dist/cropper.css';
import 'vue3-tree/dist/style.css';
import 'vue3-toastify/dist/index.css';
import 'form-wizard-vue3/dist/form-wizard-vue3.css';
import '@vuepic/vue-datepicker/dist/main.css';
import 'vue-multiselect/dist/vue-multiselect.css';
import 'vue3-simple-typeahead/dist/vue3-simple-typeahead.css';
import 'vue-rate/dist/vue-rate.css';
import '@globalhive/vuejs-tour/dist/style.css';
import 'vue-slider-component/theme/antd.css';
import 'leaflet/dist/leaflet.css';
import 'dropzone-vue/dist/dropzone-vue.common.css';
import { LIcon, LMap, LMarker, LPopup, LPolygon, LTileLayer } from '@vue-leaflet/vue-leaflet';
import Datepicker from '@vuepic/vue-datepicker';
import AosVue from 'aos-vue';
import { Tooltip, Popover } from 'bootstrap/dist/js/bootstrap.esm.min.js';
import DropZone from 'dropzone-vue';
import Wizard from 'form-wizard-vue3';
import L from 'leaflet';
import Swal from 'sweetalert2';
import VueCropper from 'vue-cropperjs';
import { VueDraggableNext } from 'vue-draggable-next';
import Lightbox from 'vue-easy-lightbox';
import VueFeather from 'vue-feather';
import { GChart } from 'vue-google-charts';
import Multiselect from 'vue-multiselect';
import VueNumber from 'vue-number-animation';
import rate from 'vue-rate';
import VueSlider from 'vue-slider-component';
import StarRating from 'vue-star-rating';
import { GoogleMap, Marker, Polyline } from 'vue3-google-map';
import SimpleTypeahead from 'vue3-simple-typeahead';
import { toast } from 'vue3-toastify';
import Tree from 'vue3-tree';

import TheBreadcrumbs from '~/components/TheBreadcrumbs.vue';

const options = {
  reverseButtons: true,
};

export default defineNuxtPlugin(nuxtApp => {
  if (import.meta.client) {
    nuxtApp.vueApp.component('Polyline', Polyline);
    nuxtApp.vueApp.component('GoogleMap', GoogleMap);
    nuxtApp.vueApp.component('Marker', Marker);
    nuxtApp.vueApp.component('LPolygon', LPolygon);
    nuxtApp.vueApp.component('LMap', LMap);
    nuxtApp.vueApp.component('LTileLayer', LTileLayer);
    nuxtApp.vueApp.component('LMarker', LMarker);
    nuxtApp.vueApp.component('LIcon', LIcon);
    nuxtApp.vueApp.component('LPopup', LPopup);
    nuxtApp.vueApp.component('Datepicker', Datepicker);
    nuxtApp.vueApp.use(VueNumber);
    nuxtApp.vueApp.use(Lightbox);
    nuxtApp.vueApp.use(DropZone);
    nuxtApp.vueApp.component('multiselect', Multiselect);
    nuxtApp.vueApp.use(SimpleTypeahead);
    nuxtApp.vueApp.use(Notifications);
    nuxtApp.vueApp.use(VueJsTour);
    nuxtApp.vueApp.use(AosVue);
    nuxtApp.vueApp.component('Rate', rate);
    nuxtApp.vueApp.component('Wizard', Wizard);
    nuxtApp.vueApp.component('GChart', GChart);
    nuxtApp.vueApp.component('Tree', Tree);
    nuxtApp.vueApp.component('VueCropper', VueCropper);
    nuxtApp.vueApp.component('VueSlider', VueSlider);
    nuxtApp.vueApp.component('vue-feather', VueFeather);
    nuxtApp.vueApp.provide('Popover', Popover);
    nuxtApp.vueApp.provide('Tooltip', Tooltip);
    nuxtApp.vueApp.component('star-rating', StarRating);
    nuxtApp.vueApp.provide('toast', toast);
    nuxtApp.vueApp.provide('createToaster ', createToaster);
    nuxtApp.vueApp.provide('VueDraggableNext', VueDraggableNext);
    nuxtApp.vueApp.provide('ClassicEditor', ClassicEditor);
    nuxtApp.vueApp.component('ckeditor', CKEditor.component);
    return {
      provide: {
        L,
      },
    };
  }
  nuxtApp.vueApp.component('TheBreadcrumbs', TheBreadcrumbs);
});

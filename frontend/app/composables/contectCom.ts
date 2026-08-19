import type personalType from '~/types/personal';

export const src = ref<string>('null');
export const filtered = ref<boolean>(false);
export const filter = ref<boolean>(false);
export const lastModified = ref<File | null>(null);

export function loadFile(event: Event, contact: personalType) {
  const target = event.target;
  if (!(target instanceof HTMLInputElement) || !target.files?.length) return;

  const file = target.files[0];
  if (file) {
    lastModified.value = file;

    if (src.value !== 'null') {
      URL.revokeObjectURL(src.value); // cleanup old blob URL
    }
    src.value = URL.createObjectURL(file);
    contact.imgUrl = src.value;
  }
}

export function collapseFilter() {
  filtered.value = !filtered.value;
}
export function collapse() {
  filter.value = !filter.value;
}

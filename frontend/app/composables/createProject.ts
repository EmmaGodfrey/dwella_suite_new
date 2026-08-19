export const title = ref<string>('');
export const desc = ref<string>('');
export const inputClasses = ref<string>('is-invalid');
export const itemClasses = ref<string>('is-invalid');

export function validated() {
  if (title.value.length < 5) {
    inputClasses.value = 'is-invalid';
  } else {
    inputClasses.value = 'is-valid';
  }
}
export function update() {
  if (desc.value.length < 4) {
    itemClasses.value = 'is-invalid';
  } else {
    itemClasses.value = 'is-valid';
  }
}

// Initialize the filtered list
export function initializeListFiltered() {
  listFiltered.value = list.value;
}

interface data {
  placeholder: string;
  minInputLength: number;
  hint: boolean;
}
export const options = ref<data>({
  placeholder: 'States of USA',
  minInputLength: 1,
  hint: false,
});
export const listFiltered = ref<string[]>([]);
export const list = ref<string[]>([
  'alabama',
  'alaska',
  'arizona',
  'arkansas',
  'california',
  'colorado',
  'connecticut',
  'delaware',
  'florida',
  'georgia',
  'hawaii',
  'idaho',
  'illinois',
  'indiana',
  'iowa',
  'kansas',
  'kentucky',
  'louisiana',
  'maine',
  'maryland',
  'massachusetts',
  'michigan',
  'minnesota',
  'mississippi',
  'missouri',
  'montana',
  'nebraska',
  'nevada',
  'new hampshire',
  'new jersey',
  'new mexico',
  'new york',
  'north carolina',
  'north dakota',
  'ohio',
  'oklahoma',
  'oregon',
  'pennsylvania',
  'rhode island',
  'south carolina',
  'south dakota',
  'tennessee',
  'texas',
  'utah',
  'vermont',
  'virginia',
  'washington',
  'west virginia',
  'wisconsin',
  'wyoming',
]);

export function selectItem(item: string) {}
export function onInput(event: { items: string[] }) {
  listFiltered.value = event.items;
}
export function onBlur(event: { items: string[] }) {
  listFiltered.value = event.items;
}

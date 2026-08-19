interface InputItem {
  data: string;
  errorMessage: string;
}

interface Inputs {
  title: InputItem;
  sub: InputItem;
  date: InputItem;
  select: InputItem;
  desc: InputItem;
}

export const errors = ref([]);

export const optionValues = ref<string[]>(['7:00', '7:30', '8:00', '8:30', '9:00', '9:30', '10:00', '11:00', '11:30', '12:00', '12:30', '1:00', '2:00', '3:00', '4:00', '5:00', '6:00']);
export const inputs = ref<Inputs>({
  title: {
    data: '',
    errorMessage: '',
  },
  sub: {
    data: '',
    errorMessage: '',
  },
  date: {
    data: '',
    errorMessage: '',
  },
  select: {
    data: '',
    errorMessage: '',
  },
  desc: {
    data: '',
    errorMessage: '',
  },
});
export const formSubmitted = ref<boolean>(false);

export function onCustomStyleSubmit() {
  formSubmitted.value = true;
  const values = inputs.value;
  values.title.data.length < 3 ? (values.title.errorMessage = 'Please choose a title') : (values.title.errorMessage = '');
  values.sub.data.length < 3 ? (values.sub.errorMessage = 'Please choose a sub.') : (values.sub.errorMessage = '');
  values.date.data.length < 3 ? (values.date.errorMessage = 'Please choose a date.') : (values.date.errorMessage = '');
  values.select.data.length < 3 ? (values.select.errorMessage = 'Please provide a valid select.') : (values.select.errorMessage = '');
  values.desc.data.length < 1 ? (values.desc.errorMessage = 'Please select a valid desc.') : (values.desc.errorMessage = '');
}

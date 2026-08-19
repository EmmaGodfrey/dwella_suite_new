interface InputData {
  data: string;
  errorMessage: string;
}

interface Inputs {
  firstname: InputData;
  lastname: InputData;
  username: InputData;
  city: InputData;
  state: InputData;
  zip: InputData;
}
interface ErrorObject {
  message: string;
  code: number;
}
export const errors = ref<ErrorObject[]>([]);

export const optionValues = ref<string[]>(['one', 'two', 'three']);
export const inputs = ref<Inputs>({
  firstname: {
    data: 'Mark',
    errorMessage: 'asdasd',
  },
  lastname: {
    data: 'Otto',
    errorMessage: '',
  },
  username: {
    data: '',
    errorMessage: '',
  },
  city: {
    data: '',
    errorMessage: '',
  },
  state: {
    data: '',
    errorMessage: '',
  },
  zip: {
    data: '',
    errorMessage: '',
  },
});
export const inputss = ref<Inputs>({
  firstname: {
    data: 'Mark',
    errorMessage: 'asdasd',
  },
  lastname: {
    data: 'Otto',
    errorMessage: '',
  },
  username: {
    data: '',
    errorMessage: '',
  },
  city: {
    data: '',
    errorMessage: '',
  },
  state: {
    data: '',
    errorMessage: '',
  },
  zip: {
    data: '',
    errorMessage: '',
  },
});
export const formSubmitted = ref<boolean>(false);
export const Submitted = ref<boolean>(false);

export function onCustomStyleSubmit() {
  formSubmitted.value = true;
  const values = inputs.value;
  values.firstname.data.length < 3 ? (values.firstname.errorMessage = 'Please choose a firstname') : (values.firstname.errorMessage = '');
  values.lastname.data.length < 3 ? (values.lastname.errorMessage = 'Please choose a lastname.') : (values.lastname.errorMessage = '');
  values.username.data.length < 3 ? (values.username.errorMessage = 'Please choose a username.') : (values.username.errorMessage = '');
  values.city.data.length < 3 ? (values.city.errorMessage = 'Please provide a valid city.') : (values.city.errorMessage = '');
  values.state.data.length < 1 ? (values.state.errorMessage = 'Please select a valid state.') : (values.state.errorMessage = '');
  values.zip.data.length < 7 ? (values.zip.errorMessage = 'Please provide a valid zip.') : (values.zip.errorMessage = '');
}

export function onCustomSubmit() {
  Submitted.value = true;
  const values = inputss.value;
  values.firstname.data.length < 3 ? (values.firstname.errorMessage = 'Please choose a firstname') : (values.firstname.errorMessage = '');
  values.lastname.data.length < 3 ? (values.lastname.errorMessage = 'Please choose a lastname.') : (values.lastname.errorMessage = '');
  values.username.data.length < 3 ? (values.username.errorMessage = 'Please choose a username.') : (values.username.errorMessage = '');
  values.city.data.length < 3 ? (values.city.errorMessage = 'Please provide a valid city.') : (values.city.errorMessage = '');
  values.state.data.length < 1 ? (values.state.errorMessage = 'Please select a valid state.') : (values.state.errorMessage = '');
  values.zip.data.length < 7 ? (values.zip.errorMessage = 'Please provide a valid zip.') : (values.zip.errorMessage = '');
}

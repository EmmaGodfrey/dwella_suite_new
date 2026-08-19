import { defineStore } from 'pinia';

import bootstrap from '~/data/bootstrap.json';

interface table {
  id: number;
  img: string;
  firstName: string;
  lastName: string;
  userName: string;
  role: string;
  company: string;
  language: string;
  badgeClass: string;
  credit: string;
  borderColor: string;
  country: string;
}
interface table1 {
  id: number;
  firstName: string;
  lastName: string;
  office: string;
  role: string;
  salary: string;
  age: number;
  join: string;
}
interface table2 {
  id: number;
  icon: string;
  status: string;
  signalName: string;
  security: string;
  stage: string;
  schedule: string;
  bgClass: string;
  teamLead: string;
  font: string;
}
interface table3 {
  id: number;
  firstName: string;
  name: string;
  email: string;
  lastName: string;
  exp: string;
  sex: string;
  contact: string;
  userName: string;
  age: string;
  dessert: string;
  calories: string;
  fat: string;
  price: string;
}
interface breckpoint {
  id: number;
  name: string;
  order: string;
  price: string;
  quantity: string;
  total: string;
}
interface sizing {
  id: number;
  Name: string;
  Date: string;
  Status: string;
  statusClass: string;
  hours: string;
  performance: string;
}
interface custom {
  id: number;
  film: string;
  released: string;
  studio: string;
  budget: string;
  domestic: string;
}
interface dashed {
  id: number;
  className: string;
  type: string;
  hours: string;
  trainer: string;
  spot: string;
}

export const useBootstrapStore = defineStore('bootstrap', () => {
  const data = ref<table[]>(bootstrap.datatable1);
  const inverse = ref<table1[]>(bootstrap.inverse);
  const hoverable = ref<table2[]>(bootstrap.hoverable);
  const caption = ref<table3[]>(bootstrap.table2);
  const breckpoint = ref<breckpoint[]>(bootstrap.breckpoint);
  const sizing = ref<sizing[]>(bootstrap.sizingTablesXl);
  const custom = ref<custom[]>(bootstrap.tableData2);
  const dashed = ref<dashed[]>(bootstrap.tableData);

  return {
    data,
    inverse,
    hoverable,
    caption,
    breckpoint,
    sizing,
    custom,
    dashed,
  };
});

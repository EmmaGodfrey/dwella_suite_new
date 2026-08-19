<template>
  <div class="row">
    <div class="col-sm-4">
      <div class="form-group">
        <label class="form-label">Birth Date</label>
        <ClientOnly>
          <multiselect
            v-model="multiValue"
            tag-placeholder="Add this as new tag"
            placeholder="Select Your Name"
            label="name"
            track-by="code"
            :options="options"
            :multiple="false"
            :taggable="true"
          ></multiselect>
        </ClientOnly>
      </div>
    </div>
    <div class="col-sm-4">
      <div class="form-group">
        <div class="col-form-label m-t-5">
          <ClientOnly>
            <multiselect v-model="Value" tag-placeholder="Add this as new tag" placeholder="Select Your Name" label="name" track-by="code" :options="options1" :multiple="false" :taggable="true">
            </multiselect>
          </ClientOnly>
        </div>
      </div>
    </div>
    <div class="col-sm-4">
      <div class="form-group">
        <div class="col-form-label m-t-5">
          <ClientOnly>
            <multiselect v-model="Value1" tag-placeholder="Add this as new tag" placeholder="Select Your Name" label="name" track-by="code" :options="options2" :multiple="false" :taggable="true">
            </multiselect>
          </ClientOnly>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import multiselect from 'vue-multiselect';

interface multi {
  code: number;
  name: string;
}
const multiValue = ref<multi[]>([{ code: 1, name: 'January' }]);
const Value = ref<multi[]>([{ code: 1, name: '1' }]);
const Value1 = ref<multi[]>([{ code: 1, name: '1985' }]);
const options = ref<multi[]>([
  { code: 1, name: 'January' },
  { code: 2, name: 'February' },
  { code: 3, name: 'March' },
  { code: 4, name: 'April' },
  { code: 5, name: 'May' },
  { code: 6, name: 'June' },
  { code: 7, name: 'July' },
  { code: 8, name: 'August' },
  { code: 9, name: 'September' },
  { code: 10, name: 'October' },
  { code: 11, name: 'November' },
  { code: 12, name: 'December' },
]);
const options1 = ref<multi[]>([
  { code: 1, name: '1' },
  { code: 2, name: '2' },
  { code: 3, name: '3' },
  { code: 4, name: '4' },
  { code: 5, name: '5' },
  { code: 6, name: '6' },
  { code: 7, name: '7' },
  { code: 8, name: '8' },
  { code: 9, name: '9' },
  { code: 10, name: '10' },
  { code: 11, name: '11' },
  { code: 12, name: '12' },
  { code: 13, name: '13' },
  { code: 14, name: '14' },
  { code: 15, name: '15' },
  { code: 16, name: '16' },
  { code: 17, name: '17' },
  { code: 18, name: '18' },
  { code: 19, name: '19' },
  { code: 20, name: '20' },
  { code: 21, name: '21' },
  { code: 22, name: '22' },
  { code: 23, name: '23' },
  { code: 24, name: '24' },
  { code: 25, name: '25' },
  { code: 26, name: '26' },
  { code: 27, name: '27' },
  { code: 28, name: '28' },
  { code: 29, name: '29' },
  { code: 30, name: '30' },
  { code: 30, name: '31' },
]);
const options2 = ref<multi[]>([
  { code: 1, name: '1985' },
  { code: 2, name: '1986' },
  { code: 3, name: '1987' },
  { code: 4, name: '1988' },
  { code: 5, name: '1989' },
  { code: 6, name: '1990' },
  { code: 7, name: '1991' },
  { code: 8, name: '1992' },
  { code: 9, name: '1993' },
  { code: 10, name: '1994' },
  { code: 11, name: '1995' },
  { code: 12, name: '1996' },
  { code: 13, name: '1997' },
  { code: 14, name: '1998' },
  { code: 15, name: '1999' },
  { code: 16, name: '2000' },
  { code: 17, name: '2001' },
  { code: 18, name: '2002' },
  { code: 19, name: '2003' },
  { code: 20, name: '2004' },
  { code: 21, name: '2005' },
  { code: 22, name: '2006' },
  { code: 23, name: '2007' },
  { code: 24, name: '2008' },
  { code: 25, name: '2009' },
  { code: 26, name: '2010' },
  { code: 27, name: '2012' },
  { code: 28, name: '2013' },
  { code: 29, name: '2014' },
  { code: 30, name: '2015' },
  { code: 30, name: '2016' },
  { code: 30, name: '2017' },
  { code: 30, name: '2018' },
  { code: 30, name: '2019' },
]);
</script>

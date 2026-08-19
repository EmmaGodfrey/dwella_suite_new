import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin, { Draggable } from '@fullcalendar/interaction';
import timeGridPlugin from '@fullcalendar/timegrid';
import FullCalendar from '@fullcalendar/vue3';

FullCalendar.options = {
  plugins: [dayGridPlugin, interactionPlugin, timeGridPlugin],
};

export default defineNuxtPlugin((/* nuxtApp */) => {
  return {
    provide: {
      fullCalendar: () => FullCalendar,
    },
  };
});

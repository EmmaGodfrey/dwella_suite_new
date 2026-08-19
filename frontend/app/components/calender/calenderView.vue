<template>
  <div class="card">
    <div class="card-body">
      <div class="row" id="wrap">
        <div class="col-xxl-3 box-col-30">
          <div id="external-events">
            <h4>Draggable Events</h4>
            <div id="external-events-list">
              <div class="fc-event fc-h-event fc-daygrid-event fc-daygrid-block-event draggableButton">
                <div class="fc-event-main"><i class="fa fa-birthday-cake me-2"></i>Birthday Party</div>
              </div>
              <div class="fc-event fc-h-event fc-daygrid-event fc-daygrid-block-event draggableButton">
                <div class="fc-event-main"><i class="fa fa-user me-2"></i>Meeting With Team.</div>
              </div>
              <div class="fc-event fc-h-event fc-daygrid-event fc-daygrid-block-event draggableButton">
                <div class="fc-event-main"><i class="fa fa-plane me-2"></i>Tour & Picnic</div>
              </div>
              <div class="fc-event fc-h-event fc-daygrid-event fc-daygrid-block-event draggableButton">
                <div class="fc-event-main"><i class="fa fa-file-text me-2"></i>Reporting Schedule</div>
              </div>
              <div class="fc-event fc-h-event fc-daygrid-event fc-daygrid-block-event draggableButton">
                <div class="fc-event-main"><i class="fa fa-briefcase me-2"></i>Lunch & Break</div>
              </div>
            </div>
            <p>
              <input class="checkbox_animated" id="drop-remove" type="checkbox" />
              <label for="drop-remove">remove after drop</label>
            </p>
          </div>
        </div>
        <div class="col-xxl-9 box-col-70">
          <div class="calendar-default" id="calendar-container">
            <div id="calendar">
              <FullCalendar id="calendar" :options="calendarOptions" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin, { Draggable, DropArg } from '@fullcalendar/interaction';
import timeGridPlugin from '@fullcalendar/timegrid';
import FullCalendar from '@fullcalendar/vue3';

import { INITIAL_EVENTS, createEventId } from '~/composables/calendardata';

import type { CalendarOptions, EventInput, DateSelectArg, EventClickArg } from '@fullcalendar/core';

const filtered = ref<boolean>(false);
const formattedEvents: EventInput[] = INITIAL_EVENTS.map(event => ({
  id: event.id,
  title: event.title,
  start: event.start || event.date,
  end: event.end,
}));
const calendarOptions: CalendarOptions = {
  plugins: [dayGridPlugin, interactionPlugin, timeGridPlugin],
  initialView: 'dayGridMonth',
  initialEvents: formattedEvents,
  editable: true,
  selectable: true,
  selectMirror: true,
  dayMaxEvents: true,
  weekends: true,
  select: handleDateSelect,
  eventClick: handleEventClick,
  droppable: true,
  drop: HandleDrop,
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek,timeGridDay',
  },
};

onMounted(() => {
  let buttons = document.getElementsByClassName('draggableButton');
  for (var i = 0; i < buttons.length; i++) {
    const button = buttons[i] as HTMLElement;
    new Draggable(button);
  }
});

function HandleDrop(selectInfo: DropArg) {
  let title = selectInfo.draggedEl.outerText;
  let calendarApi = selectInfo.view.calendar;
  calendarApi.unselect();
  if (title) {
    calendarApi.addEvent({
      id: createEventId(),
      title,
      start: selectInfo.date,
      allDay: true,
    });
  }
}
function handleDateSelect(selectInfo: DateSelectArg) {
  let title = prompt('Please enter a new title for your event');
  let calendarApi = selectInfo.view.calendar;
  calendarApi.unselect();
  if (title) {
    calendarApi.addEvent({
      id: createEventId(),
      title,
      start: selectInfo.startStr,
      end: selectInfo.endStr,
      allDay: selectInfo.allDay,
    });
  }
}
function handleEventClick(clickInfo: EventClickArg) {
  if (confirm(`Are you sure you want to delete the event '${clickInfo.event.title}'`)) {
    clickInfo.event.remove();
  }
}

function collapseFilter() {
  filtered.value = !filtered.value;
}
</script>

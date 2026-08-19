let eventGuid: number = 0;
const todayStr = new Date().toISOString().replace(/T.*$/, '');

export const INITIAL_EVENTS = [
  {
    id: createEventId(),
    title: 'All-day event',
    start: todayStr,
  },
  {
    id: createEventId(),
    title: 'Timed event',
    start: todayStr + 'T12:00:00',
  },

  {
    id: createEventId(),
    title: 'All-day event',
    start: '2023-07-02',
    end: '2023-07-04',
  },

  {
    id: createEventId(),
    title: 'event 2',
    start: '2023-07-07',
    end: '2023-07-09',
  },
  {
    id: createEventId(),
    title: 'all-day event',
    start: '2023-08-09T10:30:00',
    end: '2023-08-10T12:30:00',
  },

  {
    id: createEventId(),
    title: 'event2',
    date: '2023-08-12',
  },

  {
    id: createEventId(),
    title: 'All Day event',
    date: '2023-09-06',
  },
  {
    id: createEventId(),
    title: 'BirthDay Party',
    date: '2023-09-22',
  },
  {
    id: createEventId(),
    title: '4p meeting',
    date: '2023-09-11',
  },
  {
    id: createEventId(),
    title: '3:30p meeting',
    date: '2023-08-05',
  },
  {
    id: createEventId(),
    title: 'Tour with our team ',
    date: '2023-09-16',
  },
  {
    id: createEventId(),
    title: '4p meeting ',
    date: '2023-08-03',
  },
  {
    id: createEventId(),
    title: 'event3',
    date: '2023-08-06',
  },
  {
    id: createEventId(),
    title: 'Birth day',
    date: '2023-08-29',
  },
  {
    id: createEventId(),
    title: '4p meeting',
    date: '2023-07-22',
  },
  {
    id: createEventId(),
    title: 'event1',
    date: '2023-08-22',
  },
  {
    id: createEventId(),
    title: '3:30p meeting',
    date: '2023-09-23',
  },
  {
    id: createEventId(),
    title: '3:30p meeting',
    date: '2023-10-27',
  },
  {
    id: createEventId(),
    groupId: 999,
    title: 'Meeting with Team',
    start: '2022-8-11T16:00:00',
  },
  {
    id: createEventId(),
    groupId: 999,
    title: 'Upload New Project',
    start: '2023-07-16T16:00:00',
  },
  {
    id: createEventId(),
    title: 'Birthday Party',
    start: '2023-09-24',
    end: '2023-09-26',
  },
  {
    id: createEventId(),
    title: 'Reporting about Theme',
    start: '2023-09-18T10:30:00',
    end: '2023-09-19T12:30:00',
  },
  {
    id: createEventId(),
    title: 'Lunch',
    start: '2023-08-28T12:00:00',
  },
  {
    id: createEventId(),
    title: 'Meeting',
    start: '2023-08-12T14:30:00',
  },
  {
    id: createEventId(),
    title: 'Happy Hour',
    start: '2023-17-24T17:30:00',
  },
];

export function createEventId() {
  return String(eventGuid++);
}

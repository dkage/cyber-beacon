import type { components } from './schema';
type Schema = components['schemas'];
// DRF emits all response fields; optional model fields are optional only on input.
export type Task = Required<Omit<Schema['Task'], 'completed'>>;
type CalendarEvent = Required<Schema['CalendarEvent']>;
export type Mount = Schema['Mount'];
export type Connection = Schema['Connection'];
export type Settings = Required<Schema['Settings']>;
export type Day = Omit<Schema['Day'], 'tasks' | 'events'> & {
	tasks: Task[];
	events: CalendarEvent[];
};

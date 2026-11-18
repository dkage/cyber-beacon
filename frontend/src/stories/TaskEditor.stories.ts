import type { Meta, StoryObj } from '@storybook/sveltekit';
import { fn } from 'storybook/test';
import TaskEditor from '../lib/TaskEditor.svelte';
const meta = {
	title: 'Planner/Task editor',
	component: TaskEditor,
	args: { day: '2026-11-18', onsaved: fn(), oncancel: fn() }
} satisfies Meta<typeof TaskEditor>;
export default meta;
type Story = StoryObj<typeof meta>;
export const NewTask: Story = {};
export const ImportedWorksheet: Story = {
	args: {
		task: {
			id: 'fixture',
			parent: null,
			title: 'Prepare the next release',
			notes: 'My local working notes',
			do_date: '2026-11-18',
			due_date: '2026-11-20',
			start_date: null,
			priority: 1,
			estimated_minutes: 45,
			position: 0,
			completed_at: null,
			deleted_at: null,
			version: 1,
			created_at: '2026-11-18T09:00:00Z',
			updated_at: '2026-11-18T09:00:00Z',
			source: {
				provider: 'notion',
				imported_at: '2026-11-18T09:00:00Z',
				url: 'https://notion.so/example',
				raw: { title: 'Upstream title' }
			}
		}
	}
};

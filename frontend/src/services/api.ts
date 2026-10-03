import { TaskSubmitResponse, TaskRun } from '../types/events';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function submitTask(prompt: string): Promise<TaskSubmitResponse> {
  const response = await fetch(`${API_BASE}/api/tasks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to submit task (HTTP ${response.status})`);
  }

  return response.json();
}

export async function getTaskDetails(taskId: string): Promise<TaskRun> {
  const response = await fetch(`${API_BASE}/api/tasks/${taskId}`);
  if (!response.ok) {
    throw new Error(`Failed to load task ${taskId} (HTTP ${response.status})`);
  }
  return response.json();
}

export async function listRecentTasks(): Promise<TaskRun[]> {
  const response = await fetch(`${API_BASE}/api/tasks`);
  if (!response.ok) {
    throw new Error(`Failed to list tasks (HTTP ${response.status})`);
  }
  return response.json();
}

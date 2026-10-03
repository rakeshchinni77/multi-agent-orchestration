export type TaskStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export type EventType =
  | 'TASK_CREATED'
  | 'TASK_STARTED'
  | 'AGENT_STARTED'
  | 'AGENT_THOUGHT'
  | 'PLAN_CREATED'
  | 'TOOL_INVOCATION'
  | 'TOOL_STARTED'
  | 'TOOL_RESULT'
  | 'TOOL_ERROR'
  | 'AGENT_COMPLETED'
  | 'FINAL_RESULT'
  | 'TASK_COMPLETED'
  | 'TASK_FAILED'
  | 'HEARTBEAT'
  | 'PONG';

export interface AgentEvent {
  task_id: string;
  agent: string;
  event_type: EventType;
  payload: Record<string, any>;
  timestamp?: string;
  replayed?: boolean;
}

export interface TaskRun {
  id: string;
  prompt: string;
  status: TaskStatus;
  final_result?: string | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  events?: AgentEvent[];
}

export interface TaskSubmitResponse {
  task_id: string;
  status: TaskStatus;
  message: string;
}

import { useState, useEffect, useRef, useCallback } from 'react';
import { AgentEvent, TaskStatus } from '../types/events';

interface UseAgentWebSocketReturn {
  events: AgentEvent[];
  connectionStatus: 'idle' | 'connecting' | 'connected' | 'disconnected' | 'error';
  taskStatus: TaskStatus;
  finalResult: string | null;
  errorMessage: string | null;
  clearEvents: () => void;
}

export function useAgentWebSocket(taskId: string | null): UseAgentWebSocketReturn {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<
    'idle' | 'connecting' | 'connected' | 'disconnected' | 'error'
  >('idle');
  const [taskStatus, setTaskStatus] = useState<TaskStatus>('PENDING');
  const [finalResult, setFinalResult] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<number | null>(null);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setFinalResult(null);
    setErrorMessage(null);
    setTaskStatus('PENDING');
  }, []);

  useEffect(() => {
    if (!taskId) {
      setConnectionStatus('idle');
      return;
    }

    const wsBase =
      import.meta.env.VITE_WS_BASE_URL ||
      (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + `//${window.location.hostname}:8000`;

    const socketUrl = `${wsBase}/api/ws/${taskId}`;
    setConnectionStatus('connecting');

    const ws = new WebSocket(socketUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus('connected');
      // Keep alive client ping every 10s
      pingIntervalRef.current = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 10000);
    };

    ws.onmessage = (event) => {
      try {
        const data: AgentEvent = JSON.parse(event.data);

        // Filter out keep-alive heartbeats from display timeline
        if (data.event_type === 'HEARTBEAT' || data.event_type === 'PONG') {
          return;
        }

        setEvents((prev) => {
          // Prevent duplicates by checking event payload or timestamp
          const isDuplicate = prev.some(
            (e) =>
              e.timestamp === data.timestamp &&
              e.event_type === data.event_type &&
              e.agent === data.agent
          );
          if (isDuplicate) return prev;
          return [...prev, data];
        });

        // Update task status based on received events
        if (data.event_type === 'TASK_STARTED') {
          setTaskStatus('RUNNING');
        } else if (data.event_type === 'FINAL_RESULT') {
          setFinalResult(data.payload.final_result || null);
        } else if (data.event_type === 'TASK_COMPLETED') {
          setTaskStatus('COMPLETED');
          if (data.payload.final_result) {
            setFinalResult(data.payload.final_result);
          }
        } else if (data.event_type === 'TASK_FAILED') {
          setTaskStatus('FAILED');
          setErrorMessage(data.payload.error || 'Execution failed.');
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (err) => {
      console.warn('WebSocket error observed:', err);
      setConnectionStatus('error');
    };

    ws.onclose = () => {
      setConnectionStatus('disconnected');
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
    };

    return () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [taskId]);

  return {
    events,
    connectionStatus,
    taskStatus,
    finalResult,
    errorMessage,
    clearEvents,
  };
}

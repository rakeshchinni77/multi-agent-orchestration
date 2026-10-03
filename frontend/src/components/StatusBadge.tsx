import React from 'react';
import { TaskStatus } from '../types/events';
import { CheckCircle2, Clock, AlertCircle, Loader2 } from 'lucide-react';

interface StatusBadgeProps {
  status: TaskStatus;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  switch (status) {
    case 'RUNNING':
      return (
        <span className="badge badge-running">
          <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
          RUNNING
        </span>
      );
    case 'COMPLETED':
      return (
        <span className="badge badge-completed">
          <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
          COMPLETED
        </span>
      );
    case 'FAILED':
      return (
        <span className="badge badge-failed">
          <AlertCircle className="w-3.5 h-3.5 mr-1.5" />
          FAILED
        </span>
      );
    case 'PENDING':
    default:
      return (
        <span className="badge badge-pending">
          <Clock className="w-3.5 h-3.5 mr-1.5" />
          PENDING
        </span>
      );
  }
};

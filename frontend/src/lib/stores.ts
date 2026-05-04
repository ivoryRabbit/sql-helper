import { writable, get } from 'svelte/store';
import type { Session, Message, DataSource } from './types';

const makeId = () => crypto.randomUUID();

export const sessions = writable<Session[]>([]);

// IDs of sessions currently shown as tabs (subset of sessions)
export const openTabIds = writable<string[]>([]);

export const activeSessionId = writable<string | null>(null);

export const activeMenu = writable<string>('sql-assistant');

// SQL carried over when "Go to analysis" is clicked
export const pendingSql = writable<string | null>(null);

// Global data source state — shared across all feature pages
export const dataSources = writable<DataSource[]>([]);
export const selectedDataSource = writable<DataSource | null>(null);

// Left sidebar collapsed state (shared between NavSidebar and AppBar)
export const sidebarCollapsed = writable(false);

/** Create a new session and open it as a tab. */
export function addSession(dataSourceId: string | null = null): void {
  const id = makeId();
  const source = dataSourceId
    ? get(dataSources).find(s => s.id === dataSourceId) ?? null
    : null;
  sessions.update(list => [
    ...list,
    {
      id,
      title: 'New Conversation',
      dataSourceId,
      createdAt: new Date(),
      messages: [
        {
          id: makeId(),
          role: 'assistant',
          content: source
            ? `안녕하세요! ${source.name}에 대해 궁금한 것을 질문해 주세요.`
            : '안녕하세요! 새 대화를 시작합니다.',
          createdAt: new Date(),
        },
      ],
    },
  ]);
  openTabIds.update(ids => [...ids, id]);
  activeSessionId.set(id);
  activeMenu.set('sql-assistant');
}

/** Close a tab without deleting the session (it stays in session history). */
export function closeTab(id: string): void {
  const ids = get(openTabIds);
  const remaining = ids.filter(i => i !== id);
  openTabIds.set(remaining);

  if (get(activeSessionId) === id) {
    if (remaining.length > 0) {
      activeSessionId.set(remaining[remaining.length - 1]);
    } else {
      // No open tabs — show most recent session from history without a tab
      const latest = get(sessions).slice().reverse()[0];
      if (latest) activeSessionId.set(latest.id);
    }
  }
}

/** Open an existing session as a tab (or bring it to front if already open). */
export function openSessionInTab(sessionId: string): void {
  openTabIds.update(ids =>
    ids.includes(sessionId) ? ids : [...ids, sessionId],
  );
  activeSessionId.set(sessionId);
  activeMenu.set('sql-assistant');
}

/** Click a connection: resume its most recent session, or create a new one. */
export function openOrCreateSession(dataSource: DataSource): void {
  const list = get(sessions);
  const existing = list
    .filter(s => s.dataSourceId === dataSource.id)
    .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())[0];

  selectedDataSource.set(dataSource);

  if (existing) {
    openSessionInTab(existing.id);
  } else {
    addSession(dataSource.id);
  }
}

/** Permanently delete a session and close its tab. */
export function removeSession(id: string): void {
  closeTab(id);
  sessions.update(s => s.filter(x => x.id !== id));
}

export function addMessage(sessionId: string, message: Message): void {
  sessions.update(list =>
    list.map(s => {
      if (s.id !== sessionId) return s;
      const isFirstUser =
        message.role === 'user' && s.messages.every(m => m.role === 'assistant');
      return {
        ...s,
        title: isFirstUser
          ? message.content.slice(0, 28) + (message.content.length > 28 ? '…' : '')
          : s.title,
        messages: [...s.messages, message],
      };
    }),
  );
}

import { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertCircle,
  Building2,
  CheckCheck,
  ChevronLeft,
  Circle,
  FileText,
  Image as ImageIcon,
  Loader2,
  Lock,
  Megaphone,
  MessageCircle,
  Paperclip,
  Plus,
  Search,
  Send,
  ShieldCheck,
  Users,
  X,
} from 'lucide-react';
import {
  bootstrapMessenger,
  createCustomConversation,
  createDirectConversation,
  fetchMessengerDirectory,
  fetchMessengerMessages,
  fetchMessengerUnreadCount,
  markMessengerConversationRead,
  sendMessengerMessage,
  uploadMessengerAttachment,
} from '../../api/messenger';

const conversationIcons = {
  direct: MessageCircle,
  department: Building2,
  custom: Users,
  announcement: Megaphone,
};

function initials(name = '') {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  return parts.slice(0, 2).map((part) => part[0]).join('').toUpperCase();
}

function formatTime(value) {
  if (!value) return '';
  const date = new Date(value);
  const today = new Date();
  const isToday = date.toDateString() === today.toDateString();
  return new Intl.DateTimeFormat(undefined, {
    hour: isToday ? 'numeric' : undefined,
    minute: isToday ? '2-digit' : undefined,
    month: isToday ? undefined : 'short',
    day: isToday ? undefined : 'numeric',
  }).format(date);
}

function attachmentIcon(contentType = '') {
  return contentType.startsWith('image/') ? ImageIcon : FileText;
}

function TypeBadge({ type }) {
  const labels = {
    direct: 'DM',
    department: 'Dept',
    custom: 'Group',
    announcement: 'Notice',
  };
  return (
    <span className="inline-flex items-center rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] font-bold uppercase text-slate-500">
      {labels[type] || type}
    </span>
  );
}

function Avatar({ name, type }) {
  const Icon = conversationIcons[type] || MessageCircle;
  if (type === 'direct') {
    return (
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded bg-slate-900 text-[11px] font-bold text-white">
        {initials(name)}
      </div>
    );
  }
  return (
    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded bg-white text-slate-700 ring-1 ring-slate-200">
      <Icon size={17} />
    </div>
  );
}

function EmptyState({ title, body }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-8 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded bg-slate-100 text-slate-600">
        <ShieldCheck size={22} />
      </div>
      <p className="text-sm font-semibold text-slate-900">{title}</p>
      <p className="mt-1 max-w-xs text-xs leading-5 text-slate-500">{body}</p>
    </div>
  );
}

export default function SecureMessengerWidget() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [directoryLoading, setDirectoryLoading] = useState(false);
  const [error, setError] = useState('');
  const [policy, setPolicy] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [directory, setDirectory] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [composerText, setComposerText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [sending, setSending] = useState(false);
  const [mode, setMode] = useState('inbox');
  const [groupTitle, setGroupTitle] = useState('');
  const [selectedMemberIds, setSelectedMemberIds] = useState([]);
  const [mobileListVisible, setMobileListVisible] = useState(true);
  const fileInputRef = useRef(null);
  const messageEndRef = useRef(null);

  const filteredConversations = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    if (!term) return conversations;
    return conversations.filter((conversation) => {
      const memberText = conversation.members?.map((member) => member.name).join(' ') || '';
      return `${conversation.title} ${conversation.type} ${memberText}`.toLowerCase().includes(term);
    });
  }, [conversations, searchTerm]);

  const filteredDirectory = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    return directory.filter((user) => {
      if (!term) return true;
      return `${user.name} ${user.email} ${user.department || ''}`.toLowerCase().includes(term);
    });
  }, [directory, searchTerm]);

  const refreshUnread = async () => {
    try {
      const data = await fetchMessengerUnreadCount();
      setUnreadCount(data.unread_count || 0);
    } catch {
      setUnreadCount(0);
    }
  };

  const refreshConversations = async (activeConversationId = activeConversation?.id) => {
    const data = await bootstrapMessenger();
    setPolicy(data.policy);
    setCurrentUser(data.current_user);
    setConversations(data.conversations || []);
    setUnreadCount(data.unread_count || 0);
    if (activeConversationId) {
      const updated = data.conversations?.find((item) => item.id === activeConversationId);
      if (updated) setActiveConversation(updated);
    }
  };

  const loadDirectory = async () => {
    setDirectoryLoading(true);
    try {
      const data = await fetchMessengerDirectory();
      setDirectory(data || []);
    } finally {
      setDirectoryLoading(false);
    }
  };

  const loadWidget = async () => {
    setLoading(true);
    setError('');
    try {
      const [bootstrapData, directoryData] = await Promise.all([
        bootstrapMessenger(),
        fetchMessengerDirectory(),
      ]);
      setPolicy(bootstrapData.policy);
      setCurrentUser(bootstrapData.current_user);
      setConversations(bootstrapData.conversations || []);
      setUnreadCount(bootstrapData.unread_count || 0);
      setDirectory(directoryData || []);
      if (!activeConversation && bootstrapData.conversations?.length) {
        const firstConversation = bootstrapData.conversations[0];
        setActiveConversation(firstConversation);
        setMobileListVisible(false);
        const firstMessages = await fetchMessengerMessages(firstConversation.id);
        setMessages(firstMessages || []);
        await markMessengerConversationRead(firstConversation.id);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Secure Messenger is temporarily unavailable.');
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (conversation) => {
    if (!conversation) return;
    setError('');
    setActiveConversation(conversation);
    setMobileListVisible(false);
    try {
      const data = await fetchMessengerMessages(conversation.id);
      setMessages(data || []);
      await markMessengerConversationRead(conversation.id);
      await refreshConversations(conversation.id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load this conversation.');
    }
  };

  useEffect(() => {
    refreshUnread();
    const interval = window.setInterval(refreshUnread, 30000);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    if (open) {
      loadWidget();
    }
  }, [open]);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages]);

  const handleSend = async () => {
    if (!activeConversation || sending) return;
    if (!composerText.trim() && !selectedFile) return;
    setSending(true);
    setError('');
    try {
      const message = selectedFile
        ? await uploadMessengerAttachment(activeConversation.id, selectedFile, composerText.trim())
        : await sendMessengerMessage(activeConversation.id, composerText.trim());
      setMessages((items) => [...items, message]);
      setComposerText('');
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      await refreshConversations();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not send the message.');
    } finally {
      setSending(false);
    }
  };

  const handleCreateDirect = async (recipientId) => {
    setError('');
    try {
      const conversation = await createDirectConversation(recipientId);
      await refreshConversations();
      await loadMessages(conversation);
      setMode('inbox');
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not open direct message.');
    }
  };

  const toggleMember = (memberId) => {
    setSelectedMemberIds((current) => (
      current.includes(memberId)
        ? current.filter((id) => id !== memberId)
        : [...current, memberId]
    ));
  };

  const handleCreateGroup = async () => {
    if (!groupTitle.trim()) return;
    setError('');
    try {
      const conversation = await createCustomConversation(groupTitle.trim(), selectedMemberIds);
      setGroupTitle('');
      setSelectedMemberIds([]);
      await refreshConversations();
      await loadMessages(conversation);
      setMode('inbox');
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create group.');
    }
  };

  const activeMemberNames = activeConversation?.members
    ?.filter((member) => member.id !== currentUser?.id)
    .map((member) => member.name)
    .slice(0, 3)
    .join(', ');

  return (
    <>
      <button
        type="button"
        aria-label="Open secure messenger"
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-slate-950 text-white shadow-2xl shadow-slate-950/30 ring-1 ring-white/10 transition hover:scale-105 hover:bg-slate-900 focus:outline-none focus:ring-4 focus:ring-slate-400/30"
      >
        <MessageCircle size={24} />
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex min-h-5 min-w-5 items-center justify-center rounded-full bg-amber-400 px-1.5 text-[11px] font-black text-slate-950 ring-2 ring-white">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-end justify-end bg-slate-950/20 p-0 backdrop-blur-[2px] sm:p-5">
          <section className="flex h-[100dvh] w-full overflow-hidden bg-white shadow-2xl ring-1 ring-slate-200 sm:h-[min(720px,calc(100vh-40px))] sm:max-w-5xl sm:rounded-lg">
            <aside className={`${mobileListVisible ? 'flex' : 'hidden'} w-full flex-col border-r border-slate-200 bg-slate-50 sm:flex sm:w-[340px]`}>
              <header className="border-b border-slate-200 bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-base font-black text-slate-950">Secure Messenger</h2>
                      <span className="inline-flex items-center gap-1 rounded bg-emerald-50 px-2 py-1 text-[10px] font-bold uppercase text-emerald-700 ring-1 ring-emerald-100">
                        <Lock size={11} />
                        Add-on
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">Private staff chat. No RAG ingestion.</p>
                  </div>
                  <button
                    type="button"
                    aria-label="Close secure messenger"
                    onClick={() => setOpen(false)}
                    className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                  >
                    <X size={18} />
                  </button>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-1 rounded bg-slate-100 p-1">
                  <button
                    type="button"
                    onClick={() => setMode('inbox')}
                    className={`rounded px-3 py-2 text-xs font-bold ${mode === 'inbox' ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-900'}`}
                  >
                    Inbox
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setMode('new');
                      loadDirectory();
                    }}
                    className={`rounded px-3 py-2 text-xs font-bold ${mode === 'new' ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-900'}`}
                  >
                    New
                  </button>
                </div>

                <label className="mt-3 flex items-center gap-2 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500 focus-within:border-slate-400 focus-within:bg-white">
                  <Search size={16} />
                  <input
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                    placeholder={mode === 'new' ? 'Find staff' : 'Search conversations'}
                    className="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
                  />
                </label>
              </header>

              {error && (
                <div className="mx-3 mt-3 flex items-start gap-2 rounded border border-red-100 bg-red-50 p-3 text-xs text-red-700">
                  <AlertCircle size={15} className="mt-0.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {mode === 'inbox' ? (
                <div className="flex-1 overflow-y-auto p-2">
                  {loading ? (
                    <div className="flex h-full items-center justify-center text-slate-500">
                      <Loader2 size={20} className="animate-spin" />
                    </div>
                  ) : filteredConversations.length === 0 ? (
                    <EmptyState title="No conversations yet" body="Department channels appear automatically when staff departments are configured." />
                  ) : (
                    <div className="space-y-1">
                      {filteredConversations.map((conversation) => (
                        <button
                          key={conversation.id}
                          type="button"
                          onClick={() => loadMessages(conversation)}
                          className={`flex w-full items-center gap-3 rounded p-2.5 text-left transition ${
                            activeConversation?.id === conversation.id
                              ? 'bg-white shadow-sm ring-1 ring-slate-200'
                              : 'hover:bg-white hover:shadow-sm'
                          }`}
                        >
                          <Avatar name={conversation.title} type={conversation.type} />
                          <span className="min-w-0 flex-1">
                            <span className="flex items-center gap-2">
                              <span className="truncate text-sm font-bold text-slate-900">{conversation.title}</span>
                              <TypeBadge type={conversation.type} />
                            </span>
                            <span className="mt-0.5 block truncate text-xs text-slate-500">
                              {conversation.last_message?.content || `${conversation.members?.length || 0} members`}
                            </span>
                          </span>
                          <span className="flex shrink-0 flex-col items-end gap-1">
                            <span className="text-[10px] font-semibold text-slate-400">{formatTime(conversation.last_message?.created_at)}</span>
                            {conversation.unread_count > 0 ? (
                              <span className="flex min-h-5 min-w-5 items-center justify-center rounded-full bg-slate-950 px-1.5 text-[10px] font-bold text-white">
                                {conversation.unread_count}
                              </span>
                            ) : (
                              <Circle size={8} className="text-slate-300" />
                            )}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex-1 overflow-y-auto p-3">
                  <div className="rounded border border-slate-200 bg-white p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-xs font-black uppercase text-slate-500">Custom Group</p>
                      <span className="text-[11px] text-slate-400">{selectedMemberIds.length} selected</span>
                    </div>
                    <input
                      value={groupTitle}
                      onChange={(event) => setGroupTitle(event.target.value)}
                      placeholder="Group name"
                      className="mt-3 w-full rounded border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-500"
                    />
                    <button
                      type="button"
                      onClick={handleCreateGroup}
                      disabled={!groupTitle.trim()}
                      className="mt-3 flex w-full items-center justify-center gap-2 rounded bg-slate-950 px-3 py-2 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                    >
                      <Plus size={16} />
                      Create Group
                    </button>
                  </div>

                  <div className="mt-3 space-y-1">
                    {directoryLoading ? (
                      <div className="flex justify-center py-8 text-slate-400">
                        <Loader2 size={18} className="animate-spin" />
                      </div>
                    ) : filteredDirectory.map((user) => (
                      <div key={user.id} className="flex items-center gap-3 rounded border border-slate-100 bg-white p-2.5">
                        <div className="flex h-8 w-8 items-center justify-center rounded bg-slate-900 text-[10px] font-bold text-white">
                          {initials(user.name)}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-bold text-slate-900">{user.name}</p>
                          <p className="truncate text-xs text-slate-500">{user.department || user.email}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleCreateDirect(user.id)}
                          className="rounded border border-slate-200 px-2.5 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-50"
                        >
                          DM
                        </button>
                        <button
                          type="button"
                          aria-label={`Toggle ${user.name} in group`}
                          onClick={() => toggleMember(user.id)}
                          className={`rounded px-2.5 py-1.5 text-xs font-bold ${
                            selectedMemberIds.includes(user.id)
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                          }`}
                        >
                          {selectedMemberIds.includes(user.id) ? 'Added' : 'Add'}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </aside>

            <div className={`${mobileListVisible ? 'hidden' : 'flex'} min-w-0 flex-1 flex-col bg-white sm:flex`}>
              {activeConversation ? (
                <>
                  <header className="flex items-center gap-3 border-b border-slate-200 px-4 py-3">
                    <button
                      type="button"
                      aria-label="Show conversations"
                      onClick={() => setMobileListVisible(true)}
                      className="rounded p-1.5 text-slate-500 hover:bg-slate-100 sm:hidden"
                    >
                      <ChevronLeft size={20} />
                    </button>
                    <Avatar name={activeConversation.title} type={activeConversation.type} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="truncate text-sm font-black text-slate-950">{activeConversation.title}</h3>
                        <TypeBadge type={activeConversation.type} />
                      </div>
                      <p className="truncate text-xs text-slate-500">
                        {activeMemberNames || `${activeConversation.members?.length || 0} members`}
                      </p>
                    </div>
                    <div className="hidden items-center gap-1 rounded bg-slate-50 px-2 py-1 text-[11px] font-semibold text-slate-500 ring-1 ring-slate-200 sm:flex">
                      <ShieldCheck size={13} />
                      Isolated
                    </div>
                  </header>

                  <div className="flex-1 overflow-y-auto bg-slate-50 px-4 py-4">
                    {messages.length === 0 ? (
                      <EmptyState title="Start the conversation" body="Messages and files stay inside the Secure Messenger add-on and are not indexed by RAG." />
                    ) : (
                      <div className="space-y-3">
                        {messages.map((message) => {
                          const mine = message.sender?.id === currentUser?.id;
                          return (
                            <div key={message.id} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
                              <div className={`max-w-[82%] rounded-lg px-3 py-2 shadow-sm ring-1 ${
                                mine
                                  ? 'bg-slate-950 text-white ring-slate-950'
                                  : 'bg-white text-slate-900 ring-slate-200'
                              }`}
                              >
                                <div className="mb-1 flex items-center gap-2">
                                  <span className={`text-[11px] font-bold ${mine ? 'text-slate-200' : 'text-slate-500'}`}>
                                    {mine ? 'You' : message.sender?.name}
                                  </span>
                                  <span className={`text-[10px] ${mine ? 'text-slate-400' : 'text-slate-400'}`}>
                                    {formatTime(message.created_at)}
                                  </span>
                                </div>
                                <p className="whitespace-pre-wrap break-words text-sm leading-5">{message.content}</p>
                                {message.attachments?.length > 0 && (
                                  <div className="mt-2 space-y-1.5">
                                    {message.attachments.map((attachment) => {
                                      const AttachmentIcon = attachmentIcon(attachment.content_type);
                                      return (
                                        <a
                                          key={attachment.id}
                                          href={attachment.download_url}
                                          target="_blank"
                                          rel="noreferrer"
                                          className={`flex items-center gap-2 rounded border px-2.5 py-2 text-xs ${
                                            mine
                                              ? 'border-white/15 bg-white/10 text-white hover:bg-white/15'
                                              : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                                          }`}
                                        >
                                          <AttachmentIcon size={15} />
                                          <span className="min-w-0 flex-1 truncate">{attachment.original_filename}</span>
                                          <span className={mine ? 'text-slate-300' : 'text-slate-400'}>
                                            {Math.max(1, Math.round(attachment.size_bytes / 1024))} KB
                                          </span>
                                        </a>
                                      );
                                    })}
                                  </div>
                                )}
                                {mine && (
                                  <div className="mt-1 flex justify-end text-slate-400">
                                    <CheckCheck size={13} />
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        })}
                        <div ref={messageEndRef} />
                      </div>
                    )}
                  </div>

                  {activeConversation.type === 'announcement' && activeConversation.role === 'readonly' ? (
                    <div className="border-t border-slate-200 bg-white p-4 text-center text-xs font-semibold text-slate-500">
                      Announcement channel is read-only.
                    </div>
                  ) : (
                    <footer className="border-t border-slate-200 bg-white p-3">
                      {selectedFile && (
                        <div className="mb-2 flex items-center gap-2 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
                          <Paperclip size={14} />
                          <span className="min-w-0 flex-1 truncate">{selectedFile.name}</span>
                          <button
                            type="button"
                            aria-label="Remove selected file"
                            onClick={() => {
                              setSelectedFile(null);
                              if (fileInputRef.current) fileInputRef.current.value = '';
                            }}
                            className="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700"
                          >
                            <X size={13} />
                          </button>
                        </div>
                      )}
                      <div className="flex items-end gap-2">
                        <input
                          ref={fileInputRef}
                          type="file"
                          className="hidden"
                          onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
                        />
                        <button
                          type="button"
                          aria-label="Attach file"
                          onClick={() => fileInputRef.current?.click()}
                          className="mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded border border-slate-200 text-slate-600 hover:bg-slate-50"
                        >
                          <Paperclip size={18} />
                        </button>
                        <textarea
                          value={composerText}
                          onChange={(event) => setComposerText(event.target.value)}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter' && !event.shiftKey) {
                              event.preventDefault();
                              handleSend();
                            }
                          }}
                          rows={1}
                          placeholder={selectedFile ? 'Add a caption' : 'Message'}
                          className="max-h-28 min-h-10 flex-1 resize-none rounded border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-500"
                        />
                        <button
                          type="button"
                          aria-label="Send message"
                          onClick={handleSend}
                          disabled={sending || (!composerText.trim() && !selectedFile)}
                          className="mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded bg-slate-950 text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                        >
                          {sending ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                        </button>
                      </div>
                      <div className="mt-2 flex items-center gap-1 text-[11px] font-medium text-slate-400">
                        <Lock size={12} />
                        Files stay in messenger storage and are not sent to LipiCore RAG. Max {policy?.max_file_size_mb || 25} MB.
                      </div>
                    </footer>
                  )}
                </>
              ) : (
                <EmptyState title="Select a conversation" body="Open a department channel, direct message, group, or announcement." />
              )}
            </div>
          </section>
        </div>
      )}
    </>
  );
}

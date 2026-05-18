# Secure Messenger Add-on Phase 1 Design

## Goal

Create a separate, deployable LipiCore Secure Messenger add-on that gives bank staff internal messaging from inside LipiCore without allowing messenger data to enter the AI, RAG, embedding, or document-ingestion systems.

The add-on is not a Slack clone and not part of LipiCore Core. It is a private staff communication layer hosted in the same bank-controlled environment and exposed through a compact Messenger-style widget.

## Non-Negotiable Data Boundary

Messenger data must never enter LipiCore RAG.

- No chat messages are embedded.
- No chat attachments are sent to the vector database.
- No chat data is used as AI context.
- No AI summarization of messenger conversations.
- No automatic or manual "send to AI" action in Phase 1.
- No shared document ingestion pipeline with LipiCore documents.
- LipiCore Core must not have database or object-storage credentials that can read messenger messages or files.

This boundary should be enforced technically with separate service credentials, separate database tables or database, separate attachment storage, and a narrow integration API that exposes only identity, unread counts, and widget session bootstrapping.

## Product Scope

Phase 1 delivers a web-only secure messenger widget inside LipiCore.

Included:

- Floating Messenger-style button in LipiCore.
- Compact chat panel with recent conversations and active conversation view.
- Direct messages between staff.
- Automatic department channels.
- Staff-created custom groups.
- Admin or manager announcement channels.
- Secure file and image sharing inside the add-on.
- Unread counts and message delivery/read status.
- Local keyword search inside messenger only.
- Audit events for message, file, membership, and admin activity.
- Bank-level retention and attachment policy settings.

Excluded:

- Mobile app.
- Face ID, fingerprint, PIN, or mobile device controls.
- Push notifications.
- Voice/video calls.
- External guests.
- AI features.
- RAG ingestion.
- LipiCore document-library integration.
- Export workflows for normal staff.

## Channel Model

### Direct Messages

One-to-one staff conversations. Membership is exactly the two users involved. Attachments are allowed if bank policy permits them.

### Department Channels

Department channels are created automatically from `User.department`.

- A bank gets one department channel per active department.
- Users are added or removed when their department changes.
- Staff cannot manually add outsiders to a department channel.
- Admins may rename the display label, but membership remains department-derived.
- Empty department channels can be hidden or archived by policy.

### Custom Groups

Regular staff may create custom groups.

- The creator becomes the group owner.
- Owners can add and remove members.
- Bank admins can disable groups, inspect metadata, and enforce retention.
- Custom groups may include cross-department members unless disabled by bank policy.
- Banks can configure maximum group size.

### Announcement Channels

Announcement channels are controlled broadcast spaces for compliance notices, IT downtime, HR/admin updates, and policy reminders.

- Normal staff can read but not post.
- Bank admins and configured manager roles can post.
- Replies are disabled in Phase 1 unless later approved.

## Attachments

Phase 1 supports secure file and image sharing in the web widget.

- Files are stored only in the messenger add-on storage.
- Files are encrypted at rest.
- Access is limited to conversation members.
- File type and size limits are bank-configurable.
- Upload, view, download, delete, and internal share events are audited.
- Attachments are searchable only by filename and message metadata in Phase 1, not by file contents.
- Attachments do not enter LipiCore document storage, RAG, embeddings, or AI context.

The Phase 2 mobile app will add stricter in-app-view-only controls. Phase 1 web may allow browser downloads only if bank policy enables them.

## Architecture

LipiCore Core hosts the widget shell and provides identity. The messenger add-on owns all chat behavior and all chat data.

```text
LipiCore Core
  - login/session
  - user identity and role source
  - sidebar/widget host
  - unread badge display
  - no message/file read access

Secure Messenger Add-on
  - chat API
  - realtime transport
  - message database
  - attachment storage
  - local keyword search
  - audit logs
  - retention policies

LipiCore AI/RAG
  - no connection to messenger data
  - no embeddings
  - no ingestion
  - no summarization
```

## Integration Contracts

The integration between LipiCore and the add-on should stay narrow.

Allowed integration:

- SSO or session token handoff.
- User id, bank id, role, name, department, and active status sync.
- Widget bootstrapping.
- Unread count endpoint.
- Optional deep link to a conversation id.
- Admin enable/disable setting per bank.

Disallowed integration:

- API access from LipiCore Core to retrieve message history.
- API access from LipiCore Core to retrieve attachment contents.
- Any API that bulk-exports messenger data to RAG or document ingestion.
- Any AI endpoint consuming messenger messages or attachments.

## Backend Components

The add-on backend should provide:

- Conversation service for DMs, department channels, custom groups, and announcements.
- Membership service with automatic department membership reconciliation.
- Message service with delivery/read state.
- Attachment service with policy validation and private storage.
- Search service for messenger-only keyword search.
- Audit service for compliance logs.
- Admin policy service for retention, file limits, and group controls.
- Realtime gateway using WebSocket or SSE depending on deployment constraints.

## Frontend Components

The LipiCore frontend should add only the host surface:

- Floating messenger launcher with unread badge.
- Embedded widget frame or mounted add-on component.
- Authentication/session bootstrap call.

The add-on UI owns:

- Conversation list.
- Conversation view.
- Message composer.
- Attachment picker.
- Member list.
- Group creation flow.
- Search panel.
- Admin/policy screens if exposed in Phase 1.

## Security And Governance

- Messenger service uses separate credentials from LipiCore Core.
- Message and attachment access is checked against conversation membership.
- Bank id is enforced on every query.
- Admin actions are audited.
- Attachment policy is enforced before storage.
- Deleted or expired attachments become inaccessible immediately.
- Retention jobs operate only inside messenger storage.
- Logs must avoid storing attachment contents or full message bodies unless explicitly required by bank policy.

## Error Handling

- If the messenger add-on is unavailable, LipiCore should show the widget as temporarily unavailable without affecting core AI/document workflows.
- Failed message sends should remain in the composer or show retry state.
- Failed uploads should show a clear failure reason such as file type, size, policy, or network error.
- Department sync failures should be visible to admins and retried safely.

## Testing

Backend tests:

- Bank isolation for conversations, messages, attachments, and unread counts.
- Department channel auto-create and membership sync.
- Custom group ownership and membership permissions.
- Announcement posting restrictions.
- Attachment policy enforcement.
- No API path exposes message or attachment bulk export to LipiCore Core.
- Retention expiry removes access.

Frontend tests:

- Widget opens and closes from LipiCore.
- Unread badge renders from add-on count.
- DM, department channel, custom group, and announcement views render.
- Upload errors are visible.
- LipiCore remains usable when the add-on API is down.

Security verification:

- Confirm LipiCore Core credentials cannot read messenger database or object storage.
- Confirm no messenger routes call RAG, embedding, document ingestion, or AI services.
- Confirm audit events are written for file upload, view, download, delete, and membership changes.


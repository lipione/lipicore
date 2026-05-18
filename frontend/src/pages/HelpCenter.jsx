import { useMemo, useState } from 'react';
import { useBranding } from '../contexts/BrandingContext';

const CATEGORIES = [
  {
    icon: 'chat',
    title: 'Using the Chat Assistant',
    description: 'Ask approved bank knowledge, draft customer replies, summarize files, translate, and understand answer trust states.',
    tags: ['Ask Knowledge', 'Drafts', 'General Answers', 'Evidence'],
  },
  {
    icon: 'folder_managed',
    title: 'Document Governance',
    description: 'Upload files, approve knowledge sources, handle failed ingestion, and know when documents are ready for RAG.',
    tags: ['Upload', 'Approve', 'Supersede', 'Failed Files'],
    wide: true,
  },
  {
    icon: 'verified',
    title: 'Citations & Accuracy',
    description: 'Review source passages, understand source-backed answers, and escalate unsupported or low-confidence answers.',
    tags: ['Citations', 'Passages', 'No Source', 'Evaluation'],
    wide: true,
  },
  {
    icon: 'admin_panel_settings',
    title: 'Admin Operations',
    description: 'Manage users, roles, branding, audit logs, reports, and support contacts for each bank deployment.',
    tags: ['Users', 'Roles', 'Branding', 'Reports'],
  },
];

const ARTICLES = [
  {
    icon: 'psychology',
    title: 'When should staff use Ask Bank Knowledge?',
    meta: 'Use for questions that must be answered from approved policy, circular, procedure, or internal knowledge documents.',
    body: 'Use Ask Bank Knowledge when the answer must be source-backed. If the assistant cannot find enough approved evidence, it should say so instead of inventing a policy answer.',
  },
  {
    icon: 'description',
    title: 'How do citations and evidence passages work?',
    meta: 'Every source-backed answer should expose the document title, page/chunk metadata, and source passage where available.',
    body: 'Staff should verify important answers by opening the evidence panel and reviewing the cited passage. A citation is not a legal approval; it is a trace to the knowledge used by the model.',
  },
  {
    icon: 'folder_open',
    title: 'What makes a document usable by RAG?',
    meta: 'Documents must upload, extract, chunk, embed, index, and be approved or ready before they can reliably answer questions.',
    body: 'Failed documents reduce retrieval coverage. Processing documents may not appear in answers yet. Approved/indexed documents are the safest source set for bank-wide staff usage.',
  },
  {
    icon: 'support_agent',
    title: 'Customer-care staff workflow',
    meta: 'Use Draft mode for customer replies and Ask Knowledge for policy verification.',
    body: 'For customer support, first ask the policy question in Ask Bank Knowledge. Then use Draft mode to write a response. Staff should review tone, facts, and customer-specific details before sending.',
  },
  {
    icon: 'policy',
    title: 'What should admins review in Audit Logs?',
    meta: 'Review login activity, document uploads, task execution, failed requests, and any high-risk metadata.',
    body: 'Audit logs are operational evidence. Export logs for review meetings and investigate repeated failures, prompt-injection rejections, document errors, or unusual usage patterns.',
  },
  {
    icon: 'warning',
    title: 'Known MVP limitations',
    meta: 'This product is not yet a core-banking integration or autonomous decision system.',
    body: 'Do not treat AI output as final approval. The MVP does not replace compliance officers, supervisors, or bank operating procedures. High-impact decisions need human review.',
  },
];

export default function HelpCenter() {
  const [query, setQuery] = useState('');
  const [selectedArticle, setSelectedArticle] = useState(ARTICLES[0]);
  const branding = useBranding();
  const supportContact = branding.support_contact || 'enterprise@lipicore.com';

  const filteredArticles = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return ARTICLES;
    return ARTICLES.filter(article =>
      `${article.title} ${article.meta} ${article.body}`.toLowerCase().includes(q)
    );
  }, [query]);

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <section className="mb-xl bg-primary-container rounded-lg p-xl text-white relative overflow-hidden">
        <div className="absolute inset-y-0 right-0 w-1/3 opacity-30 bg-[radial-gradient(circle_at_center,#316bf3_0%,transparent_70%)]" />
        <div className="relative z-10 max-w-3xl">
          <p className="font-label-caps text-label-caps text-on-primary-container uppercase tracking-widest mb-md">
            {branding.product_name} Support
          </p>
          <h1 className="font-h1 text-h1 mb-md">Help Center</h1>
          <p className="font-body-lg text-body-lg text-slate-300 mb-lg">
            Practical guidance for bank staff using private AI, approved knowledge, citations, audit evidence, and admin workflows.
          </p>
          <div className="relative max-w-xl">
            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-[20px]">
              search
            </span>
            <input
              className="w-full bg-white text-on-surface pl-12 pr-4 py-3 rounded-lg border-0 focus:ring-2 focus:ring-secondary text-body-sm"
              placeholder="Search help topics..."
              value={query}
              onChange={e => setQuery(e.target.value)}
            />
          </div>
        </div>
      </section>

      <section className="grid grid-cols-12 gap-gutter mb-xl">
        {CATEGORIES.map(category => (
          <article
            key={category.title}
            className={`${category.wide ? 'col-span-12 lg:col-span-8' : 'col-span-12 lg:col-span-4'} bg-white border border-slate-200 p-lg rounded-lg hover:border-secondary transition-colors`}
          >
            <div className="flex items-start justify-between gap-md">
              <div className="w-12 h-12 bg-slate-50 flex items-center justify-center rounded-lg flex-shrink-0">
                <span className="material-symbols-outlined text-secondary">{category.icon}</span>
              </div>
              <span className="text-xs font-bold text-secondary bg-blue-50 px-2 py-1 rounded">
                Guide
              </span>
            </div>
            <h2 className="font-h2 text-h2 text-on-surface mt-lg mb-sm">{category.title}</h2>
            <p className="text-body-sm text-on-surface-variant mb-lg max-w-2xl">{category.description}</p>
            <div className="flex flex-wrap gap-sm">
              {category.tags.map(tag => (
                <span key={tag} className="px-3 py-1 bg-surface-container text-secondary text-xs font-bold rounded-full">
                  {tag}
                </span>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section className="grid grid-cols-12 gap-gutter">
        <div className="col-span-12 lg:col-span-5">
          <h3 className="font-label-caps text-label-caps text-on-surface uppercase tracking-widest mb-md">
            Operational Articles
          </h3>
          <div className="space-y-sm">
            {filteredArticles.length === 0 ? (
              <div className="p-lg bg-white border border-slate-200 rounded-lg text-slate-400 text-center">
                No help articles match this search.
              </div>
            ) : filteredArticles.map(article => (
              <button
                key={article.title}
                onClick={() => setSelectedArticle(article)}
                className={`w-full flex items-center justify-between p-md border rounded-lg text-left transition-all ${
                  selectedArticle.title === article.title
                    ? 'bg-white border-secondary shadow-card'
                    : 'bg-white border-slate-200 hover:shadow-card'
                }`}
              >
                <div className="flex items-center gap-md min-w-0">
                  <span className="material-symbols-outlined text-slate-400 flex-shrink-0">{article.icon}</span>
                  <div className="min-w-0">
                    <p className="font-bold text-on-surface truncate">{article.title}</p>
                    <p className="text-xs text-slate-400 truncate">{article.meta}</p>
                  </div>
                </div>
                <span className="material-symbols-outlined text-slate-300 flex-shrink-0">chevron_right</span>
              </button>
            ))}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4">
          <div className="bg-white border border-slate-200 p-lg rounded-lg min-h-[360px]">
            <div className="flex items-start gap-md mb-lg">
              <div className="w-11 h-11 bg-slate-50 rounded-lg flex items-center justify-center">
                <span className="material-symbols-outlined text-secondary">{selectedArticle.icon}</span>
              </div>
              <div>
                <h2 className="font-h2 text-h2 text-on-surface">{selectedArticle.title}</h2>
                <p className="text-xs text-slate-500 mt-xs">{selectedArticle.meta}</p>
              </div>
            </div>
            <p className="text-body-md leading-relaxed text-on-surface-variant">{selectedArticle.body}</p>
          </div>
        </div>

        <aside className="col-span-12 lg:col-span-3">
          <div className="bg-surface-container border-l-4 border-secondary p-lg rounded-lg sticky top-24">
            <h3 className="font-h2 text-h2 text-on-surface mb-sm">Need operator support?</h3>
            <p className="text-body-sm text-on-surface-variant mb-lg">
              Use your bank-approved internal support path for production incidents, account access, and document processing failures.
            </p>
            <div className="space-y-md">
              {[
                ['mail', 'Support Contact', supportContact],
                ['schedule', 'Response Priority', 'Critical incidents first'],
                ['admin_panel_settings', 'Admin Path', 'Settings > Audit Logs > Reports'],
              ].map(([icon, label, detail]) => (
                <div key={label} className="flex items-start gap-md">
                  <span className="material-symbols-outlined text-secondary">{icon}</span>
                  <div>
                    <p className="font-bold text-body-sm text-on-surface">{label}</p>
                    <p className="text-xs text-slate-500 break-words">{detail}</p>
                  </div>
                </div>
              ))}
            </div>
            <a href={`mailto:${supportContact}`}
              className="w-full mt-lg bg-primary text-white font-bold py-3 rounded-lg hover:opacity-90 transition-all flex items-center justify-center gap-2">
              Contact Support
              <span className="material-symbols-outlined text-sm">mail</span>
            </a>
          </div>
        </aside>
      </section>
    </div>
  );
}

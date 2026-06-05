export const FEATURE_GROUPS = [
  {
    label: 'Daily Work',
    features: [
      {
        key: 'employee_directory',
        label: 'Employee Search',
        desc: 'Search staff profiles, departments, branches, and internal contacts.',
        icon: 'badge',
      },
      {
        key: 'staff_inbox',
        label: 'Staff Inbox',
        desc: 'Internal task handoff, requests, and staff-to-staff work queues.',
        icon: 'inbox',
      },
    ],
  },
  {
    label: 'Communications',
    features: [
      {
        key: 'notifications',
        label: 'Notifications & Alerts',
        desc: 'Bank alerts for urgent circulars, pending reviews, and operational notices.',
        icon: 'notifications_active',
      },
      {
        key: 'ceo_messages',
        label: "CEO's Message",
        desc: 'Executive announcements shown to employees in the workspace.',
        icon: 'campaign',
      },
    ],
  },
  {
    label: 'Market Utilities',
    features: [
      {
        key: 'market_time',
        label: 'Forex, Time & Dates',
        desc: 'Bank-updated exchange rates, local time, business dates, and value-date helpers.',
        icon: 'currency_exchange',
      },
    ],
  },
  {
    label: 'Knowledge & Governance',
    features: [
      {
        key: 'knowledge_gaps',
        label: 'Knowledge Gap Queue',
        desc: 'Collect unanswered staff questions and assign missing policy updates.',
        icon: 'psychology_alt',
      },
      {
        key: 'citation_nli_verification',
        label: 'Citation NLI Verification',
        desc: 'Use NLI to validate claims against source text for stronger anti-hallucination checks.',
        icon: 'fact_check',
      },
      {
        key: 'policy_changes',
        label: 'Policy Change Watch',
        desc: 'Track policy updates and notify affected departments.',
        icon: 'rule_settings',
      },
      {
        key: 'audit_evidence_pack',
        label: 'Audit Evidence Packs',
        desc: 'Create exportable bundles with sources, answers, and approval history.',
        icon: 'fact_check',
      },
      {
        key: 'citation_semantic_verification',
        label: 'Citation Semantic Verification',
        desc: 'Enable embedding-based claim-to-source matching, including cross-language checks.',
        icon: 'psychology',
      },
    ],
  },
  {
    label: 'Banking Workflows',
    features: [
      {
        key: 'complaint_workspace',
        label: 'Complaint Workspace',
        desc: 'Draft customer complaint responses using approved policy references.',
        icon: 'support_agent',
      },
      {
        key: 'circular_impact_analyzer',
        label: 'Circular Impact Analyzer',
        desc: 'Assess new circulars against products, branches, and staff workflows.',
        icon: 'travel_explore',
      },
      {
        key: 'branch_response_builder',
        label: 'Branch Response Builder',
        desc: 'Generate consistent branch operations responses and checklists.',
        icon: 'account_balance',
      },
      {
        key: 'kyc_case_prep',
        label: 'KYC Case Prep',
        desc: 'Prepare KYC review packets with required documents and exception notes.',
        icon: 'manage_search',
      },
      {
        key: 'checklist_validator',
        label: 'Checklist Validator',
        desc: 'Validate submitted files against bank workflow and compliance checklists.',
        icon: 'checklist',
      },
    ],
  },
];

export const DEFAULT_FEATURE_FLAGS = FEATURE_GROUPS
  .flatMap((group) => group.features)
  .reduce((flags, feature) => ({ ...flags, [feature.key]: false }), {});

export const FEATURE_METADATA = FEATURE_GROUPS
  .flatMap((group) => group.features.map((feature) => ({ ...feature, group: group.label })))
  .reduce((metadata, feature) => ({ ...metadata, [feature.key]: feature }), {});

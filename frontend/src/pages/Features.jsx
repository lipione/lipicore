import { useState } from 'react';

export default function Features() {
  const [selectedCategory, setSelectedCategory] = useState('analysis');

  const categories = [
    {
      id: 'analysis',
      name: 'Document Analysis',
      icon: 'description',
      features: [
        {
          title: 'Multi-Document Processing',
          desc: 'Upload and analyze multiple documents simultaneously in organized sessions',
          details: ['Upload up to 50 MB per file', 'Batch process documents', 'Drag-and-drop upload', 'Real-time progress tracking']
        },
        {
          title: 'Financial Report Analysis',
          desc: 'Automatically extract metrics, variance analysis, and KPIs from financial documents',
          details: ['P&L extraction', 'Balance sheet analysis', 'Cash flow insights', 'Ratio calculations']
        },
        {
          title: 'Compliance Review Support',
          desc: 'Compare documents against approved directives and internal governance references for human review',
          details: ['Source-backed checklists', 'Potential gap notes', 'Citation review', 'Audit trail generation']
        },
        {
          title: 'Loan File Review Support',
          desc: 'Extract key terms and open questions from loan files for lending staff review',
          details: ['Interest rate extraction', 'Term date identification', 'Clause references', 'Risk factor notes']
        }
      ]
    },
    {
      id: 'search',
      name: 'Search & Query',
      icon: 'search',
      features: [
        {
          title: 'Semantic Search',
          desc: 'Search across all documents using natural language with context-aware results',
          details: ['Meaning-based search', 'Multi-language support', 'Instant results', 'Source attribution']
        },
        {
          title: 'Session-Based Analysis',
          desc: 'Organize analysis into sessions with full conversation history and source tracking',
          details: ['Multi-turn conversations', 'Document context', 'Session persistence', 'Export capabilities']
        },
        {
          title: 'Source Attribution',
          desc: 'Every answer is backed by specific document references with page numbers',
          details: ['Quote extraction', 'Page references', 'Confidence indicators', 'Full traceability']
        },
        {
          title: 'Multi-Language Queries',
          desc: 'Ask questions in English or Nepali and get responses in your preferred language',
          details: ['English support', 'Nepali support', 'Language detection', 'Translation aware']
        }
      ]
    },
    {
      id: 'security',
      name: 'Security & Compliance',
      icon: 'security',
      features: [
        {
          title: 'Air-Gapped Deployment',
          desc: 'Complete data isolation with no external connectivity or cloud dependencies',
          details: ['Isolated network', 'No internet required', 'Full data control', 'On-premise only']
        },
        {
          title: 'Encryption Controls',
          desc: 'Deployment-ready controls for encrypted transport, protected storage, and bank-owned key policy',
          details: ['Data encryption options', 'Transport security', 'Key management policy', 'Hardware security alignment']
        },
        {
          title: 'Audit Logging',
          desc: 'Comprehensive logging of all user actions with tamper-proof audit trails',
          details: ['User activity logs', 'Document access logs', 'Query history', 'Modification tracking']
        },
        {
          title: 'Role-Based Access Control',
          desc: 'Fine-grained permissions to control who can access what information',
          details: ['User roles', 'Permission management', 'Department-level access', 'Custom rules']
        },
        {
          title: 'Compliance-Ready Controls',
          desc: 'Controls and logs that support bank security review and third-party audit work',
          details: ['Security review support', 'Privacy controls', 'Audit evidence', 'Policy mapping']
        }
      ]
    },
    {
      id: 'performance',
      name: 'Performance & Reliability',
      icon: 'speed',
      features: [
        {
          title: 'High-Performance Processing',
          desc: 'Process documents asynchronously with capacity measured on the selected pilot infrastructure',
          details: ['Async upload queue', 'Measured API latency', 'Document processing reports', 'Capacity test evidence']
        },
        {
          title: 'Redundancy & Backup',
          desc: 'Backup, restore, and redundancy options sized by deployment tier',
          details: ['Backup policy', 'Restore drills', 'Retention settings', 'Deployment-tier design']
        },
        {
          title: 'Tiered Availability Design',
          desc: 'Availability targets depend on pilot, department, or whole-bank HA architecture',
          details: ['Tiered SLA design', 'Monitoring', 'Incident response', 'Dedicated support options']
        },
        {
          title: 'Scalability',
          desc: 'Scale from controlled pilots to department and whole-bank deployments after load testing',
          details: ['Pilot to enterprise tiers', 'Measured concurrency', 'Upgrade path', 'Load balancing']
        }
      ]
    },
    {
      id: 'integration',
      name: 'Integration & Customization',
      icon: 'api',
      features: [
        {
          title: 'REST API',
          desc: 'Complete API for programmatic access to all BankAi functionality',
          details: ['Document upload', 'Query execution', 'Session management', 'Batch operations']
        },
        {
          title: 'File Format Support',
          desc: 'Support for all common enterprise document formats',
          details: ['PDF files', 'Word documents', 'Excel spreadsheets', 'PowerPoint presentations', 'Plain text', 'CSV data']
        },
        {
          title: 'Custom Analysis Templates',
          desc: 'Create reusable templates for common analysis workflows',
          details: ['Template creation', 'Workflow automation', 'Preset questions', 'Batch execution']
        },
        {
          title: 'Export & Reporting',
          desc: 'Generate reports and export analysis results in multiple formats',
          details: ['PDF export', 'Excel export', 'JSON data', 'Custom reports']
        }
      ]
    },
    {
      id: 'admin',
      name: 'Administration',
      icon: 'admin_panel_settings',
      features: [
        {
          title: 'User Management',
          desc: 'Create and manage unlimited users within your organization',
          details: ['User provisioning', 'Role assignment', 'Department management', 'Deprovisioning']
        },
        {
          title: 'Organization Settings',
          desc: 'Configure system-wide settings and policies for your deployment',
          details: ['Email configuration', 'Security policies', 'Default quotas', 'Branding options']
        },
        {
          title: 'System Monitoring',
          desc: 'Monitor system health, performance, and resource utilization',
          details: ['CPU/RAM monitoring', 'Storage usage', 'Service status', 'Performance metrics']
        },
        {
          title: 'Backup & Recovery',
          desc: 'Automated daily backups with easy recovery procedures',
          details: ['Automated backups', 'Point-in-time recovery', 'Disaster recovery', 'Data retention']
        }
      ]
    }
  ];

  const selectedCat = categories.find(cat => cat.id === selectedCategory);

  const benefits = [
    { icon: 'savings', title: '50% Time Reduction', desc: 'Cut document analysis time in half' },
    { icon: 'verified_user', title: 'Source Evidence', desc: 'Answers show the documents and passages used' },
    { icon: 'lock', title: 'Private Deployment', desc: 'Bank data stays inside controlled infrastructure' },
    { icon: 'trending_up', title: 'Pilot Metrics', desc: 'Measure accuracy, latency, and escalation reduction' },
  ];

  return (
    <div className="bg-surface text-on-surface min-h-screen">
      {/* Header */}
      <div className="bg-gradient-to-br from-primary-container via-surface to-surface px-6 py-16">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-4xl lg:text-5xl font-bold font-public-sans text-slate-900 mb-4">
            Comprehensive Features
          </h1>
          <p className="text-xl text-slate-600">
            Explore the staff-assistance, source-backed search, governance, and deployment controls behind LipiCore
          </p>
        </div>
      </div>

      {/* Benefits */}
      <section className="py-16 px-6 bg-white border-b border-slate-100">
        <div className="max-w-6xl mx-auto grid md:grid-cols-4 gap-8">
          {benefits.map((benefit) => (
            <div key={benefit.title} className="text-center">
              <span className="material-symbols-outlined text-primary text-5xl flex justify-center mb-4">
                {benefit.icon}
              </span>
              <h3 className="font-bold text-slate-900 mb-2">{benefit.title}</h3>
              <p className="text-sm text-slate-600">{benefit.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Feature Categories */}
      <section className="py-16 px-6">
        <div className="max-w-6xl mx-auto">
          {/* Category Tabs */}
          <div className="flex flex-wrap gap-2 mb-12 p-2 bg-slate-100 rounded-lg w-fit">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded font-semibold transition-all ${
                  selectedCategory === cat.id
                    ? 'bg-primary text-white'
                    : 'text-slate-700 hover:bg-slate-200'
                }`}>
                <span className="material-symbols-outlined text-[18px]">{cat.icon}</span>
                {cat.name}
              </button>
            ))}
          </div>

          {/* Category Features Grid */}
          <div className="grid md:grid-cols-2 gap-8">
            {selectedCat.features.map((feature) => (
              <div
                key={feature.title}
                className="bg-white border border-slate-200 rounded-lg p-8 hover:shadow-lg hover:border-secondary transition-all">
                <h3 className="text-xl font-bold text-slate-900 mb-3">{feature.title}</h3>
                <p className="text-slate-600 mb-6">{feature.desc}</p>
                <ul className="space-y-2">
                  {feature.details.map((detail) => (
                    <li key={detail} className="flex items-center gap-2 text-sm">
                      <span className="w-1.5 h-1.5 bg-primary rounded-full"></span>
                      <span className="text-slate-700">{detail}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* File Format Support */}
      <section className="py-16 px-6 bg-slate-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold font-public-sans text-slate-900 mb-12 text-center">
            Supported File Formats
          </h2>
          <div className="grid md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { ext: 'PDF', icon: 'picture_as_pdf', desc: 'PDF documents' },
              { ext: 'DOCX', icon: 'article', desc: 'Word documents' },
              { ext: 'XLSX', icon: 'table_chart', desc: 'Excel spreadsheets' },
              { ext: 'PPTX', icon: 'slideshow', desc: 'PowerPoint presentations' },
              { ext: 'TXT', icon: 'description', desc: 'Text files' },
              { ext: 'CSV', icon: 'data_table', desc: 'CSV data' },
            ].map((format) => (
              <div key={format.ext} className="bg-white rounded-lg p-6 text-center border border-slate-200 hover:shadow-lg transition-all">
                <span className="material-symbols-outlined text-primary text-5xl flex justify-center mb-3">
                  {format.icon}
                </span>
                <h4 className="font-bold text-slate-900">{format.ext}</h4>
                <p className="text-xs text-slate-600 mt-1">{format.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance & Certifications */}
      <section className="py-16 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold font-public-sans text-slate-900 mb-12 text-center">
            Compliance & Certifications
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { cert: 'Audit Evidence', icon: 'verified_user', desc: 'Logs and exports for review' },
              { cert: 'Privacy Controls', icon: 'privacy_tip', desc: 'Bank-controlled data handling' },
              { cert: 'Access Governance', icon: 'health_and_safety', desc: 'Roles and permissions' },
              { cert: 'Payment Data Policy', icon: 'credit_card', desc: 'Controls for sensitive data handling' },
              { cert: 'NRB Review Support', icon: 'policy', desc: 'Source-backed regulatory lookup' },
              { cert: 'ISO 27001 Alignment', icon: 'shield', desc: 'Security controls for bank review' },
            ].map((cert) => (
              <div key={cert.cert} className="bg-white border border-slate-200 rounded-lg p-8 text-center hover:shadow-lg transition-all">
                <span className="material-symbols-outlined text-primary text-5xl flex justify-center mb-4">
                  {cert.icon}
                </span>
                <h3 className="font-bold text-slate-900 mb-2">{cert.cert}</h3>
                <p className="text-sm text-slate-600">{cert.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Performance Metrics */}
      <section className="py-16 px-6 bg-slate-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold font-public-sans text-slate-900 mb-12 text-center">
            Performance Metrics
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white rounded-lg p-8 border border-slate-200">
              <h3 className="font-bold text-slate-900 mb-6">Throughput</h3>
              <div className="space-y-4">
                {[
                  { metric: 'Concurrent Users', value: 'Measured by tier' },
                  { metric: 'Upload Capacity', value: 'Configurable' },
                  { metric: 'Document Processing', value: 'Queue-based' },
                  { metric: 'API Response Time', value: 'Load tested' },
                  { metric: 'Query Processing', value: 'Model dependent' },
                  { metric: 'Storage Capacity', value: 'Sized per bank' },
                ].map((item) => (
                  <div key={item.metric} className="flex justify-between items-center pb-4 border-b border-slate-100">
                    <span className="text-slate-600">{item.metric}</span>
                    <span className="font-bold text-primary">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-lg p-8 border border-slate-200">
              <h3 className="font-bold text-slate-900 mb-6">Reliability</h3>
              <div className="space-y-4">
                {[
                  { metric: 'Uptime SLA', value: 'By tier' },
                  { metric: 'MTTR', value: 'By contract' },
                  { metric: 'Automatic Failover', value: 'HA tier' },
                  { metric: 'Backup Frequency', value: 'Policy based' },
                  { metric: 'Recovery Time', value: 'Drill tested' },
                  { metric: 'Data Redundancy', value: 'Architecture based' },
                ].map((item) => (
                  <div key={item.metric} className="flex justify-between items-center pb-4 border-b border-slate-100">
                    <span className="text-slate-600">{item.metric}</span>
                    <span className="font-bold text-primary">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-6 bg-primary-container">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold font-public-sans text-white mb-6">
            Experience All Features in Action
          </h2>
          <p className="text-lg text-on-primary-container opacity-90 mb-10">
            Start with the demo or request an enterprise quote for your organization
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <button className="px-8 py-3 bg-white text-primary rounded font-semibold hover:opacity-90 transition-opacity">
              Back to Dashboard
            </button>
            <button className="px-8 py-3 border-2 border-white text-white rounded font-semibold hover:bg-white hover:text-primary transition-colors">
              Request Demo
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

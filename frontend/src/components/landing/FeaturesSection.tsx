import React from 'react';
import { Shield, Zap, Globe, Database, Network, Cpu } from 'lucide-react';

const features = [
  {
    icon: <Shield className="w-6 h-6 text-indigo-400" />,
    title: "Privacy First",
    description: "Operates in an isolated local environment. Your identity and browsing history remain entirely yours."
  },
  {
    icon: <Globe className="w-6 h-6 text-blue-400" />,
    title: "Universal Access",
    description: "No APIs required. If a human can browse it, MOSAIC can navigate it, extract from it, and interact with it."
  },
  {
    icon: <Zap className="w-6 h-6 text-yellow-400" />,
    title: "Lightning Fast",
    description: "Built on high-performance architecture. MOSAIC executes complex multi-step web tasks in seconds."
  },
  {
    icon: <Database className="w-6 h-6 text-emerald-400" />,
    title: "Smart Memory",
    description: "Retains context across sessions. It remembers your preferences, logins, and past interactions."
  },
  {
    icon: <Network className="w-6 h-6 text-purple-400" />,
    title: "Adaptive Learning",
    description: "Learns website structures dynamically. Even if a UI changes, MOSAIC adapts without breaking."
  },
  {
    icon: <Cpu className="w-6 h-6 text-pink-400" />,
    title: "Local AI Models",
    description: "Leverages local or dedicated LLMs to ensure your data never leaves your infrastructure."
  }
];

export default function FeaturesSection() {
  return (
    <section className="py-32 px-6 relative z-10 bg-slate-50 dark:bg-slate-950/50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-20">
          <h2 className="text-3xl md:text-5xl font-bold mb-6 font-display">Unleash Next-Gen Capabilities</h2>
          <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto text-lg">
            Built from the ground up for privacy, speed, and boundless automation.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="glass-card p-6 rounded-2xl hover:-translate-y-2 transition-transform duration-300 group cursor-default"
            >
              <div className="w-12 h-12 bg-slate-200 dark:bg-slate-800/50 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold mb-3 text-slate-900 dark:text-slate-100">{feature.title}</h3>
              <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

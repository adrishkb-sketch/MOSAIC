import React from 'react';
import { motion } from 'framer-motion';
import { MousePointerClick, BrainCircuit, CheckCircle2 } from 'lucide-react';

const steps = [
  {
    icon: <MousePointerClick className="w-8 h-8 text-indigo-400" />,
    title: "1. Command Your Agent",
    description: "Simply type what you want to achieve in natural language. 'Find flights to Tokyo', 'Extract pricing data', or 'Fill out this form'."
  },
  {
    icon: <BrainCircuit className="w-8 h-8 text-purple-400" />,
    title: "2. Autonomous Navigation",
    description: "MOSAIC's AI engine interprets your command, plans the optimal route, and physically interacts with the browser just like a human would."
  },
  {
    icon: <CheckCircle2 className="w-8 h-8 text-emerald-400" />,
    title: "3. Results Delivered",
    description: "Get structured data, summaries, or completed actions directly in your dashboard. MOSAIC learns from every interaction to get faster."
  }
];

export default function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-32 px-6 relative z-10">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-20">
          <h2 className="text-3xl md:text-5xl font-bold mb-6 font-display">How It Works</h2>
          <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto text-lg">
            Complex web automation simplified into three effortless steps.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6, delay: index * 0.2 }}
              className="glass-panel p-8 rounded-3xl relative overflow-hidden group hover:border-indigo-500/50 transition-all duration-500"
            >
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="mb-6 p-4 bg-slate-200 dark:bg-slate-800/50 rounded-2xl inline-block">
                {step.icon}
              </div>
              <h3 className="text-xl font-bold mb-4">{step.title}</h3>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

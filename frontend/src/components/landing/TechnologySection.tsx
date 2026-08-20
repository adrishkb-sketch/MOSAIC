import React from 'react';

const technologies = [
  "Next.js", "React", "TypeScript", "Tailwind CSS", "Three.js", "Framer Motion", "FastAPI", "Python", "Local LLMs"
];

export default function TechnologySection() {
  return (
    <section className="py-24 px-6 relative z-10 border-t border-slate-300/30 dark:border-white/5 bg-slate-50 dark:bg-slate-950/30">
      <div className="max-w-4xl mx-auto text-center">
        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-widest mb-8">Powered By Leading Technologies</h3>
        <div className="flex flex-wrap justify-center gap-4 md:gap-8 opacity-70 hover:opacity-100 transition-opacity duration-500">
          {technologies.map((tech, index) => (
            <span key={index} className="text-lg md:text-xl font-medium text-slate-700 dark:text-slate-300">
              {tech}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

import { EmptyState } from '@/components/empty-state/EmptyState';
import { ScreenFrame } from '@/layout/ScreenFrame';
import type { Section } from '@/navigation/sections';

// Each section shows this until its own screen is built (docs/dashboard-plan.md, "Order").
export function SectionScreen({ section }: { section: Section }) {
  const inspector = <p className="inspector-note">Settings for {section.title} will show here.</p>;

  return (
    <ScreenFrame title={section.title} inspector={inspector}>
      <EmptyState icon={section.icon} title={`${section.title} is on its way`}>
        {section.summary}
        {section.needs ? <> It needs {section.needs} first, and there is none yet.</> : null}
      </EmptyState>
    </ScreenFrame>
  );
}

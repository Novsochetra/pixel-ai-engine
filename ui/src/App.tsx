import { Navigate, Route, Routes } from 'react-router';
import type { ComponentType } from 'react';
import { AnimateScreen } from '@/animate/AnimateScreen';
import { CreateScreen } from '@/create/CreateScreen';
import { AppShell } from '@/layout/AppShell';
import { LibraryScreen } from '@/library/LibraryScreen';
import { SECTIONS } from '@/navigation/sections';
import { SectionScreen } from '@/screens/SectionScreen';
import { TrainingScreen } from '@/training/TrainingScreen';

const FIRST_SECTION = SECTIONS[0]!.path;

// The sections built so far; the others show a placeholder until their step of the plan.
const SCREENS: Partial<Record<string, ComponentType>> = {
  animate: AnimateScreen,
  create: CreateScreen,
  library: LibraryScreen,
  training: TrainingScreen,
};

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        {SECTIONS.map((section) => {
          const Screen = SCREENS[section.id];

          return (
            <Route
              key={section.id}
              path={section.path}
              element={Screen ? <Screen /> : <SectionScreen section={section} />}
            />
          );
        })}
        <Route path="*" element={<Navigate to={FIRST_SECTION} replace />} />
      </Route>
    </Routes>
  );
}

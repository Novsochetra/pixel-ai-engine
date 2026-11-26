import { Navigate, Route, Routes } from 'react-router';
import type { ComponentType } from 'react';
import { AnimateScreen } from '@/animate/AnimateScreen';
import { CreateScreen } from '@/create/CreateScreen';
import { LibraryScreen } from '@/library/LibraryScreen';
import { RotateScreen } from '@/rotate/RotateScreen';
import { SectionScreen } from '@/screens/SectionScreen';
import { TrainingRunScreen } from '@/training/TrainingRunScreen';
import { TrainingScreen } from '@/training/TrainingScreen';
import { SECTIONS } from './sections';

const FIRST_SECTION = SECTIONS[0]!.path;

// The sections built so far; the others show a placeholder until their step of the plan.
const SCREENS: Partial<Record<string, ComponentType>> = {
  animate: AnimateScreen,
  create: CreateScreen,
  library: LibraryScreen,
  rotate: RotateScreen,
  training: TrainingScreen,
};

// Each layer of the screen stack shows the screen at its own path, so one left under the stack
// keeps showing its screen while the route has moved on.
export function ScreenRoutes({ path }: { path: string }) {
  return (
    <Routes location={path}>
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
      <Route path="/training/:name" element={<TrainingRunScreen />} />
      <Route path="*" element={<Navigate to={FIRST_SECTION} replace />} />
    </Routes>
  );
}

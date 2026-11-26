import { Navigate, Route, Routes } from 'react-router';
import { AppShell } from '@/layout/AppShell';
import { SECTIONS } from '@/navigation/sections';
import { SectionScreen } from '@/screens/SectionScreen';

const FIRST_SECTION = SECTIONS[0]!.path;

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        {SECTIONS.map((section) => (
          <Route
            key={section.id}
            path={section.path}
            element={<SectionScreen section={section} />}
          />
        ))}
        <Route path="*" element={<Navigate to={FIRST_SECTION} replace />} />
      </Route>
    </Routes>
  );
}

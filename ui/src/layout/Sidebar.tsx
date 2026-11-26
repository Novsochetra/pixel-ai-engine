import { NavLink } from 'react-router';
import { AppearanceButton } from '@/appearance/AppearanceButton';
import { Icon } from '@/components/icons';
import { JobStatus } from '@/jobs/JobStatus';
import { GROUPS, sectionsIn } from '@/navigation/sections';
import './sidebar.css';

export function Sidebar() {
  return (
    <aside className="sidebar">
      <header className="sidebar__brand">
        <span className="app-mark" aria-hidden="true" />
        <span className="sidebar__name">Pixel Engine</span>
      </header>
      <nav className="sidebar__nav" aria-label="Sections">
        {GROUPS.map((group) => (
          <section className="sidebar__group" key={group.id} aria-labelledby={`group-${group.id}`}>
            <h2 className="sidebar__heading" id={`group-${group.id}`}>
              {group.title}
            </h2>
            <ul className="sidebar__list">
              {sectionsIn(group.id).map((section) => (
                <li key={section.id}>
                  <NavLink className="sidebar__row" to={section.path}>
                    <Icon name={section.icon} />
                    {section.title}
                  </NavLink>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </nav>
      <footer className="sidebar__footer">
        <JobStatus placement="sidebar" />
        <AppearanceButton />
      </footer>
    </aside>
  );
}

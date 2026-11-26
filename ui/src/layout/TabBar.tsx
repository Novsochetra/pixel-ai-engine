import { useState } from 'react';
import { NavLink, useLocation } from 'react-router';
import { Icon } from '@/components/icons';
import { sectionAt, tabSections } from '@/navigation/sections';
import { MoreSheet } from './MoreSheet';
import './tab-bar.css';

export function TabBar() {
  const [isMoreOpen, setMoreOpen] = useState(false);
  const current = sectionAt(useLocation().pathname);
  const isMoreCurrent = Boolean(current && !current.inTabBar);

  return (
    <>
      <nav className="tab-bar" aria-label="Sections">
        {tabSections().map((section) => (
          <NavLink className="tab-bar__item" to={section.path} key={section.id}>
            <Icon name={section.icon} size="large" />
            {section.title}
          </NavLink>
        ))}
        <button
          className="tab-bar__item"
          type="button"
          aria-current={isMoreCurrent ? 'page' : undefined}
          onClick={() => setMoreOpen(true)}
        >
          <Icon name="more" size="large" />
          More
        </button>
      </nav>
      <MoreSheet isOpen={isMoreOpen} onClosed={() => setMoreOpen(false)} />
    </>
  );
}

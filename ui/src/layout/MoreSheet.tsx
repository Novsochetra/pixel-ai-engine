import { NavLink } from 'react-router';
import { AppearanceButton } from '@/appearance/AppearanceButton';
import { Icon } from '@/components/icons';
import { Sheet } from '@/components/sheet/Sheet';
import { moreSections } from '@/navigation/sections';

// The sections a narrow screen's tab bar has no room for, and the appearance switch.
export function MoreSheet({ isOpen, onClosed }: { isOpen: boolean; onClosed: () => void }) {
  return (
    <Sheet title="More" isOpen={isOpen} onClosed={onClosed}>
      <ul className="more-list">
        {moreSections().map((section) => (
          <li key={section.id}>
            <NavLink className="more-list__row" to={section.path} onClick={onClosed}>
              <Icon name={section.icon} />
              {section.title}
            </NavLink>
          </li>
        ))}
      </ul>
      <div className="more-list__appearance">
        <span>Appearance</span>
        <AppearanceButton />
      </div>
    </Sheet>
  );
}

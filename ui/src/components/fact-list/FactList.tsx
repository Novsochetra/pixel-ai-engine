import './fact-list.css';

export interface FactRow {
  label: string;
  value: string;
}

// A grouped, inset list of label and value rows, like a Settings section.
export function FactList({ title, facts }: { title?: string; facts: readonly FactRow[] }) {
  return (
    <section className="fact-list">
      {title ? <h3 className="fact-list__title">{title}</h3> : null}
      <dl className="fact-list__rows">
        {facts.map((fact) => (
          <div className="fact-list__row" key={fact.label}>
            <dt className="fact-list__label">{fact.label}</dt>
            <dd className="fact-list__value">{fact.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

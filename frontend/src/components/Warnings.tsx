interface Props {
  warnings: string[];
  className?: string;
  title?: string;
}

export default function Warnings({ warnings, className = "warnings", title }: Props) {
  if (warnings.length === 0) return null;

  return (
    <div className={className}>
      {title && <strong>{title}</strong>}
      {warnings.map((w, i) => (
        <p key={i}>{w}</p>
      ))}
    </div>
  );
}

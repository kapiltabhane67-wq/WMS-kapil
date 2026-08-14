function statusClass(status: string) {
  if (["SHIPPED", "COMPLETED", "GENERATED", "PICKED"].includes(status)) return "ok";
  if (["AWAITING_STOCK", "PICKING", "LABEL_CREATED"].includes(status)) return "warn";
  if (["CANCELLED", "FAILED"].includes(status)) return "danger";
  return "";
}

export function SimpleTable<T extends Record<string, unknown>>({
  title,
  rows,
  columns,
}: {
  title: string;
  rows: T[];
  columns: string[];
}) {
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>{title}</h2>
        <span className="badge">{rows.length}</span>
      </div>
      <div className="panel-body">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column.replaceAll("_", " ")}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={columns.length}>No records yet</td>
              </tr>
            )}
            {rows.map((row, index) => (
              <tr key={String(row.id ?? index)}>
                {columns.map((column) => {
                  const value = row[column];
                  const text = value === null || value === undefined ? "-" : String(value);
                  return (
                    <td key={column}>
                      {column === "status" ? <span className={`badge ${statusClass(text)}`}>{text}</span> : text}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}


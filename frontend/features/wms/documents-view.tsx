import { SimpleTable } from "../../components/simple-table";
import type { DocumentRow } from "../../lib/types";

export function DocumentsView({ documents }: { documents: DocumentRow[] }) {
  return <SimpleTable title="Documents" rows={documents} columns={["id", "document_type", "reference_type", "reference_id", "file_name", "status"]} />;
}

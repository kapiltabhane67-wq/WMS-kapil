"use client";

import { FormEvent, useState } from "react";

import { SimpleTable } from "../../components/simple-table";
import { uploadFile } from "../../lib/api";
import type { DocumentRow } from "../../lib/types";

export function DocumentsView({
  documents,
  token,
  onUploaded,
}: {
  documents: DocumentRow[];
  token: string;
  onUploaded: () => Promise<void>;
}) {
  const [documentType, setDocumentType] = useState("OTHER");
  const [referenceType, setReferenceType] = useState("manual_upload");
  const [referenceId, setReferenceId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    setError("");
    if (!file) {
      setError("Choose a file before uploading.");
      return;
    }
    const formData = new FormData();
    formData.append("document_type", documentType);
    formData.append("reference_type", referenceType);
    formData.append("reference_id", referenceId || "0");
    formData.append("file", file);
    setBusy(true);
    try {
      await uploadFile<DocumentRow>("/v1/documents/upload", token, formData);
      setMessage("Document uploaded and recorded successfully.");
      setFile(null);
      await onUploaded();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Document upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <form className="panel upload-panel" onSubmit={submit}>
        <div className="panel-head">
          <h2>Upload document</h2>
          <span className="badge">PDF, CSV, DOCX, XLSX, images</span>
        </div>
        <div className="upload-grid">
          <label>
            <span>Document type</span>
            <select value={documentType} onChange={(event) => setDocumentType(event.target.value)}>
              <option value="RECEIPT">Receipt</option>
              <option value="INVOICE">Invoice</option>
              <option value="SHIPPING_LABEL">Shipping label</option>
              <option value="PACKING_SLIP">Packing slip</option>
              <option value="PURCHASE_ORDER">Purchase order</option>
              <option value="RETURN_DOCUMENT">Return document</option>
              <option value="OTHER">Other</option>
            </select>
          </label>
          <label>
            <span>Reference type</span>
            <select value={referenceType} onChange={(event) => setReferenceType(event.target.value)}>
              <option value="manual_upload">Manual upload</option>
              <option value="inbound_receipt">Inbound receipt</option>
              <option value="sales_order">Sales order</option>
              <option value="shipment">Shipment</option>
            </select>
          </label>
          <label>
            <span>Reference ID</span>
            <input
              type="number"
              min="0"
              value={referenceId}
              onChange={(event) => setReferenceId(event.target.value)}
              placeholder="Leave blank for manual upload"
            />
          </label>
          <label>
            <span>File</span>
            <input
              type="file"
              accept=".pdf,.csv,.txt,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>
        </div>
        <button className="primary" type="submit" disabled={busy}>
          {busy ? "Uploading" : "Upload document"}
        </button>
        {message && <div className="notice">{message}</div>}
        {error && <div className="notice error">{error}</div>}
      </form>
      <SimpleTable
        title="Documents"
        rows={documents}
        columns={["id", "document_type", "reference_type", "reference_id", "file_name", "status", "file_size"]}
      />
    </div>
  );
}

"use client";

import { PackageCheck, ScanLine, Truck } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { FormPanel, Input, NumberInput, Select } from "../../components/forms";
import { SimpleTable } from "../../components/simple-table";
import type { OrderRow, PickTask, SubmitJson } from "../../lib/types";

export function FulfillmentView({
  submitJson,
  tasks,
  orders,
}: {
  submitJson: SubmitJson;
  tasks: PickTask[];
  orders: OrderRow[];
}) {
  const firstTask = tasks.find((task) => task.status === "READY" || task.status === "PICKING") ?? tasks[0];
  const [taskId, setTaskId] = useState(firstTask?.id ?? 1);
  const [sku, setSku] = useState("");
  const [binCode, setBinCode] = useState("");
  const [quantity, setQuantity] = useState(1);
  const latestLabelOrder = orders.find((order) => order.status === "LABEL_CREATED");
  const [shipmentId, setShipmentId] = useState("");
  const [carrier, setCarrier] = useState("UPS");
  const [weightOz, setWeightOz] = useState(16);
  const [lengthIn, setLengthIn] = useState(10);
  const [widthIn, setWidthIn] = useState(8);
  const [heightIn, setHeightIn] = useState(4);
  const selectedTask = tasks.find((task) => task.id === taskId) ?? firstTask;
  const canScan = Boolean(selectedTask && sku && binCode && quantity > 0);
  const canPack = Boolean(selectedTask && selectedTask.status === "PICKED");
  const knownShipmentId = shipmentId || (selectedTask?.shipment_id ? String(selectedTask.shipment_id) : "");

  useEffect(() => {
    if (!firstTask) return;
    setTaskId(firstTask.id);
    setSku(firstTask.first_sku ?? "");
    setBinCode(firstTask.first_bin_code ?? "");
    setQuantity(firstTask.total_units || 1);
    setShipmentId(firstTask.shipment_id ? String(firstTask.shipment_id) : "");
  }, [firstTask?.id]);

  function chooseTask(value: string) {
    const nextTask = tasks.find((task) => task.id === Number(value));
    if (!nextTask) return;
    setTaskId(nextTask.id);
    setSku(nextTask.first_sku ?? "");
    setBinCode(nextTask.first_bin_code ?? "");
    setQuantity(nextTask.total_units || 1);
    setShipmentId(nextTask.shipment_id ? String(nextTask.shipment_id) : "");
  }

  async function pack(event: FormEvent) {
    event.preventDefault();
    const result = await submitJson<{ shipment_id: number; tracking_number: string }>(
      `/v1/fulfillment/pick-tasks/${taskId}/pack`,
      { carrier, weight_oz: weightOz, length_in: lengthIn, width_in: widthIn, height_in: heightIn },
      "Packed, label generated, and shipment is ready to dispatch"
    );
    if (result?.shipment_id) {
      setShipmentId(String(result.shipment_id));
    }
  }

  return (
    <div className="grid forms">
      <div className="grid">
        <FormPanel
          title="Pick Scan"
          icon={<ScanLine size={18} />}
          onSubmit={(event) => {
            event.preventDefault();
            submitJson(`/v1/fulfillment/pick-tasks/${taskId}/scan`, { sku, bin_code: binCode, quantity }, "Pick scan accepted");
          }}
        >
          <div className="receiver-flow">
            <span>1. Select task</span>
            <span>2. Scan bin + SKU</span>
            <span>3. Confirm quantity</span>
            <span>4. Pack parcel</span>
            <span>5. Dispatch</span>
          </div>
          <Select
            label="Assigned pick task"
            value={selectedTask ? String(taskId) : ""}
            onChange={chooseTask}
            options={tasks.map((task) => String(task.id))}
            placeholder="No pick task ready"
          />
          {selectedTask?.pick_items && <div className="notice">Pick instruction: {selectedTask.pick_items}</div>}
          {selectedTask && (
            <div className="notice">
              Order {selectedTask.external_order_id} | Ship to {selectedTask.ship_to_name}, {selectedTask.ship_to_city} | Status {selectedTask.status}
            </div>
          )}
          <Input label="SKU - Stock Keeping Unit (product code)" value={sku} onChange={setSku} />
          <Input label="Bin (storage location)" value={binCode} onChange={setBinCode} />
          <NumberInput label="Quantity" value={quantity} onChange={setQuantity} />
          <button className="primary" type="submit" disabled={!canScan}>
            <ScanLine size={16} />
            Confirm Pick
          </button>
        </FormPanel>
        <FormPanel title="Pack And Dispatch" icon={<Truck size={18} />} onSubmit={pack}>
          <Select label="Carrier" value={carrier} onChange={setCarrier} options={["UPS", "FedEx", "USPS", "DHL", "Local Carrier"]} />
          <div className="row">
            <NumberInput label="Weight oz" value={weightOz} onChange={setWeightOz} />
            <NumberInput label="Length in" value={lengthIn} onChange={setLengthIn} />
          </div>
          <div className="row">
            <NumberInput label="Width in" value={widthIn} onChange={setWidthIn} />
            <NumberInput label="Height in" value={heightIn} onChange={setHeightIn} />
          </div>
          <button className="primary" type="submit" disabled={!canPack && selectedTask?.status !== "PACKED"}>
            <PackageCheck size={16} />
            {selectedTask?.status === "PACKED" ? "Reload Packed Shipment" : "Pack Selected Task"}
          </button>
          <Input label="Shipment ID for dispatch" value={knownShipmentId} onChange={setShipmentId} />
          {selectedTask?.tracking_number && <div className="notice">Tracking: {selectedTask.tracking_number} | Shipment status: {selectedTask.shipment_status}</div>}
          <button type="button" onClick={() => submitJson(`/v1/shipments/${knownShipmentId}/dispatch`, {}, "Shipment dispatched and physical stock deducted")} disabled={!knownShipmentId}>
            <Truck size={16} />
            Dispatch Shipment
          </button>
          {knownShipmentId && <div className="notice">Shipment #{knownShipmentId} is ready for dispatch.</div>}
          {latestLabelOrder && !knownShipmentId && <div className="notice">A recent order has label status: order #{latestLabelOrder.id}</div>}
        </FormPanel>
      </div>
      <SimpleTable title="Pick Queue" rows={tasks} columns={["id", "order_id", "warehouse_code", "external_order_id", "pick_items", "status", "shipment_id", "tracking_number", "shipment_status"]} />
    </div>
  );
}

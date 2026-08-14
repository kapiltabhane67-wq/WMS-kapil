# Controllers

Controllers are the business-flow layer.

The PDF structure says:

```text
router -> controller -> crud/service -> database
```

In this WMS project, each major role has its own controller file:

- `auth_controller.py` - login, logout, session, self password change
- `org_admin_controller.py` - organization setup, users, settings, audit, reports
- `warehouse_manager_controller.py` - manager dashboard, order import, adjustments
- `receiver_controller.py` - receiving incoming stock
- `picker_packer_controller.py` - pick, pack, label, dispatch
- `seller_viewer_controller.py` - seller read-only portal data
- `inventory_controller.py` - inventory ledger reads and adjustments
- `document_controller.py` - document list and file upload
- `user_controller.py` - user account business rules used by admin

Routes should stay thin. Put role/business decisions here, not in `routes/`.


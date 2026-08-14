# Routes

Routes are the HTTP layer only.

They should:

- define endpoint paths;
- receive path/query/body/form/file inputs;
- open the database connection;
- call a controller;
- return the controller result.

They should not contain warehouse business rules.

Example:

```text
POST /v1/receiving/complete
-> receiving_router.py
-> receiver_controller.py
-> receiving_service.py
-> SQLite database
```


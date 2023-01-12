# TODO
create_app_exchange()
1. app_input:
    ```python
    create_queue_in_app_borker()
    set_callback_to_app_queue()
    publish_to_server_exchange()
    ```
2. app_output:
    ```python
    create_queue_in_central_broker()
    bind_result_queue_to_server_exchange()
    set_callback_to_result_queue()
    publish_to_app_exchange()
    ```
3. route:
   ```python
   for server in route:
        server["input"]
   ```

<app><client><exchange><type>
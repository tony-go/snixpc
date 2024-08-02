> ⚠️: This lldb plugin is under development, there are a few bugs to fix :)

> 👉: Share your feedback [in this issue](https://github.com/tony-go/snixpc/issues/2).

<h1 align="center">snixpc</h1>
<h3 align="center">Inspect xpc messages of your favorite binary</h3>

`snixpc` is an LLDB plugin designed to capture and polish XPC messages. It allows developers
and security researchers to easily intercept and examine XPC communications.

## Example

```text
(lldb) command script import /path/to/snif.py
(lldb) snif
XPC Tracker plugin loaded. Use 'snif' to set breakpoints on XPC functions.
...
Breakpoints set on XPC functions.
(lldb) c
Process 1234 resuming
...
{
    "xpc_function": "xpc_connection_send_message",
    "connection_name": "com.apple.example.service",
    "connection_pid": "5678",
    "message": {
        "command": "fetch_data",
        "parameters": {
            "id": 12345,
            "type": "user_info"
        }
    },
    "direction": "send"
}
```

## Features

- Set breakpoints on XPC send and receive functions
- Capture and serialize XPC message content
- Display connection information (name and PID)

### Roadmap

- Make this version stable
- Add a `--output/-o` flag to write serialized messages to file
- Add a `unsnif` command to stop XPC "sniffing"
- Wrap this plugin into an executable

> 🤙 Stay tuned as we continue to expand our feature set.

### XPC Function Support

| Function                                    | Support    |
|---------------------------------------------|------------|
| xpc_connection_send_message                 | ✅ Supported |
| xpc_connection_send_message_with_reply      | ✅ Supported |
| xpc_connection_send_message_with_reply_sync | ✅ Supported |
| xpc_connection_set_event_handler            | ✅ Supported |
| xpc_connection_set_event_handler_with_flags | ✅ Supported |

### Types

| XPC Type            | Support          |
|---------------------|------------------|
| XPC_TYPE_STRING     | ✅ Supported     |
| XPC_TYPE_INT64      | ✅ Supported     |
| XPC_TYPE_UINT64     | ✅ Supported     |
| XPC_TYPE_BOOL       | ✅ Supported     |
| XPC_TYPE_DOUBLE     | ✅ Supported     |
| XPC_TYPE_DATA       | ✅ Supported     |
| XPC_TYPE_ARRAY      | ❌ Not Supported |
| XPC_TYPE_DICTIONARY | ✅ Supported     |


## Bugs / Limitations

- We don't serialize properly `XPC_TYPE_ARRAY`
- The plugin is not resilient when there is a lot of messages
  - This warning appears:
    ```
    warning: hit breakpoint while running function, skipping commands and conditions to prevent recursion
    ```
  - It is very difficult to stop the execution when there are a lot of messages

## Dependencies

- macOS
- Xcode
- Python

## Usage


1. Clone the repository or download the snif.xpc file

2. In your LLDB debugging session, load the script:
   ```shell
   (lldb) command script import /path/to/snif.py
   ```

3. Set XPC breakpoints using the 'snif' command:
   ```shell
   (lldb) snif
   ```

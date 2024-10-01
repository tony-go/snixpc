> ⚠️: This lldb plugin is under development.

> 👉: Share your feedback [in this issue](https://github.com/tony-go/snixpc/issues/2).

<h1 align="center">snixpc</h1>
<h3 align="center">Inspect xpc messages of your favorite binary</h3>

`snixpc` is an LLDB plugin designed to capture and polish XPC messages. It allows developers
and security researchers to easily intercept and examine XPC communications.

## Example

```text
(lldb) command script import /path/to/snif.py
(lldb) snif
Set breakpoint on: xpc_connection_send_message
Set breakpoint on: xpc_connection_send_message_with_reply
Set breakpoint on: xpc_connection_send_message_with_reply_sync
Set breakpoint on: xpc_connection_set_event_handler
Set breakpoint on: xpc_connection_set_event_handler_with_flags
Breakpoints set on XPC functions.
(lldb) c
Process 52098 resuming
(lldb) ======================================
XPC Function: xpc_connection_send_message
Direction: SEND
Thread: 0xede788
Connection: "<connection: 0x600002d90000> { name = com.apple.distributed_notifications@Uv3, listener = false, pid = 1476, euid = 501, egid = 20, asid = 100033 }"
Message: "<dictionary: 0x600003688fc0> { count = 5, transaction: 0, voucher = 0x0, contents =
    "options" => <uint64: 0x8fa5d5b4a0f1ce8f>: 1
    "object" => <string: 0x600001c9afa0> { length = 24, contents = "kCFNotificationAnyObject" }
    "name" => <string: 0x600001c9b030> { length = 49, contents = "com.apple.HIToolbox.beginMenuTrackingNotification" }
    "method" => <string: 0x600001c9bb10> { length = 4, contents = "post" }
    "version" => <uint64: 0x8fa5d5b4a0f1ce8f>: 1
}"
```

## Features

- Set breakpoints on XPC send and receive functions
- Display
  - XPC connection
  - XPC message
  - Direction
  - XPC function
  - Thread id

### Roadmap

- Add a `--output/-o` flag to write messages to file
- Add a `--format/-f` flag to serialize to json (only with `-o` flag)
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

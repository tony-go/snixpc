# AGPL License

# Copyright (c) 2024 Tony Gorez

import lldb

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f snif.set_xpc_breakpoints snif')
    print("XPC Tracker plugin loaded. Use 'snif' to set breakpoints on XPC functions.")

def clean_description(description):
    return description.replace('\\n', '\n').replace('\\t', '\t').replace('\\', '')

def ansi_bold(text):
    return f"\033[1m{text}\033[0m"


def display_xpc_event(frame, direction):
    xpc_func = frame.GetFunctionName()
    thread = hex(frame.GetThread().GetThreadID())
    con_hex = frame.FindRegister("x0").GetValue()
    msg_hex = frame.FindRegister("x1").GetValue()

    con_description_raw = frame.EvaluateExpression(f"(char *)xpc_copy_description({con_hex})").GetSummary()
    msg_description_raw = frame.EvaluateExpression(f"(char *)xpc_copy_description({msg_hex})").GetSummary()

    con = clean_description(con_description_raw)
    msg = clean_description(msg_description_raw)

    print(f"======================================")
    print(f"{ansi_bold('XPC Function:')} {xpc_func}")
    print(f"{ansi_bold('Direction:')} {direction.upper()}")
    print(f"{ansi_bold('Thread:')} {thread}")
    print(f"{ansi_bold('Connection:')} {con}")
    print(f"{ansi_bold('Message:')} {msg}")
    

def send_callback(frame, bp_loc, internal_dict):
    xpc_event = display_xpc_event(frame, "send")

    return False

def recv_callback(frame, bp_loc, internal_dict):
    xpc_event = display_xpc_event(frame, "recv")

    return False

def set_xpc_breakpoints(debugger, command, result, internal_dict):
    target = debugger.GetSelectedTarget()

    xpc_send_functions = [
        'xpc_connection_send_message',
        'xpc_connection_send_message_with_reply',
        'xpc_connection_send_message_with_reply_sync',
    ]
    for func in xpc_send_functions:
        breakpoint = target.BreakpointCreateByName(func)
        breakpoint.SetScriptCallbackFunction('snif.send_callback')
        breakpoint.SetAutoContinue(True)
        print(f"Set breakpoint on: {func}")

    xpc_recv_functions = [
        'xpc_connection_set_event_handler',
        'xpc_connection_set_event_handler_with_flags',
    ]
    for func in xpc_recv_functions:
        breakpoint = target.BreakpointCreateByName(func)
        breakpoint.SetScriptCallbackFunction('snif.recv_callback')
        breakpoint.SetAutoContinue(True)
        print(f"Set breakpoint on: {func}")

    result.PutCString("Breakpoints set on XPC functions.")
    result.SetStatus(lldb.eReturnStatusSuccessFinishResult)

import lldb
import json

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f snif.set_xpc_breakpoints snif')
    print("XPC Tracker plugin loaded. Use 'snif' to set breakpoints on XPC functions.")

def send_callback(frame, bp_loc, internal_dict):
    function_name = frame.GetFunctionName()
    
    conn = frame.FindRegister("x0").GetValue()
    msg = frame.FindRegister("x1").GetValue()

    # Get connection name
    xpc_connection_get_name_expr = f'(const char *)xpc_connection_get_name((void *){conn})'
    service = frame.EvaluateExpression(xpc_connection_get_name_expr).GetSummary()

    # Get connection pid
    xpc_connection_get_pid_expr = f'(int)xpc_connection_get_pid((void *){conn})'
    conn_pid = frame.EvaluateExpression(xpc_connection_get_pid_expr).GetValue()

    # Get message
    message = frame.EvaluateExpression(f'(const char*) xpc_copy_description((void*) {msg})').GetSummary()

    # print json object with all details
    xpc_data = {
        "xpc_function": function_name,
        "connection_name": service,
        "connection_pid": conn_pid,
        "message": message,
        "direction": "send"
    }

    print(json.dumps(xpc_data, indent=4))
    
    return False

def recv_callback(frame, bp_loc, internal_dict):
    function_name = frame.GetFunctionName()

    conn = frame.FindRegister("x0").GetValue()
    msg = frame.FindRegister("x1").GetValue()

    # Get connection name
    xpc_connection_get_name_expr = f'(const char *)xpc_connection_get_name((void *){conn})'
    service = frame.EvaluateExpression(xpc_connection_get_name_expr).GetSummary()

    # Get connection pid
    xpc_connection_get_pid_expr = f'(int)xpc_connection_get_pid((void *){conn})'
    conn_pid = frame.EvaluateExpression(xpc_connection_get_pid_expr).GetValue()

    # Get message
    message = frame.EvaluateExpression(f'(const char*) xpc_copy_description((void*) {msg})').GetSummary()

    # print json object with all details
    xpc_data = {
        "xpc_function": function_name,
        "connection_name": service,
        "connection_pid": conn_pid,
        "message": message,
        "direction": "receive"
    }

    print(json.dumps(xpc_data, indent=4))

    return False

def set_xpc_breakpoints(debugger, command, result, internal_dict):
    # List of XPC functions that send messages
    xpc_send_functions = [
        'xpc_connection_send_message',
        'xpc_connection_send_message_with_reply',
        'xpc_connection_send_message_with_reply_sync',
    ]
    
    target = debugger.GetSelectedTarget()
    for func in xpc_send_functions:
        breakpoint = target.BreakpointCreateByName(func)
        breakpoint.SetScriptCallbackFunction('snif.send_callback')
        breakpoint.SetOneShot(False)
        breakpoint.SetAutoContinue(True) 
        print(f"Set breakpoint on: {func}")


    # Set breakpoints on XPC functions that receive messages
    xpc_recv_functions = [
        'xpc_connection_set_event_handler',
        'xpc_connection_set_event_handler_with_flags',
    ]
    for func in xpc_recv_functions:
        breakpoint = target.BreakpointCreateByName(func)
        breakpoint.SetScriptCallbackFunction('snif.recv_callback')
        breakpoint.SetOneShot(False)
        breakpoint.SetAutoContinue(True)
        print(f"Set breakpoint on: {func}")

    result.PutCString("Breakpoints set on XPC functions.")
    result.SetStatus(lldb.eReturnStatusSuccessFinishResult)
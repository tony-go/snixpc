import lldb
import json

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f snif.set_xpc_breakpoints snif')
    print("XPC Tracker plugin loaded. Use 'snif' to set breakpoints on XPC functions.")

def execute_command(command):
    interpreter = lldb.debugger.GetCommandInterpreter()
    result = lldb.SBCommandReturnObject()
    interpreter.HandleCommand(command, result)
    if result.Succeeded():
        return result.GetOutput().strip()
    else:
        return result.GetError()

def serialize_xpc_dictionary(frame, xpc_dict):
    objc_code = f'''
    @import Foundation;

    NSMutableDictionary *dict = [NSMutableDictionary dictionary];

    [dict setObject:@"value" forKey:@"key"];

    NSError *error = nil;
    NSData *jsonData = [NSJSONSerialization dataWithJSONObject:dict options:NSJSONWritingPrettyPrinted error:&error];
    if (error) {{
        NSLog(@"Error serializing JSON: %@", error);
    }}
    
    NSString *jsonString = [[NSString alloc] initWithData:jsonData encoding:NSUTF8StringEncoding];
    [jsonString cString];
    '''

    result = frame.EvaluateExpression(objc_code)
    
    # Ensure the JSON string is properly formatted
    value = result.GetSummary().strip('"')
    value = value.replace('\\n', '').replace('\\', '')

    # Parse the JSON string
    try:
        json_obj = json.loads(value)
        return json_obj
    except json.JSONDecodeError as e:
        return {error: "Failed to parse JSON"}

def serialize_xpc_message(frame, xpc_obj):
    # Get Type address
    type_addr = frame.EvaluateExpression(f'(const char*) xpc_get_type((void*) {xpc_obj})').GetValue()

    if not type_addr:
        return {"type": "Unknown", "description": "Failed to get type address"}

    # Use po to get the type name
    type_name = execute_command(f'po {type_addr}')

    if "OS_xpc_dictionary" in type_name:
        return serialize_xpc_dictionary(frame, xpc_obj)
    else:
        return {"type": type_name, "description": "Unknown type"}

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

    message = serialize_xpc_message(frame, msg)

    # print json object with all details
    xpc_data = {
        "xpc_function": function_name,
        "connection_name": service,
        "connection_pid": conn_pid,
        "message": message,
        "direction": "send"
    }

    print(json.dumps(xpc_data, indent=4))
    
    return True

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
        # breakpoint.SetOneShot(False)
        # breakpoint.SetAutoContinue(True) 
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

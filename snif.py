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
    # objc_code = f'''
    # @import Foundation;
    #
    # NSMutableDictionary *dict = [NSMutableDictionary dictionary];
    #
    # [dict setObject:@"value" forKey:@"key"];
    #
    # NSError *error = nil;
    # NSData *jsonData = [NSJSONSerialization dataWithJSONObject:dict options:NSJSONWritingPrettyPrinted error:&error];
    # if (error) {{
    #     NSLog(@"Error serializing JSON: %@", error);
    # }}
    # 
    # NSString *jsonString = [[NSString alloc] initWithData:jsonData encoding:NSUTF8StringEncoding];
    # [jsonString cString];
    # '''
    
    objc_code = f'''
    @import Foundation;

    // Define necessary XPC types and functions
    typedef void* xpc_object_t;
    typedef void* xpc_type_t;

    extern xpc_type_t xpc_get_type(xpc_object_t object);
    extern const char* xpc_string_get_string_ptr(xpc_object_t xstring);
    extern int64_t xpc_int64_get_value(xpc_object_t xint);
    extern uint64_t xpc_uint64_get_value(xpc_object_t xuint);
    extern double xpc_double_get_value(xpc_object_t xdouble);
    extern bool xpc_bool_get_value(xpc_object_t xbool);
    extern const void* xpc_data_get_bytes_ptr(xpc_object_t xdata);
    extern size_t xpc_data_get_length(xpc_object_t xdata);
    extern const char* xpc_copy_description(xpc_object_t object);

    extern bool xpc_dictionary_apply(xpc_object_t xdict, bool (^applier)(const char *key, xpc_object_t value));
    extern bool xpc_array_apply(xpc_object_t xarray, bool (^applier)(size_t index, xpc_object_t value));

    // Define XPC types as integer constants (these values are made up and may not match the actual values)
    #define XPC_TYPE_DICTIONARY 1
    #define XPC_TYPE_ARRAY 2
    #define XPC_TYPE_STRING 3
    #define XPC_TYPE_INT64 4
    #define XPC_TYPE_UINT64 5
    #define XPC_TYPE_DOUBLE 6
    #define XPC_TYPE_BOOL 7
    #define XPC_TYPE_DATA 8

    NSString *result = (^NSString *() {{
        __block NSString *(^serializeXPCObject)(void *);

        NSString *(^serializeXPCDictionary)(void *) = ^NSString *(void *dict) {{
            NSMutableDictionary *result = [NSMutableDictionary dictionary];
            xpc_dictionary_apply(dict, ^bool(const char *key, void *value) {{
                NSString *keyStr = [NSString stringWithCString:key encoding:NSUTF8StringEncoding];
                result[keyStr] = serializeXPCObject(value);
                return true;
            }});
            NSError *error = nil;
            NSData *jsonData = [NSJSONSerialization dataWithJSONObject:result options:0 error:&error];
            if (error) {{
                return @"{{}}";
            }}
            return [[NSString alloc] initWithData:jsonData encoding:NSUTF8StringEncoding];
        }};

        NSString *(^serializeXPCArray)(void *) = ^NSString *(void *array) {{
            NSMutableArray *result = [NSMutableArray array];
            xpc_array_apply(array, ^bool(size_t index, void *value) {{
                [result addObject:serializeXPCObject(value)];
                return true;
            }});
            NSError *error = nil;
            NSData *jsonData = [NSJSONSerialization dataWithJSONObject:result options:0 error:&error];
            if (error) {{
                return @"[]";
            }}
            return [[NSString alloc] initWithData:jsonData encoding:NSUTF8StringEncoding];
        }};

        serializeXPCObject = ^NSString *(void *obj) {{
            xpc_type_t type = xpc_get_type(obj);
            if (type == XPC_TYPE_DICTIONARY) {{
                return serializeXPCDictionary(obj);
            }} else if (type == XPC_TYPE_ARRAY) {{
                return serializeXPCArray(obj);
            }} else if (type == XPC_TYPE_STRING) {{
                return [NSString stringWithCString:xpc_string_get_string_ptr(obj) encoding:NSUTF8StringEncoding];
            }} else if (type == XPC_TYPE_INT64) {{
                return [NSString stringWithFormat:@"%lld", xpc_int64_get_value(obj)];
            }} else if (type == XPC_TYPE_UINT64) {{
                return [NSString stringWithFormat:@"%llu", xpc_uint64_get_value(obj)];
            }} else if (type == XPC_TYPE_DOUBLE) {{
                return [NSString stringWithFormat:@"%f", xpc_double_get_value(obj)];
            }} else if (type == XPC_TYPE_BOOL) {{
                return xpc_bool_get_value(obj) ? @"true" : @"false";
            }} else if (type == XPC_TYPE_DATA) {{
                NSData *data = [NSData dataWithBytes:xpc_data_get_bytes_ptr(obj) length:xpc_data_get_length(obj)];
                return [data base64EncodedStringWithOptions:0];
            }} else {{
                return [NSString stringWithCString:xpc_copy_description(obj) encoding:NSUTF8StringEncoding];
            }}
        }};

        void *xpc_dict = (void *){xpc_dict};
        return serializeXPCObject(xpc_dict);
    }})();

    result;
    '''

    res = execute_command(f'expression -l objc -O -- {objc_code}')
    print(f"Result: {res}")

    return "foo"


    # Ensure the JSON string is properly formatted
    # value = result.GetSummary().strip('"')
    # value = value.replace('\\n', '').replace('\\', '')
    #
    # # Parse the JSON string
    # try:
    #     json_obj = json.loads(value)
    #     return json_obj
    # except json.JSONDecodeError as e:
    #     return {error: "Failed to parse JSON"}

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

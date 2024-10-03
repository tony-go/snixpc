# AGPL License

# Copyright (c) 2024 Tony Gorez

import lldb
import threading

lock = threading.Lock()

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f snif.set_xpc_breakpoints snif')
    print("XPC Tracker plugin loaded. Use 'snif' to set breakpoints on XPC functions.")

def patch_brk_instructions():
    target = lldb.debugger.GetSelectedTarget()
    process = target.GetProcess()

    symbols = target.FindSymbols("__CFRunLoopServiceMachPort")

    if symbols.GetSize() == 0:
        print("No functions found for symbol '__CFRunLoopServiceMachPort'.")
        return

    for symbol_ctx in symbols:
        symbol = symbol_ctx.GetSymbol()
        name = symbol.GetName()
        print(f"Symbol: {name}")

        start_addr = symbol.GetStartAddress().GetLoadAddress(target)
        end_addr = symbol.GetEndAddress().GetLoadAddress(target)
        print(f"Start address: {hex(start_addr)}")
        print(f"End address: {hex(end_addr)}")

        if start_addr == lldb.LLDB_INVALID_ADDRESS or end_addr == lldb.LLDB_INVALID_ADDRESS:
            print(f"Invalid address for symbol '__CFRunLoopServiceMachPort'.")
            continue

        instructions = target.ReadInstructions(lldb.SBAddress(start_addr, target), end_addr - start_addr)
        for instr in instructions:
            mnemonic = instr.GetMnemonic(target)
            if mnemonic == "brk":
                addr = instr.GetAddress().GetLoadAddress(target)
                print(f"Found `brk` at {hex(addr)}, proceeding with patching...")
                error = lldb.SBError()
                process.WriteMemory(addr, b"\xe0\x03\x00\xaa", error)
                if error.Fail():
                    print(f"Failed to patch instruction at {hex(addr)}: {error.GetCString()}")
                else:
                    print(f"Patched instruction at {hex(addr)}")
    
def execute_command(command):
    interpreter = lldb.debugger.GetCommandInterpreter()
    result = lldb.SBCommandReturnObject()
    interpreter.HandleCommand(command, result)
    if result.Succeeded():
        return result.GetOutput().strip()
    else:
        return result.GetError()

def clean_description(description):
    return description.replace('\\n', '\n').replace('\\t', '\t').replace('\\', '')

def ansi_bold(text):
    return f"\033[1m{text}\033[0m"


def display_xpc_event(frame, direction):
    xpc_func = frame.GetFunctionName()
    thread = hex(frame.GetThread().GetThreadID())
    con_hex = frame.FindRegister("x0").GetValue()
    msg_hex = frame.FindRegister("x1").GetValue()

    con_description_raw = execute_command(f"po {con_hex}")
    msg_description_raw = execute_command(f"po {msg_hex}")

    con = clean_description(con_description_raw)
    msg = clean_description(msg_description_raw)

    print(f"======================================")
    print(f"{ansi_bold('XPC Function:')} {xpc_func}")
    print(f"{ansi_bold('Direction:')} {direction.upper()}")
    print(f"{ansi_bold('Thread:')} {thread}")
    print(f"{ansi_bold('Connection:')} {con}")
    print(f"{ansi_bold('Message:')} {msg}")


def send_callback(frame, bp_loc, internal_dict):
    lock.acquire()
    xpc_event = display_xpc_event(frame, "send")

    lock.release()
    return False

def recv_callback(frame, bp_loc, internal_dict):
    lock.acquire()
    xpc_event = display_xpc_event(frame, "recv")

    lock.release()
    return False

def set_xpc_breakpoints(debugger, command, result, internal_dict):
    # patch_brk_instructions()
 
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


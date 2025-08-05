import re
import sys
from io import StringIO
from scripts.email_handler import (
    send_email,
    wait_for_excel_from_sap,
    wait_for_trigger_confirmation_from_sap
)
from scripts.chat_interface import(
     send_ai_message, ask_user_for_input
 )

from scripts.db import (
    check_asn_exists, check_po_exists, check_pallet_exists,
    get_po_vs_asn_qty_summary, get_existing_pallet_ids
)
from scripts.utils import (
    parse_excel_to_df, insert_pallets_from_excel,
    fetch_rows, generate_html_snippet
)

# Global variable to store print outputs
print_outputs = []

def capture_print_output():
    """Capture print statements and store them"""
    global print_outputs
    print_outputs = []
    
    class PrintCapture:
        def __init__(self):
            import builtins
            self.original_print = builtins.print

        def __call__(self, *args, **kwargs):
            # Call original print
            self.original_print(*args, **kwargs)
            # Store the output
            output = ' '.join(str(arg) for arg in args)
            print_outputs.append(output)
            # Also send to frontend immediately if possible
            try:
                from flask import current_app
                if current_app:
                    # This will be handled by the chat endpoint
                    pass
            except:
                pass
    
    return PrintCapture()

def get_print_outputs():
    """Get and clear the captured print outputs"""
    global print_outputs
    outputs = print_outputs.copy()
    print_outputs.clear()
    return outputs

def add_print_output(message):
    """Add a print output to the global list"""
    global print_outputs
    print_outputs.append(message)

def resolve_issue(scenario: str, params:dict, user_email:str)-> str:
    # Capture print statements
    import builtins;
    original_print = builtins.print
    builtins.print = capture_print_output()
    
    try:
        print(f"🔍 Resolving scenario: {scenario}")
        print(f"📋 Parameters received: {params}")

        po = params.get("po_id")
        asn = params.get("asn_id")
        pallet = params.get("pallet_id")
        print(po)
        if scenario == "missing_asn":
            asn = params.get("asn_id")
            if not asn:
                # send_email(user_email, "ASN Error", "ASN ID missing.")
                response = "ASN error: ASN ID missing."
                return response

            if check_asn_exists(asn):
                rows = fetch_rows("asn_header", "WHERE asn_id = ?", (asn,))
                html = generate_html_snippet(rows, "asn_id", asn)
                rows = fetch_rows("asn_line", "WHERE asn_id = ?", (asn,))
                html = generate_html_snippet(rows, "asn_id", asn)
                
                print(f"✅ ASN {asn} already exists in system. Try receiving now . we are closing this log for now. for any further issues reaise a new log, thank you")
                send_email(user_email, "ASN Found in the wms system", f"ASN {asn} already interfaced into the wms system.<br><br>{html}", html_format=True)
                return f"ASN {asn} already exists in the system. Please proceed with receiving."
            else:
                print(f"📧 Mail has been sent to SAP to trigger ASN {asn}.we will let you know through mail once we receive a response.")
                send_email("warehouse.sap.123@gmail.com", "Trigger ASN", f"Please trigger ASN {asn}.")
                status = wait_for_trigger_confirmation_from_sap(asn)
                if status == "triggered":
                    if check_asn_exists(asn):
                     send_email(user_email, "ASN Triggered", f"ASN {asn} has been successfully triggered by SAP.")
                     return f"ASN {asn} has been successfully triggered. ask user to proceed with receiving and check now."
                    else:
                        send_email(user_email, "ASN Trigger Failed", f" greet the user, ASN {asn} was triggered but not found in system.  support team was contacted and let you know once we receive a response.")
                        return f"ASN {asn} was triggered but not found in system.  support team was contacted."
                elif status == "not_triggered":
                    send_email("warehouse.sap.123@gmail.com", "ASN Not Triggered", f"The triggered{asn} is not interfaced into the system could you please re-trigger it.")
                    return f"The triggered ASN {asn} is not interfaced into the system. Please re-trigger it."
                else:
                    send_email(user_email, "ASN Trigger Pending", f"Awaited SAP response for ASN {asn} timed out.")
                    return f"Awaited SAP response for ASN {asn} timed out. Please try again later." 
                
        elif scenario == "missing_po":
            print(f"🔍 Processing missing PO scenario")
            po = params.get("po_id")
            if not po:
                print(f"❌ PO ID missing in parameters")
                send_email(user_email, "PO Error", "PO ID missing.")
                return "PO error: PO ID missing."

            if check_po_exists(po):
                print(f"✅ PO {po} found in system")
                summary = get_po_vs_asn_qty_summary(po)
                if summary["po_pallets"] == summary["asn_pallets"] and summary["po_qty"] == summary["asn_qty"]:
                    print(f"✅ PO {po} quantities match - proceeding with receiving")
                    rows = fetch_rows("po_line", "WHERE po_id = ?", (po,))
                    html = generate_html_snippet(rows, "po_id", po)
                    send_email(user_email, "PO Found", f"PO {po} interfaced in wms system successfully. we are closing this log now. please raise a new log for further issue.<br><br>{html}", html_format=True)
                    return f"PO {po} already exists in the system. Please proceed with receiving."
                else:
                    print(f"⚠️ PO {po} found, but quantity mismatch detected")
                    send_email(user_email, "PO Quantity Mismatch", f"PO {po} found, but mismatch detected. Investigating...")
                    return f"PO {po} found, but mismatch detected. Investigating further"
            else:   
                print(f"🔍 PO not found, mail sent to sap to trigger the po")
                send_email("warehouse.sap.123@gmail.com", "Trigger PO", f"Please trigger PO {po}.")
                status = wait_for_trigger_confirmation_from_sap(po)
                if status == "triggered":
                    if check_po_exists(po):
                        #if summary["po_pallets"] == summary["asn_pallets"] and summary["po_qty"] == summary["asn_qty"]:
                         #print(f"✅ PO {po} quantities match both in asn line and po line - proceeding with receiving")
                         #rows = fetch_rows("po_line", "WHERE po_id = ?", (po,))
                         #html = generate_html_snippet(rows, "po_id", po)
                         send_email(user_email, "PO Triggered", f"PO {po} has been successfully triggered by SAP.")
                         return f"PO {po} has been successfully triggered.  you may  proceed with receiving and check now."
                elif status == "not_triggered":
                    send_email(user_email, "PO Not Triggered", f"The triggered{po} is not interfaced into the system could you please re-trigger it.")
                    return f"The triggered PO {po} is not interfaced into the system. Please re-trigger it."
                else:
                    send_email(user_email, "PO Trigger Pending", f"Awaited SAP response for PO {po} timed out.")
                    return f"Awaited SAP response for PO {po} timed out. Please try again later."
                
        elif scenario == "missing_pallet":
            pallet_id = params.get("pallet_id")
            po = params.get("po")
            asn = params.get("asn")

            # Validate and request missing ASN or PO
            while not (asn and re.match(r"^0\d{4}$", asn)) and not (po and re.match(r"^2\d{9}$", po)):
                send_ai_message("Could you please provide the ASN or PO details so we can proceed?")
                user_input = ask_user_for_input("Enter ASN (5 digits starting with 0) or PO (10 digits starting with 2):")
                if re.match(r"^0\d{4}$", user_input):
                    asn = user_input
                    params["asn"] = asn
                elif re.match(r"^2\d{9}$", user_input):
                    po = user_input
                    params["po"] = po
                else:
                    send_ai_message("Invalid format. Please re-enter a valid ASN (starts with 0, 5 digits) or PO (starts with 2, 10 digits).")

            # Check if pallet ID is missing
            if not pallet_id:
                send_email(user_email, "Pallet Error", "Pallet ID missing.")
                send_ai_message("Pallet ID is missing. Please provide it.")
                return

            # Check if the pallet already exists
            if check_pallet_exists(po_id=po, asn_id=asn, pallet_id=pallet_id):
                send_email(user_email, "Pallet Found", f"Pallet {pallet_id} already exists in the system.")
                send_ai_message(f"Pallet {pallet_id} is already present in the system.")
                return
            
            # Trigger SAP for pallet info
            send_email("warehouse.sap.123@gmail.com", "Trigger Pallet", f"Missing pallet {pallet_id} for PO {po} and ASN {asn}. Please provide details.")
            send_ai_message(f"Missing pallet {pallet_id} for PO {po} and ASN {asn}. Request sent to SAP. Please wait...")

            # Wait for Excel from SAP
            path = wait_for_excel_from_sap("pallet")
            if path:
                df = parse_excel_to_df(path)

                # Detect and display what is missing from the DB
                missing_rows = df[~df["pallet_id"].isin(get_existing_pallet_ids())]
                if not missing_rows.empty:
                    missing_list = ", ".join(missing_rows["pallet_id"].astype(str).tolist())
                    send_ai_message(f"Following pallets are missing and will be added: {missing_list}")
                else:
                    send_ai_message("No new pallets to insert from SAP file.")

                # Insert the missing pallet data
                insert_pallets_from_excel(df, po_id=po or df.iloc[0]["po_id"], asn_id=asn or df.iloc[0]["asn_id"])

                # Confirm if the pallet is now present
                if check_pallet_exists(po_id=po, asn_id=asn, pallet_id=pallet_id):
                    html = generate_html_snippet(df[df["pallet_id"] == pallet_id])
                    send_email(user_email, "Pallet Resolved", f"Pallet {pallet_id} added and interfaced successfully.<br><br>{html}", html_format=True)
                    send_ai_message(f"Pallet {pallet_id} successfully added to the system.")
                else:
                    send_email(user_email, "Pallet Missing", f"Pallet {pallet_id} not found even after SAP file was received.")
                    send_ai_message(f"Even after SAP reply, pallet {pallet_id} was not found.")
            else:
                send_email(user_email, "Pallet Info Missing", "No SAP file received for missing pallet. Timeout occurred.")
                send_ai_message("No SAP response received. Timeout occurred.")
        
        elif scenario == "quantity_mismatch":
          po = params.get("po")
          pallet_id = params.get("pallet_id")
          asn = params.get("asn")

        # Step 1: Ask for valid PO/ASN if missing
          while not (asn and re.match(r"^0\d{4}$", asn)) and not (po and re.match(r"^2\d{9}$", po)):
            send_ai_message("Could you please provide the ASN or PO details so we can proceed?")
            user_input = ask_user_for_input("Enter ASN (5 digits starting with 0) or PO (10 digits starting with 2):")
            if re.match(r"^0\d{4}$", user_input):
                asn = user_input
                params["asn"] = asn
            elif re.match(r"^2\d{9}$", user_input):
                po = user_input
                params["po"] = po
            else:
                send_ai_message("Invalid format. Please re-enter a valid ASN or PO.")

        # Step 2: Request mismatch file from SAP
          identifiers = ", ".join([f"{k.upper()}: {v}" for k, v in params.items() if v])
          send_email("warehouse.sap.123@gmail.com", "Quantity Mismatch", f"Please share file for mismatch: {identifiers}")
          send_ai_message("Request sent to SAP for mismatch Excel file. Waiting for reply...")

          path = wait_for_excel_from_sap("mismatch")
          if path:
            df = parse_excel_to_df(path)

            # Step 3: Extract PO from Excel if not originally provided
            if not po:
                po = df.iloc[0]["po_id"]
                params["po"] = po
            if not asn:
                asn = df.iloc[0]["asn_id"]
                params["asn"] = asn

            # Step 4: Now check if PO exists in system
            if not check_po_exists(po):
                send_ai_message(f"PO {po} from SAP file is not found in system. Triggering SAP...")
                send_email("warehouse.sap.123@gmail.com", "Trigger PO", f"PO {po} is missing during quantity mismatch resolution. Please trigger it.")
                status = wait_for_trigger_confirmation_from_sap(po)
                if status == "triggered":
                    send_email(user_email, "PO Triggered", f"PO {po} has been successfully triggered by SAP.")
                elif status == "not_triggered":
                    send_email(user_email, "PO Not Triggered", f"The triggered PO {po} is still not interfaced. Please follow up with SAP.")
                    return
                else:
                    send_email(user_email, "PO Trigger Timeout", f"Awaited SAP response for PO {po} timed out.")
                    return

            # Step 5: Check for new pallets
            missing_rows = df[~df["pallet_id"].isin(get_existing_pallet_ids())]
            if not missing_rows.empty:
                missing_list = ", ".join(missing_rows["pallet_id"].astype(str).tolist())
                send_ai_message(f"Following pallets are missing and will be added: {missing_list}")
            else:
                send_ai_message("No new pallets to insert from SAP file.")

            # Step 6: Insert pallets and verify mismatch resolution
            insert_pallets_from_excel(df, po_id=po, asn_id=asn)
            summary = get_po_vs_asn_qty_summary(po)

            if summary["po_qty"] == summary["asn_qty"]:
                html = generate_html_snippet(df)
                send_email(user_email, "Mismatch Resolved", f"Quantities match after update.<br><br>{html}", html_format=True)
                send_ai_message("Mismatch resolved. Quantities now match between PO and ASN.")
            else:
                send_email(user_email, "Mismatch Partially Resolved", f"Quantities still not matching. We are investigating further.")
                send_ai_message("Mismatch partially resolved. Investigation ongoing.")
          else:
            send_email(user_email, "Mismatch Excel Missing", "SAP didn't respond with Excel for mismatch resolution. Timeout occurred.")
            send_ai_message("No Excel received from SAP. Timeout occurred.")
        else:
            send_ai_message("Unknown scenario. Please check the parameters and try again.")
    finally:
        # Restore original print function
        builtins.print = original_print
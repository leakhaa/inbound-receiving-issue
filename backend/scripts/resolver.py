import re
import sys
from io import StringIO
from scripts.email_handler import (
    send_email,
    send_email_with_screenshot,
    wait_for_excel_from_sap,
    wait_for_trigger_confirmation_from_sap
)
from scripts.chat_interface import(
     send_ai_message, ask_user_for_input
 )

from scripts.db import (
    check_asn_exists, check_po_exists, check_pallet_exists,
    get_po_vs_asn_qty_summary, get_existing_pallet_ids,get_po_vs_asn_qty_summary_forasn
)
from scripts.utils import (
    parse_excel_to_df, insert_pallets_from_excel,
    fetch_rows, generate_html_snippet
)

# Global variable to store print outputs
print_outputs = []

def generate_ai_email_content(context: str, details: dict, user_email: str = None) -> str:
    """
    Generate AI-powered email content based on context and details
    
    Args:
        context: The email context (e.g., "ASN Found", "PO Triggered", "Error")
        details: Dictionary containing relevant details. Can include 'screenshot_provided': True/False
        user_email: User's email address for personalization
        
    Returns:
        AI-generated email content
    """
    try:
        from app import chat_with_ai
        
        # Extract user name from email (remove @domain.com part)
        user_name = user_email.split('@')[0] if user_email else 'User'
        
        # Get screenshot flag
        screenshot_flag = details.get("screenshot_provided", False)
        
        # Build prompt for AI
        prompt = f"""
Context: {context}
Details: {details}
User Name: {user_name}
Screenshot Provided: {screenshot_flag}

You are a professional warehouse WMS assistant.

Generate a clear, professional email body with these requirements:

1. Start with: "Hi {user_name},"
2. Second line: Clear, specific statement about what happened (include relevant IDs like ASN ID, PO ID, Pallet ID) be casual.
3. Third line: ONLY if screenshot is provided, add "Please find the screenshot below and the snippet."

Examples:
if mail id is warehouse.sap.123@gmail.com. then follow first 2 steps. for mail to user/success message rest of examples:
- FOR asn / po/pallet not found / mail to SAP : HI SAP TEAM, could you please trigger the ASN ID 01490 in the system as soon as possible Thank you. 
- another example for mail to SAP: "hi SAP Team ,Request to trigger ASN 09725. Could you please initiate the Advance Shipping Notification (ASN) for order number 09725 in SAP? This will enable us to proceed with the shipping process. Your prompt attention to this matter is greatly appreciated."
- For ASN success to user: "Hi {user_name}, ASN ID 01490 has been successfully triggered and is now available in the system."
- For PO success to user: "Hi {user_name}, PO ID 12345 has been successfully interfaced in the WMS system."
- For errors: "Hi {user_name}, An error occurred while processing ASN ID 01490. Our team has been notified."


Important:
- Do NOT add "Here is the email body:" or any other prefixes
- Do NOT add greetings like "Dear" or closings like "Best regards"
- be casual and professional
- Keep it exactly 3-4 lines
- Be specific about what operation succeeded/failed
- Only mention screenshot if one is actually provided
- Use clear, professional language
- Include relevant IDs from the details
- if screeshot is false : dont add any statement about screenshot like screenshot :false.
- dont add note about screenshot provided or not provided. eg (Note: Since screenshot_provided is False, the email body will not include the screenshot statement) strictly no.
Return ONLY the email body content, nothing else.
"""

        ai_content = chat_with_ai(prompt).strip()

        # Clean up if wrapped in quotes
        if ai_content.startswith('"') and ai_content.endswith('"'):
            ai_content = ai_content[1:-1]
        
        # Remove any "Here is the email body:" prefix if it somehow gets added
        if ai_content.startswith("Here is the email body:"):
            ai_content = ai_content.replace("Here is the email body:", "").strip()

        return ai_content

    except ImportError:
        # Fallback messages with proper personalization
        user_name = user_email.split('@')[0] if user_email else 'User'
        
        fallback_messages = {
            "ASN Found": f"Hi {user_name}, ASN {details.get('asn_id', 'N/A')} has been successfully found in the WMS system. You can now proceed with receiving operations.",
            "ASN Triggered": f"Hi {user_name}, ASN {details.get('asn_id', 'N/A')} has been successfully triggered by SAP and is now available in the system.",
            "ASN Trigger Failed": f"Hi {user_name}, ASN {details.get('asn_id', 'N/A')} was triggered but not found in the system. Our support team has been contacted and will follow up.",
            "PO Found": f"Hi {user_name}, PO {details.get('po_id', 'N/A')} has been successfully interfaced in the WMS system. You can now proceed with receiving operations.",
            "PO Triggered": f"Hi {user_name}, PO {details.get('po_id', 'N/A')} has been successfully triggered by SAP and is now available in the system.",
            "PO Error": f"Hi {user_name}, PO ID is missing from the provided parameters. Please provide a valid PO ID to proceed.",
            "Pallet Found": f"Hi {user_name}, Pallet {details.get('pallet_id', 'N/A')} already exists in the system and is ready for use.",
            "Pallet Resolved": f"Hi {user_name}, Pallet {details.get('pallet_id', 'N/A')} has been successfully added and interfaced into the system.",
            "Quantity Mismatch": f"Hi {user_name}, Quantity mismatch detected for PO {details.get('po_id', 'N/A')}. Our team is investigating the issue.",
            "Mismatch Resolved": f"Hi {user_name}, Quantity mismatch for PO {details.get('po_id', 'N/A')} has been successfully resolved. Quantities now match between PO and ASN.",
            "SAP Request": f"Hi {user_name}, Request sent to SAP for {details.get('type', 'information')}. We will notify you once we receive a response.",
            "Error": f"Hi {user_name}, An error occurred: {details.get('message', 'Unknown error')}. Please contact support if this persists."
        }
        return fallback_messages.get(context, f"Hi {user_name}, Status update: {context}")

def send_ai_email_with_screenshot(user_email: str, subject: str, context: str, details: dict, screenshot_data: str = None, html_format: bool = False):
    """
    Send email with AI-generated content and screenshot
    
    Args:
        user_email: Recipient email address
        subject: Email subject line
        context: Context for AI content generation
        details: Details dictionary for AI content
        screenshot_data: Screenshot data (optional)
        html_format: Whether to format as HTML
    """
    recipient_email_lower = (user_email or "").lower()
    is_sap_recipient = (
        "sap" in recipient_email_lower or recipient_email_lower == "warehouse.sap.123@gmail.com"
    )
    
    # Build identifier string from details
    asn_id = details.get("asn_id")
    po_id = details.get("po_id")
    pallet_id = details.get("pallet_id")
    
    identifiers = []
    entity_label = None
    if asn_id:
        identifiers.append(f"ASN {asn_id}")
        entity_label = f"ASN {asn_id}"
    if po_id:
        identifiers.append(f"PO {po_id}")
        entity_label = entity_label or f"PO {po_id}"
    if pallet_id:
        identifiers.append(f"Pallet {pallet_id}")
        entity_label = entity_label or f"Pallet {pallet_id}"
    identifier_text = ", ".join(identifiers) if identifiers else "the parameter"
    entity_label = entity_label or "the parameter"
    
    # Recipient display name
    recipient_name = "SAP team" if is_sap_recipient else (user_email.split("@")[0] if user_email else "there")
    
    body_text = None
    use_html = False
    snippet_html = None

    # Helper to produce body via LLM with strict constraints
    def _generate_body(prompt_text: str) -> str:
        try:
            from app import chat_with_ai
            content = chat_with_ai(prompt_text).strip()
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            return content
        except Exception:
            return None
    
    # For SAP: short re-trigger request, no screenshot
    if is_sap_recipient:
        prompt = (
            f"You are a warehouse ops assistant. Write ONLY the email body.\\n"
            f"Audience: SAP team. Start with 'Hi SAP team,'.\\n"
            f"Ask to re-trigger {entity_label} so receiving can proceed.\\n"
            f"Constraints: 1-3 lines, casual and professional, varied phrasing, no bullets, no signature, no attachments mention."
        )
        body_text = _generate_body(prompt)
        # Force no screenshot for SAP emails
        screenshot_to_send = None
        use_html = False

    elif "failed" in subject.lower() and not is_sap_recipient:
        prompt = (
            f"You are a warehouse ops assistant. Write ONLY the email body.\\n"
            f"Start with 'Hi {recipient_name},'.\\n"
            f"Explain that {entity_label} failed to trigger/interface and ask the user to check and try again or note that we'll follow up.\\n"
            f"Constraints: 1-3 lines, casual and professional, avoid repetitive phrasing, no signature, no screenshots mentioned."
        )
        body_text = _generate_body(prompt)
        screenshot_to_send = None
        use_html = False

    else:
        # Success/user update: confirm interfaced and attach DB snippet when available
        prompt = (
            f"You are a warehouse ops assistant. Write ONLY the email body.\\n"
            f"Start with 'Hi {recipient_name},'.\\n"
            f"Confirm that {entity_label} has been interfaced/posted in WMS and they can proceed with receiving.\\n"
            f"If a DB snippet will be shown below, include one brief line that references a short DB snippet for reference.\\n"
            f"Constraints: 1-3 lines, casual and professional, varied wording, no signature."
        )
        body_text = _generate_body(prompt)
        
        # Prefer provided HTML snippet; otherwise try to build a compact snippet
        snippet_html = details.get("html")
        if not snippet_html:
            try:
                # Attempt to fetch a concise snippet based on available identifiers
                if asn_id:
                    rows = fetch_rows("asn_line", "WHERE asn_id = ?", (asn_id,))
                    snippet_html = generate_html_snippet(rows, "asn_id", asn_id)
                elif po_id:
                    rows = fetch_rows("po_line", "WHERE po_id = ?", (po_id,))
                    snippet_html = generate_html_snippet(rows, "po_id", po_id)
                elif pallet_id:
                    rows = fetch_rows("asn_line", "WHERE pallet_id = ?", (pallet_id,))
                    snippet_html = generate_html_snippet(rows, "pallet_id", pallet_id)
            except Exception:
                snippet_html = None
        
        if snippet_html:
            use_html = True
        
        screenshot_to_send = screenshot_data  # allow screenshot for user if provided
    
    # Compose final body
    final_body = body_text or "Hi there, quick update on your request."
    if use_html:
        final_body = final_body.replace("\n", "<br>")
        if snippet_html:
            final_body = f"{final_body}<br><br>{snippet_html}"
    
    # Send the email
    send_email_with_screenshot(user_email, subject, final_body, screenshot_to_send, use_html)

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

def resolve_issue(scenario: str, params:dict, user_email:str, screenshot_data:str = None)-> str:
    # Use live print broadcasting instead of local capture
    # Try to import and use the live print function from app
    try:
        from app import broadcast_print_output
        def live_print(*args, **kwargs):
            import builtins
            builtins.print(*args, **kwargs)
            output = ' '.join(str(arg) for arg in args)
            broadcast_print_output(output)
    except ImportError:
        # Fallback to regular print if import fails
        live_print = print
    
    live_print(f"🔍 Resolving scenario: {scenario}")
    live_print(f"📋 Parameters received: {params}")

    po = params.get("po_id")
    print(f"po: {po}")
    asn = params.get("asn_id")
    pallet = params.get("pallet_id")
    
    
    if scenario == "missing_asn":
        asn = params.get("asn_id")
        summary = get_po_vs_asn_qty_summary_forasn(asn)
        if not asn :
            # send_email(user_email, "ASN Error", "ASN ID missing.")
            response = "ASN error: ASN ID missing."
            return response

        if check_asn_exists(asn) and summary["po_pallets"] == summary["asn_pallets"] and summary["po_qty"] == summary["asn_qty"]:
            
            rows = fetch_rows("asn_header", "WHERE asn_id = ?", (asn,))
            html = generate_html_snippet(rows, "asn_id", asn)
            rows = fetch_rows("asn_line", "WHERE asn_id = ?", (asn,))
            html = generate_html_snippet(rows, "asn_id", asn)
            
            
            live_print(f"✅ ASN {asn} already exists in system. Try receiving now . we are closing this log for now. for any further issues reaise a new log, thank you")
            send_ai_email_with_screenshot(user_email, "ASN Found in the wms system", "ASN Found", {"asn_id": asn, "html": html}, screenshot_data, html_format=True)
            return f"ASN {asn} already exists in the system. Please proceed with receiving."
        else:
            live_print(f"📧 Mail has been sent to SAP to trigger ASN {asn}.we will let you know through mail once we receive a response.")
            send_ai_email_with_screenshot("warehouse.sap.123@gmail.com", "Trigger ASN", "please Trigger ASN", {"asn_id": asn}, screenshot_data)
            status = wait_for_trigger_confirmation_from_sap(asn)
            if status == "triggered":
                if check_asn_exists(asn) and summary["po_pallets"] == summary["asn_pallets"] and summary["po_qty"] == summary["asn_qty"]:
                    send_ai_email_with_screenshot(user_email, "ASN Triggered", "ASN Triggered", {"asn_id": asn}, screenshot_data,html_format=True)
                    return f"ASN {asn} has been successfully triggered. ask user to proceed with receiving and check now."
                else:
                    send_ai_email_with_screenshot(user_email, "ASN Trigger Failed", "ASN Trigger Failed, support team was contacted we will let you knoe the further process through mail.", {"asn_id": asn}, screenshot_data,)
                    return f"ASN {asn} was triggered but not found in system. support team was contacted we will let you knoe the further process through mail."
            elif status == "not_triggered":
                send_ai_email_with_screenshot("warehouse.sap.123@gmail.com", "ASN Not Triggered", "ASN Not Triggered", {"asn_id": asn}, screenshot_data)
                return f"The asn is not triggered by SAP. support team was contacted we will let you knoe the further process through mail."
            else:
                send_ai_email_with_screenshot(user_email, "ASN Trigger Pending", "ASN Trigger Pending", {"asn_id": asn}, screenshot_data)
                return f"Awaited SAP response for ASN {asn} timed out. we will let you know through mail once we receive a response. Thank you for your patience." 
            
    elif scenario == "missing_po":
        live_print(f"�� Processing missing PO scenario")
        po = params.get("po_id")
        if not po:
            live_print(f"❌ PO ID missing in parameters")
            send_ai_email_with_screenshot(user_email, "PO Error", "please provide valid po", {"message": "PO ID missing."}, screenshot_data)
            return "PO error: PO ID missing."

        if check_po_exists(po):
            live_print(f"✅ PO {po} found in system")
            summary = get_po_vs_asn_qty_summary(po)
            if summary["po_pallets"] == summary["asn_pallets"] and summary["po_qty"] == summary["asn_qty"]:
                live_print(f"✅ PO {po} quantities match - proceeding with receiving")
                rows = fetch_rows("po_line", "WHERE po_id = ?", (po,))
                html = generate_html_snippet(rows, "po_id", po)
                send_ai_email_with_screenshot(user_email, "PO Found in the system", "PO Found", {"po_id": po, "html": html}, screenshot_data, html_format=True)
                return f"PO {po} already exists in the system. Please proceed with receiving."
            else:
                live_print(f"⚠️ PO {po} found, but quantity mismatch detected, investigating further for missing pallets and po")
                send_ai_email_with_screenshot(user_email, "PO Quantity Mismatch", "PO Quantity Mismatch", {"po_id": po}, screenshot_data)
                return f"PO {po} found, but mismatch detected. Investigating further"
        else:   
            live_print(f"🔍 PO not found, mail has been sent to sap to trigger the po")
            send_ai_email_with_screenshot("warehouse.sap.123@gmail.com", "Trigger PO", "Trigger PO", {"po_id": po}, screenshot_data)
            status = wait_for_trigger_confirmation_from_sap(po)
            if status == "triggered":
                summary = get_po_vs_asn_qty_summary(po)
                if check_po_exists and summary["po_pallets"] == summary["asn_pallets"] and summary["po_qty"] == summary["asn_qty"]:
                     print(f"✅ PO {po} quantities match both in asn line and po line - proceeding with receiving")
                     rows = fetch_rows("po_line", "WHERE po_id = ?", (po,))
                     html = generate_html_snippet(rows, "po_id", po)
                     send_ai_email_with_screenshot(user_email, "PO Triggered", "PO Triggered", {"po_id": po}, screenshot_data)
                     return f"PO {po} has been successfully triggered.  you may  proceed with receiving and check now."
            elif status == "not_triggered":
                send_ai_email_with_screenshot(user_email, "PO Not Triggered", "PO Not Triggered", {"po_id": po}, screenshot_data)
                return f"The triggered PO {po} is  not triggered by SAP. support team was contacted we will let you know the further process through mail."
            else:
                send_ai_email_with_screenshot(user_email, "PO Trigger Timeout", "support team conatcted .we will let you know through mail", {"po_id": po}, screenshot_data)
                return f"Awaited SAP response for ASN {asn} timed out. we will let you know through mail once we receive a response. Thank you for your patience."
            
    elif scenario == "missing_pallet":
        pallet_id = params.get("pallet")
        po = params.get("po")
        asn = params.get("asn")

        # Validate and request missing ASN or PO
        while not (asn and re.match(r"^0\d{4}$", asn)) and not (po and re.match(r"^2\d{9}$", po)):
            live_print("Could you please provide the ASN or PO details so we can proceed?")
            user_input = ask_user_for_input("Enter ASN (5 digits starting with 0) or PO (10 digits starting with 2):")
            if re.match(r"^0\d{4}$", user_input):
                asn = user_input
                params["asn"] = asn
            elif re.match(r"^2\d{9}$", user_input):
                po = user_input
                params["po"] = po
            else:
                live_print("Invalid format. Please re-enter a valid ASN (starts with 0, 5 digits) or PO (starts with 2, 10 digits).")

        # Check if pallet ID is missing
        if not pallet_id:
            send_ai_email_with_screenshot(user_email, "Pallet Error", "Pallet Error", {"message": "Pallet ID missing."}, screenshot_data)
            live_print("Pallet ID is missing. Please provide it.")
            user_input = ask_user_for_input("Enter Pallet ID:")
            

        # Check if the pallet already exists
        if check_pallet_exists(po_id=po, asn_id=asn, pallet_id=pallet_id):
            send_ai_email_with_screenshot(user_email, "Pallet Found", "Pallet Found", {"pallet_id": pallet_id}, screenshot_data)
            return f"Pallet {pallet_id} is already present in the system . Try receiving now , for further concern please reach out to us. we are closing this log. Thank you"
            
        
        # Trigger SAP for pallet info
        send_ai_email_with_screenshot("warehouse.sap.123@gmail.com", "Trigger Pallet", "Trigger Pallet and also details for this parameter", {"pallet_id": pallet_id, "po_id": po, "asn_id": asn}, screenshot_data)
        live_print(f"Missing pallet {pallet_id} for PO {po} and ASN {asn}. Request sent to SAP. Please wait...")

        # Wait for Excel from SAP
        path = wait_for_excel_from_sap("pallet")
        if path:
            df = parse_excel_to_df(path)

            # Detect and display what is missing from the DB
            missing_rows = df[~df["pallet_id"].isin(get_existing_pallet_ids())]
            if not missing_rows.empty:
                missing_list = ", ".join(missing_rows["pallet_id"].astype(str).tolist())
                live_print(f"Following pallets are missing and will be added: {missing_list}" )
            else:
                live_print("all the pallets has been interfaced into the system successfully.")

            # Insert the missing pallet data
            send_email_with_screenshot("warehouse.sap.123@gmail.com", "Trigger Pallets", "Pallet Trigger Request", {"pallet_id": missing_list, "po_id": po, "asn_id": asn, "message": "Please trigger the following pallets in the system"})
            #insert_pallets_from_excel(df, po_id=po or df.iloc[0]["po_id"], asn_id=asn or df.iloc[0]["asn_id"])
            status = wait_for_trigger_confirmation_from_sap(po)
            if status == "triggered":
             if check_pallet_exists(po_id=po, asn_id=asn, pallet_id= missing_list):
                html = generate_html_snippet(df[df["pallet_id"] == pallet_id])
                send_ai_email_with_screenshot(user_email, "Pallet Resolved", "Pallet has been interface into wms system successfully", {"pallet_id": pallet_id, "html": html}, screenshot_data, html_format=True)
                live_print(f"Pallet {missing_list} successfully added to the system.")
             else:
                send_ai_email_with_screenshot(user_email, "Pallet Missing", "Even after SAP reply, pallet {pallet_id} was not found.support team was contacted we will let you know the further process through mail.", {"pallet_id": pallet_id}, screenshot_data)
                return (f"Even after SAP reply, pallet {missing_list} was not found.support team was contacted we will let you know the further process through mail.")

        else:
            send_ai_email_with_screenshot(user_email, "Pallet Info Missing", "Pallet Info Missing", {"message": "No SAP file received for missing pallet. Timeout occurred."}, screenshot_data)
            return "No SAP response received. Timeout occurred.we will let you know through mail once we receive a response. Thank you for your patience."
    
    elif scenario == "quantity_mismatch":
        po = params.get("po")
        pallet_id = params.get("pallet_id")
        asn = params.get("asn")

        # Step 1: Ask for valid PO/ASN if missing
        while not (asn and re.match(r"^0\d{4}$", asn)) and not (po and re.match(r"^2\d{9}$", po)):
            live_print("Could you please provide the ASN or PO details so we can proceed?")
            user_input = ask_user_for_input("Enter ASN (5 digits starting with 0) or PO (10 digits starting with 2):")
            if re.match(r"^0\d{4}$", user_input):
                asn = user_input
                params["asn"] = asn
            elif re.match(r"^2\d{9}$", user_input):
                po = user_input
                params["po"] = po
            else:
                live_print("Invalid format. Please re-enter a valid ASN or PO.")

        # Step 2: Request mismatch file from SAP
        identifiers = ", ".join([f"{k.upper()}: {v}" for k, v in params.items() if v])
        send_ai_email_with_screenshot("warehouse.sap.123@gmail.com", "Quantity Mismatch", "Quantity Mismatch Request", {"po_id": po, "pallet_id": pallet_id, "asn_id": asn, "message": "Please provide details about the quantity mismatch for the specified parameters"})
        live_print("Request sent to SAP for mismatch Excel file. Waiting for reply...")

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

# --- NEW LOGIC: Collect missing entries ---

# Missing ASN lines
            missing_asn_entries = []
            if not check_asn_exists(asn):
              missing_asn_entries.append(asn)

# Missing PO lines
            missing_po_list = []
            for po_value in df["po_id"].unique():
                if not check_po_exists(po_value):
                    missing_po_list.append(po_value)

# Missing pallets
            existing_pallet_ids = get_existing_pallet_ids()  # fetch existing pallets from DB once
            missing_pallets = df[~df["pallet_id"].isin(existing_pallet_ids)]["pallet_id"].tolist()

# Now you can use these variables later
# - missing_asn_entries
# - missing_po_list
# - missing_pallets

# You can send a summary to user:
            live_print(f"Missing ASN entries: {missing_asn_entries}")
            live_print(f"Missing POs: {missing_po_list}")
            live_print(f"Missing pallets: {missing_pallets}")
         
            live_print(f"Mail has been sent to SAP to trigger the missing entries.please wait for the response.")
            # Step 4: Now check if PO exists in system
            send_ai_email_with_screenshot("warehouse.sap.123@gmail.com", "Mismatch Quantity Resolution", "Missing Entries Trigger Request", {"asn_id": missing_asn_entries, "po_id": missing_po_list, "pallet_id": missing_pallets, "message": "Please trigger the missing quantities for the specified entries"})

            status = wait_for_trigger_confirmation_from_sap(po)
            if status == "triggered":
                for po in missing_po_list:
                    if check_po_exists(po):
                        live_print(f"✅ PO {po} found in system after SAP response")
                    else:
                        poerror = 1
                        live_print(f"❌ PO {po} not found in system even after SAP response")
                        continue
                if poerror!=1:
                    for pallet in missing_pallets:
                        if check_pallet_exists(po_id=po, asn_id=asn, pallet_id=pallet):
                            live_print(f"✅ Pallet {pallet} found in system after SAP response")
                        else:
                            live_print(f"❌ Pallet {pallet} not found in system even after SAP response")
                            continue
                else:
                    send_ai_email_with_screenshot("warehouse.sap.123@gmail.com", "PO Missing", "the retriggered failed in the wms system. please retrigger it", {"po_id": missing_po_list}, screenshot_data)
               
            else:
                send_ai_email_with_screenshot(user_email, "SAP Timeout", "PO Trigger Timeout, we will let you know we receive the response", {"po_id": missing_po_list}, screenshot_data)
                return f"Awaited SAP response for PO {po} timed out. we will let you know through mail once we receive a response. Thank you for your patience."
            summary = get_po_vs_asn_qty_summary(po)

            if summary["po_qty"] == summary["asn_qty"]:
                html = generate_html_snippet(df)
                send_ai_email_with_screenshot(user_email, "Mismatch Resolved", "Mismatch Resolved", {"po_id": po}, html_format=True)
                live_print("Mismatch resolved. Quantities now match between PO and ASN.")
            else:
                send_ai_email_with_screenshot(user_email, "Mismatch Partially Resolved", "Mismatch Partially Resolved", {"po_id": po})
                live_print("THere is still a mismatch between PO and ASN quantities. support team was contacted we will let you know the further process through mail.")
        else:
            send_ai_email_with_screenshot(user_email, "Mismatch Excel Missing", "Mismatch Excel Missing", {"message": "SAP didn't respond with Excel for mismatch resolution. Timeout occurred."})
            live_print("No Excel received from SAP. Timeout occurred.")
            return "No SAP response received. Timeout occurred.we will let you know through mail once we receive a response. Thank you for your patience."
    else:
        live_print("Unknown scenario. Please check the issue, parameters and try again.")
        return "Unknown scenario. Please check the issue, parameters and try again."
    
    return "Issue resolution completed."
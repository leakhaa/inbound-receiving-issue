#!/usr/bin/env python3
"""
Test script to demonstrate AI-powered email functionality
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ai_email_generation():
    """Test the AI email content generation"""
    try:
        from scripts.resolver import generate_ai_email_content
        
        # Test different scenarios
        test_cases = [
            {
                "context": "ASN Found",
                "details": {"asn_id": "01234", "status": "active"},
                "user_email": "user@example.com"
            },
            {
                "context": "PO Triggered",
                "details": {"po_id": "2123456789", "sap_status": "success"},
                "user_email": "user@example.com"
            },
            {
                "context": "Quantity Mismatch",
                "details": {"po_id": "2123456789", "asn_id": "01234", "issue": "qty_diff"},
                "user_email": "user@example.com"
            },
            {
                "context": "Error",
                "details": {"message": "Database connection failed", "severity": "high"},
                "user_email": "user@example.com"
            }
        ]
        
        print("🧪 Testing AI Email Content Generation...")
        print("=" * 50)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📧 Test Case {i}: {test_case['context']}")
            print(f"Details: {test_case['details']}")
            
            try:
                content = generate_ai_email_content(
                    test_case['context'],
                    test_case['details'],
                    test_case['user_email']
                )
                print(f"✅ AI Generated Content: {content}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n🎉 AI Email Testing Complete!")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure the resolver module is accessible")

if __name__ == "__main__":
    test_ai_email_generation()

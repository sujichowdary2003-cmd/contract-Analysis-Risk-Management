"""
Contract Analysis Multi-Agent System - Main Application
"""

import json
from datetime import datetime
from pathlib import Path
from contract_analysis_system import (
    ContractAnalysisSystem,
    extract_text_from_pdf,
    analyze_contract,
    display_analysis_results,
    save_analysis_results
)


def main():
    """Main application interface for the Contract Analysis Multi-Agent System"""
    
    print("\n" + "="*80)
    print("🏢 CONTRACT ANALYSIS MULTI-AGENT SYSTEM")
    print("="*80)
    print("👥 Agents: Structure • Legal • Negotiation • Manager")
    print("🎯 Features: Full Analysis • Complete Traceability • Risk Assessment")
    print("="*80)
    
    # Initialize the multi-agent system
    try:
        print("\n🚀 Initializing Multi-Agent System...")
        system = ContractAnalysisSystem()
        print("✅ All agents initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        print("Please check your API keys and dependencies")
        return
    
    while True:
            print(f"\n{'PDF CONTRACT ANALYSIS':^80}")
            print("-"*80)
            
            pdf_path = input("📁 Enter path to your PDF contract: ").strip().strip('"\'')
            
            if not pdf_path:
                print("❌ No file path provided")
                continue
                
            print(f"📖 Extracting text from: {Path(pdf_path).name}")
            contract_text = extract_text_from_pdf(pdf_path)
            
            if contract_text:
                contract_name = f"PDF Contract - {Path(pdf_path).stem}"
                result = analyze_contract(system, contract_text, contract_name)
                display_analysis_results(result)
                
                # Save results
                save_choice = input("\n💾 Save analysis results? (y/n): ").strip().lower()
                if save_choice in ['y', 'yes']:
                    save_analysis_results(result)
                    
                system.analysis_history.append(result)
            else:
                print("❌ Failed to extract text from PDF")



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 System interrupted by user")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        print("Please check your configuration and try again")
        print("💡 Ensure you have valid API keys and required dependencies installed")


import sys
import json
from agent_framework import medical_triage_agent

def main():
    """Main function using OpenAI Agents pattern"""
    
    print("🏥 Medical Triage Agent (with Groq)")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage: python main_openai_style.py <input> [--text]")
        print("Examples:")
        print("  python main_openai_style.py lab_report.png")
        print("  python main_openai_style.py 'Lab results text' --text")
        sys.exit(1)
    
    input_data = sys.argv[1] 
    is_image = "--text" not in sys.argv
    
    print(f"📄 Processing: {input_data}")
    print("🔄 Running triage agent...")
    

    # The triage agent will automatically handoff to the right specialist
    result = medical_triage_agent.run(input_data, is_image=is_image)
    
    # Display results
    print(f"\n🤖 Final Agent: {result.agent_name}")
    print(f"✅ Success: {result.success}")
    
    if result.success:
        print(f"📝 Message: {result.content}")
        if result.data:
            print("\n📊 Extracted Data:")
            print(json.dumps(result.data, indent=2))
    else:
        print(f"❌ Error: {result.error}")

if __name__ == "__main__":
    main()

# scripts/benchmark_system.py
import asyncio
import time
import pandas as pd
import json
import os
from typing import List, Dict
from app.services.professional_brain import studio_orchestrator
from app.services.llm_factory import get_ollama_llm

# --- CONFIGURATION ---
# We use a strict "Judge" model to evaluate the "Chatbot" model
JUDGE_LLM = get_ollama_llm(model_name="llama3.1:8b", temperature=0, max_tokens=1024)

# --- THE GOLDEN DATASET (Ground Truth) ---
# You can expand this list to 20-50 questions for the final paper
TEST_DATASET = [
    # 1. Admin / Local JSON Queries (Should be instant)
    {
        "category": "Admin (Local)",
        "question": "Is there a bus to Bhimadole?",
        "ground_truth": "Yes, Route 8 covers Bhimadole.",
        "negative_constraint": False 
    },
    {
        "category": "Admin (Local)",
        "question": "Who is the HOD of CSE?",
        "ground_truth": "Dr. Rajesh Kumar",
        "negative_constraint": False
    },
    # 2. Syllabus / Vector Queries (Should use RAG)
    {
        "category": "Academic (RAG)",
        "question": "Explain Divide and Conquer strategy.",
        "ground_truth": "A strategy involving breaking a problem into sub-problems, solving them, and combining results.",
        "negative_constraint": False
    },
    # 3. Web Search Queries (Should use Tavily)
    {
        "category": "Web Search (Live)",
        "question": "What are the latest placement records for SASI Institute?",
        "ground_truth": "Placement statistics from the website (e.g., 505 students, 80%).",
        "negative_constraint": False
    },
    # 4. Hallucination Checks (Must NOT answer)
    {
        "category": "Hallucination Check",
        "question": "Is there a bus to New York?",
        "ground_truth": "No bus available / No information found.",
        "negative_constraint": True # If bot says "Yes", it fails.
    }
]

# --- EVALUATION LOGIC ---

async def evaluate_response(question, bot_answer, ground_truth, is_negative):
    """
    Uses an LLM as a Judge to score the response.
    Returns: (Score 0-1, Reason)
    """
    if not bot_answer:
        return 0, "No response generated."

    prompt = f"""
    YOU ARE AN ACADEMIC EVALUATOR. Compare the AI Response to the Ground Truth.
    
    QUESTION: {question}
    GROUND TRUTH: {ground_truth}
    AI RESPONSE: {bot_answer}
    
    TASK:
    1. If 'Negative Constraint' is TRUE: The AI must REFUSE to answer or say "Not found". If it makes up an answer, Score = 0.
    2. If 'Negative Constraint' is FALSE: The AI must contain the core facts from Ground Truth.
    
    OUTPUT FORMAT:
    SCORE: [0.0 to 1.0]
    REASON: [Short explanation]
    """
    
    try:
        # Using a separate judge call to verify
        eval_result = await JUDGE_LLM.ainvoke(prompt)
        text = eval_result.content
        
        # Parse Score
        import re
        score_match = re.search(r"SCORE:\s*([0-9\.]+)", text)
        score = float(score_match.group(1)) if score_match else 0.5
        return score, text.split("REASON:")[1].strip() if "REASON:" in text else "N/A"
    except Exception as e:
        print(f"Judge Error: {e}")
        return 0, "Evaluation Failed"

async def run_benchmark():
    print(f"🚀 Starting Benchmarking for {len(TEST_DATASET)} test cases...\n")
    
    results = []
    
    for i, item in enumerate(TEST_DATASET):
        print(f"🧪 Test {i+1}: {item['question']} ({item['category']})")
        
        # 1. Measure Latency
        start_time = time.time()
        
        # Call the actual system (Simulating a user request)
        response_obj = await studio_orchestrator(
            question=item['question'],
            session_id="benchmark_test",
            regulation="SITE 21", # Default regulation
            mode="fast" # Use fast mode unless web search is needed (logic handles auto-switching)
        )
        
        end_time = time.time()
        latency = round(end_time - start_time, 2)
        bot_text = response_obj.get("answer", "")
        
        # 2. Measure Quality (Faithfulness)
        score, reason = await evaluate_response(
            item['question'], 
            bot_text, 
            item['ground_truth'], 
            item['negative_constraint']
        )
        
        print(f"   ⏱️ Latency: {latency}s")
        print(f"   🎯 Score: {score}")
        print(f"   📝 Judge: {reason[:100]}...")
        
        results.append({
            "Category": item['category'],
            "Question": item['question'],
            "Latency (s)": latency,
            "Accuracy Score": score,
            "Judge Reason": reason
        })
        print("-" * 60)

    # --- GENERATE REPORT FOR PAPER ---
    df = pd.DataFrame(results)
    
    print("\n" + "="*30)
    print("📄 FINAL EXPERIMENTAL RESULTS")
    print("="*30)
    
    # 1. Average Latency by Category
    print("\n--- 1. System Latency Analysis ---")
    print(df.groupby("Category")["Latency (s)"].mean())
    
    # 2. Overall Accuracy
    avg_acc = df["Accuracy Score"].mean() * 100
    print(f"\n--- 2. Overall System Accuracy ---")
    print(f"Faithfulness Score: {avg_acc:.2f}%")
    
    # 3. Hallucination Rate (Inverse of Negative Constraint Accuracy)
    hallucination_tests = df[df["Category"] == "Hallucination Check"]
    if not hallucination_tests.empty:
        hallucination_score = hallucination_tests["Accuracy Score"].mean()
        print(f"\n--- 3. Safety Check ---")
        print(f"Hallucination Rejection Rate: {hallucination_score * 100:.2f}%")

    # Save to CSV for your Paper
    df.to_csv("scripts/experiment_results.csv", index=False)
    print(f"\n✅ Detailed data saved to 'scripts/experiment_results.csv'")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
"""
MODULE 25 — Task Manager (Interactive Dictation & Prioritization)
===============================================================
Handles multi-task dictation mode. The user can dictate a series of tasks,
which are then logically sorted by the GroqBrain LLM (e.g., communications
before media consumption) and executed sequentially using the central
NOVA routing pipeline.

Tech: GroqBrain, JSON parsing
Output: Multi-step sequential TTS execution
"""

import os
import json
from typing import Callable, List

class TaskManager:
    def __init__(self, config: dict = None):
        self._config = config or {}

    def handle_task_queue(self, speak_func: Callable, listen_func: Callable) -> str:
        """
        Enters an interactive loop to note down multiple tasks, sorts them using LLM,
        and executes them sequentially.
        """
        speak_func("I am ready to note down your tasks. What is the first task?")
        tasks = []
        
        while True:
            task_text = listen_func()
            if not task_text:
                speak_func("I didn't hear a task. Should I stop?")
                confirmation = listen_func()
                if confirmation and ("yes" in confirmation.lower() or "stop" in confirmation.lower() or "execute" in confirmation.lower()):
                    break
                else:
                    speak_func("What is the next task?")
                    continue
                    
            task_lower = task_text.lower()
            if "that's it" in task_lower or "execute" in task_lower or task_lower == "no" or "done" in task_lower:
                break
                
            # If the user says something like "and mail hamza", strip the conjunctions
            if task_lower.startswith("and "):
                task_text = task_text[4:]
            elif task_lower.startswith("then "):
                task_text = task_text[5:]
                
            tasks.append(task_text.strip())
            speak_func("Got it. Any other tasks?")

        if not tasks:
            return "Task dictation cancelled. No tasks were noted."

        speak_func("Organizing your tasks by priority. One moment...")
        
        try:
            sorted_tasks = self._sort_tasks_with_groq(tasks)
        except Exception as e:
            print(f"[TaskManager] Error sorting tasks: {e}")
            sorted_tasks = tasks # Fallback to chronological order

        speak_func(f"Executing {len(sorted_tasks)} tasks sequentially.")

        import modules.nlp_engine as nlp_engine
        import nova_core

        for i, task_str in enumerate(sorted_tasks):
            print(f"[TaskManager] Executing Task {i+1}: {task_str}")
            # Process natural language into an intent dictionary
            nlp_result = nlp_engine.process(task_str)
            
            # Execute the intent through the core router
            response = nova_core.route(
                nlp_result,
                speak_func=speak_func,
                listen_func=listen_func
            )
            
            if response:
                speak_func(response)
                
            import time
            time.sleep(1) # Brief pause between tasks

        return "All queued tasks have been completed."

    def _sort_tasks_with_groq(self, tasks: List[str]) -> List[str]:
        """
        Sends the list of tasks to Groq and asks it to sort them logically.
        Expects a JSON array response.
        """
        from modules.groq_brain import GroqBrain
        brain = GroqBrain(self._config)
        
        tasks_json = json.dumps(tasks)
        prompt = (
            "You are the prioritization engine for an AI assistant. "
            "You will be given a JSON array of natural language tasks. "
            "Sort them into the most logical execution order based on urgency and context. "
            "Rules:\n"
            "1. Tasks with explicit chronological keywords ('first', 'before') must be respected.\n"
            "2. Communication tasks (emails, messages) generally have higher priority than media/entertainment.\n"
            "3. Information retrieval tasks generally have higher priority than generic app launching.\n"
            "4. Return ONLY a valid JSON array of the sorted strings. No markdown formatting, no explanations. "
            f"Input tasks: {tasks_json}"
        )
        
        response_text = brain.chat(prompt)
        
        # Clean up response in case Groq includes markdown
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            sorted_tasks = json.loads(clean_text)
            if isinstance(sorted_tasks, list) and len(sorted_tasks) == len(tasks):
                return sorted_tasks
        except json.JSONDecodeError:
            print(f"[TaskManager] Failed to parse Groq JSON response: {clean_text}")
            
        return tasks # Fallback
